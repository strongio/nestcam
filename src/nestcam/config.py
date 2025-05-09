import os

from dotenv import load_dotenv

load_dotenv()

RING_USERNAME = os.getenv("RING_USERNAME")
RING_PASSWORD = os.getenv("RING_PASSWORD")

# Support both password and SSO (external browser) authentication for Snowflake
SNOWFLAKE_AUTHENTICATOR = os.getenv("SNOWFLAKE_AUTHENTICATOR")  # externalbrowser

SNOWFLAKE_CONFIG = {
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    "authenticator": SNOWFLAKE_AUTHENTICATOR,
}

SNOWFLAKE_IMAGE_STAGE = os.getenv("SNOWFLAKE_IMAGE_STAGE")  # e.g. 'my_stage'
SNOWFLAKE_INFERENCE_TABLE = os.getenv("SNOWFLAKE_INFERENCE_TABLE")  # e.g. 'my_table'
CAPTURE_INTERVAL_SECONDS = 30

LANDINGAI_APP_URL = os.getenv("LANDINGAI_APP_URL")  # e.g. 'https://app.landing.ai'
LANDINGLENS_ENDPOINT_ID = os.getenv("LANDINGLENS_ENDPOINT_ID")  # e.g. 'my_endpoint_id'
