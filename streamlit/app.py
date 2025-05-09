import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from PIL import Image, ImageDraw

import streamlit as st

st.set_page_config(layout="wide")

load_dotenv()


# Load and validate environment variables
SNOWFLAKE_CONFIG = {
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    "authenticator": os.getenv("SNOWFLAKE_AUTHENTICATOR"),
}

STAGE_NAME = os.getenv("SNOWFLAKE_IMAGE_STAGE")


def get_snowflake_connection():
    import snowflake.connector

    if "sf_conn" not in st.session_state or st.session_state.sf_conn is None:
        conn_args = {k: v for k, v in SNOWFLAKE_CONFIG.items() if v is not None}
        st.session_state.sf_conn = snowflake.connector.connect(**conn_args)
    return st.session_state.sf_conn


@st.cache_data(ttl=60)
def load_robin_detections(limit=100):
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT *
        FROM robin_detections
        ORDER BY detected_at DESC
        LIMIT {limit}
    """)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    df = pd.DataFrame(rows, columns=columns)
    df.columns = [col.lower() for col in df.columns]
    return df


def download_image_from_stage(stage_name: str, image_path: str):
    conn = get_snowflake_connection()
    cur = conn.cursor()
    local_dir = Path("./data")
    local_dir.mkdir(exist_ok=True)
    local_path = local_dir / "latest_detection.jpg"
    try:
        full_path = f"@{stage_name}/{image_path}"
        # Remove existing file if it exists
        if local_path.exists():
            local_path.unlink()
        cur.execute(f"GET {full_path} file://{local_dir}")
        # Rename the downloaded file to latest_detection.jpg
        downloaded_file = local_dir / Path(image_path).name
        if downloaded_file.exists():
            downloaded_file.rename(local_path)
            return str(local_path)
        else:
            st.error(f"Downloaded file not found: {downloaded_file}")
            return None
    except Exception as e:
        st.error(f"Error downloading image: {e}")
        return None
    finally:
        cur.close()


st.title("🐦 Robin Nest")

if st.button("🔄 Refresh"):
    st.cache_data.clear()

# Show latest detection image and plot side by side
col1, col2 = st.columns(2)

with col1:
    latest_df = load_robin_detections()
    if not latest_df.empty and "filename" in latest_df.columns:
        image_path = latest_df.iloc[0]["filename"]
        detected_at = latest_df.iloc[0].get("detected_at")
        bboxes = latest_df.iloc[0].get("bboxes")
        if image_path:
            tmp_file_path = download_image_from_stage(STAGE_NAME, image_path)
            if tmp_file_path and os.path.exists(tmp_file_path):
                try:
                    image = Image.open(tmp_file_path).convert("RGB")
                    draw = ImageDraw.Draw(image)
                    if isinstance(bboxes, str):
                        bbox_list = json.loads(bboxes)
                    else:
                        bbox_list = bboxes
                    if isinstance(bbox_list[0], list):
                        for bbox in bbox_list:
                            draw.rectangle(bbox, outline="red", width=3)
                    else:
                        draw.rectangle(bbox_list, outline="red", width=3)
                    st.image(image, caption="Latest Robin Detection")
                except Exception as e:
                    st.warning(f"Could not draw bounding box: {e}")
                    st.image(tmp_file_path, caption="Latest Robin Detection")
                if detected_at:
                    st.info(f"🕒 Latest Robin Detection at {detected_at}", icon="🟢")
            else:
                st.warning("Image file not found after download.")
        else:
            st.info("No image available for the latest detection.")
    else:
        st.info("No latest detection found or image column missing.")

with col2:
    df = load_robin_detections(200)
    if df.empty:
        st.warning("No robin detections found.")
    else:
        df["detected_at"] = pd.to_datetime(df["detected_at"], utc=True)
        now = pd.Timestamp.utcnow()
        last_30_min = now - pd.Timedelta(minutes=30)
        visits_last_30_min = df[df["detected_at"] >= last_30_min].shape[0]
        st.metric("Visits in last 30 minutes", visits_last_30_min)
        df["interval"] = df["detected_at"].dt.floor("30min")
        freq = df.groupby("interval").size().reset_index(name="visits")
        st.subheader("Robin Visits per 30 Minutes (All Data)")
        st.bar_chart(data=freq.set_index("interval"), y="visits")
        if st.checkbox("Show raw data", key="show_raw_data"):
            st.dataframe(df)
