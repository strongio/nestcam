import json
import os
from datetime import datetime
from pathlib import Path

import snowflake.connector
from rich import print

from nestcam.config import SNOWFLAKE_CONFIG, SNOWFLAKE_IMAGE_STAGE, SNOWFLAKE_INFERENCE_TABLE


def get_snowflake_connection_and_cursor(config: dict = None):
    config = config or SNOWFLAKE_CONFIG
    conn = snowflake.connector.connect(**config)
    cursor = conn.cursor()
    return conn, cursor


def upload_images_to_snowflake(file_paths, cursor, stage_name: str = None):
    stage_name = stage_name or SNOWFLAKE_IMAGE_STAGE
    for file_path in file_paths:
        put_command = f"PUT file://{file_path} @{stage_name} AUTO_COMPRESS=FALSE"
        print(f"Uploading {file_path} to Snowflake stage {stage_name}")
        cursor.execute(put_command)
        os.remove(file_path)


def _parse_date_and_event_id(file_path: str):
    """
    Extracts event_id and (year, month, day, hour, minute, second) from a filename containing an event_id and a timestamp in the format YYYYMMDDHHMMSS.
    Example filename: FrontDoor_7502087232390641204_20250508145117_2.jpg
    Returns: (event_id: str, year: int, month: int, day: int, hour: int, minute: int, second: int)
    """
    filename = Path(file_path).name
    parts = filename.split("_")
    if len(parts) < 3:
        raise ValueError("Filename does not contain a valid event_id or timestamp part")
    # device_id = parts[0]
    event_id = parts[1]
    timestamp = parts[2]
    dt = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
    return event_id, dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second


def upload_inference_results_to_snowflake(inference_results, cursor, table_name: str = None):
    table_name = table_name or SNOWFLAKE_INFERENCE_TABLE
    for result in inference_results:
        try:
            file_path = result["file"]
            filename = Path(file_path).name

            endpoint_id = result.get("endpoint_id", "")
            predictions = result.get("predictions", [])

            event_id, year, month, day, hour, minute, second = _parse_date_and_event_id(file_path)

            # Ensure predictions is always a list
            if not isinstance(predictions, list):
                predictions = [predictions]
            for obj in predictions:
                try:
                    bboxes_json = json.dumps(obj.bboxes)
                    insert_query = f"""
                        INSERT INTO {table_name} (
                            filename, endpoint_id, DT_year, DT_month, DT_day, DT_hour, DT_minute, DT_second,
                            label_name, label_index, confidence, bboxes, id, event_id
                        )
                        SELECT
                            '{filename}', '{endpoint_id}', {year}, {month}, {day}, {hour}, {minute}, {second},
                            '{obj.label_name}', {obj.label_index}, {obj.score}, PARSE_JSON('{bboxes_json}'), '{obj.id}', '{event_id}'
                    """
                    cursor.execute(insert_query)
                except Exception as e:
                    print(f"[red]Failed to insert prediction for {filename}: {e}[/red]")
        except KeyError as e:
            print(f"[red]Missing expected key in inference result: {e}[/red]")
        except Exception as e:
            print(f"[red]Unexpected error processing inference result: {e}[/red]")
