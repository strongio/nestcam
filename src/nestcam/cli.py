import asyncio
import subprocess
from pathlib import Path

import typer

app = typer.Typer(help="Nest Tracker CLI")


@app.command()
def streamlit():
    """Launch the Streamlit app."""
    app_path = Path(__file__).parent.parent.parent / "streamlit" / "app.py"
    try:
        subprocess.run(["streamlit", "run", str(app_path)], check=True)
    except KeyboardInterrupt:
        typer.echo("Streamlit app stopped.")


@app.command()
def process_events(device_name: str = "Front Door", minutes: int = 60):
    """Process all Ring events from the last 60 minutes."""
    from nestcam.core import process_events_last_minutes

    try:
        asyncio.run(process_events_last_minutes(device_name=device_name, minutes=minutes))
    except KeyboardInterrupt:
        typer.echo("Processing last hour stopped.")


@app.command()
def collect_data(device_name: str = "Front Door", minutes: int = 60):
    """Download all Ring events from the last `minutes` and upload snapshots to Snowflake (no inference)."""
    from nestcam.core import collect_data_last_minutes

    try:
        asyncio.run(collect_data_last_minutes(device_name=device_name, minutes=minutes))
    except KeyboardInterrupt:
        typer.echo("Collecting data stopped.")


@app.command()
def run(device_name: str = "Front Door"):
    """Run the Ring capture pipeline."""
    from nestcam.core import event_loop

    try:
        asyncio.run(event_loop(device_name=device_name))
    except KeyboardInterrupt:
        typer.echo("Ring capture pipeline stopped.")
