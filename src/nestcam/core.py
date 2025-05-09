import asyncio

from landingai.predict import SnowflakeNativeAppPredictor
from rich import print

from nestcam.capture.auth import get_authenticated_ring
from nestcam.capture.ring_client import download_recording, get_recent_events, new_recording_event
from nestcam.config import LANDINGAI_APP_URL, LANDINGLENS_ENDPOINT_ID, SNOWFLAKE_CONFIG
from nestcam.inference import run_inference_on_images
from nestcam.snowflake_utils import (
    get_snowflake_connection_and_cursor,
    upload_images_to_snowflake,
    upload_inference_results_to_snowflake,
)
from nestcam.video_utils import video_to_snapshots


def get_predictor():
    return SnowflakeNativeAppPredictor(
        endpoint_id=LANDINGLENS_ENDPOINT_ID,
        native_app_url=LANDINGAI_APP_URL,
        snowflake_account=SNOWFLAKE_CONFIG["account"],
        snowflake_user=SNOWFLAKE_CONFIG["user"],
        snowflake_password=SNOWFLAKE_CONFIG["password"],
        snowflake_authenticator=SNOWFLAKE_CONFIG.get("authenticator", None),
    )


async def process_recording_event(ring, auth, recording_id, cursor, predictor, device_name=None):
    video_file = await download_recording(ring, auth, recording_id, device_name)
    if not video_file:
        return
    print(f"Parsing video {video_file} into snapshots")
    image_files = video_to_snapshots(video_file)
    print(f"Running inference on {len(image_files)} snapshots")
    inference_results = run_inference_on_images(image_files, predictor)
    print(f"Uploading {len(image_files)} snapshots to Snowflake")
    upload_images_to_snowflake(image_files, cursor)
    print("Uploading inference results to Snowflake")
    upload_inference_results_to_snowflake(inference_results, cursor)


async def check_new_event_and_process(ring, auth, previous_id, cursor, predictor, device_name=None):
    event, new_id = await new_recording_event(ring, auth, previous_id, device_name)
    if event:
        await process_recording_event(ring, auth, new_id, cursor, predictor, device_name)
        await asyncio.sleep(10)
    return new_id


async def process_events_last_minutes(device_name=None, minutes=60):
    """Process all Ring events from the last `minutes` minutes."""
    print(f"[bold]Processing events from the last {minutes} minutes[/bold]")
    ring, auth = await get_authenticated_ring()
    await ring.async_update_data()

    conn, cursor = get_snowflake_connection_and_cursor()
    predictor = get_predictor()

    try:
        recent_events = await get_recent_events(ring, device_name, minutes=minutes)
        print(f"[bold]Found {len(recent_events)} events in the last {minutes} minutes[/bold]")

        for event in recent_events:
            recording_id = event["id"]
            await process_recording_event(ring, auth, recording_id, cursor, predictor, device_name)
            await asyncio.sleep(2)  # avoid hammering the API

    finally:
        await auth.async_close()  # Properly close aiohttp session
        cursor.close()
        conn.close()


async def collect_data_last_minutes(device_name=None, minutes=60):
    """Download all Ring events from the last `minutes` and upload snapshots to Snowflake (no inference)."""
    print(f"[bold]Collecting data from the last {minutes} minutes (no inference)[/bold]")
    ring, auth = await get_authenticated_ring()
    await ring.async_update_data()

    conn, cursor = get_snowflake_connection_and_cursor()

    try:
        recent_events = await get_recent_events(ring, device_name, minutes=minutes)
        print(f"[bold]Found {len(recent_events)} events in the last {minutes} minutes[/bold]")

        for event in recent_events:
            recording_id = event["id"]
            video_file = await download_recording(ring, auth, recording_id, device_name)
            if not video_file:
                continue
            print(f"Parsing video {video_file} into snapshots")
            image_files = video_to_snapshots(video_file)
            print(f"Uploading {len(image_files)} snapshots to Snowflake")
            upload_images_to_snowflake(image_files, cursor)
            await asyncio.sleep(2)  # avoid hammering the API

    finally:
        await auth.async_close()  # Properly close aiohttp session
        cursor.close()
        conn.close()


async def event_loop(device_name=None):
    print("[bold]Starting Ring to Snowflake pipeline[/bold]")
    ring, auth = await get_authenticated_ring()
    await ring.async_update_data()

    conn, cursor = get_snowflake_connection_and_cursor()
    predictor = get_predictor()

    try:
        previous_id = "-1"
        while True:
            previous_id = await check_new_event_and_process(ring, auth, previous_id, cursor, predictor, device_name)
            await asyncio.sleep(5)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    asyncio.run(event_loop(device_name="Front Door"))
