import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rich import print


def get_stickup_cam(devices, device_name=None):
    cams = devices["stickup_cams"]
    if not cams:
        print("[red]No stickup cameras found[/red]")
        return None
    if device_name:
        for cam in cams:
            if cam.name == device_name:
                return cam
        print(f"[yellow]No stickup camera found with name '{device_name}', defaulting to first[/yellow]")
    return cams[0] if cams else None


async def get_latest_event_id(ring, auth, device_name=None):
    device = get_stickup_cam(ring.devices(), device_name)
    if not device:
        await auth.async_close()
        print("[red]No stickup camera found[/red]")
        return None
    history = await device.async_history(limit=1)
    await auth.async_close()
    if history:
        return history[0]["id"]
    return None


async def new_recording_event(ring, auth, previous_id, device_name=None):
    device = get_stickup_cam(ring.devices(), device_name)
    if not device:
        await auth.async_close()
        print("[red]No stickup camera found[/red]")
        return None, previous_id
    history = await device.async_history(limit=1)
    await auth.async_close()
    if history:
        latest_event = history[0]
        if latest_event["id"] != previous_id:
            print(f"[green]New recording event detected on {device.name}: {latest_event['id']}[/green]")
            return latest_event, latest_event["id"]
        else:
            print(f"[yellow]No new recording event on {device.name}[/yellow]")
            return None, previous_id
    print(f"[yellow]No events found for {device.name}[/yellow]")
    return None, previous_id


async def get_recent_events(ring, device_name=None, limit=100, minutes=60):
    """
    Return all events for the given device from the last `minutes`.
    """
    device = get_stickup_cam(ring.devices(), device_name)
    if not device:
        print(f"[red]No stickup camera found for device_name={device_name}[/red]")
        return []

    now = datetime.now(timezone.utc)
    since = now - timedelta(minutes=minutes)
    history = await device.async_history(limit=limit)

    recent_events = []
    for event in history:
        created_at = event.get("created_at")
        if isinstance(created_at, datetime):
            created_at_dt = created_at
        else:
            created_at_dt = datetime.fromtimestamp(created_at, tz=timezone.utc)
        if created_at_dt >= since:
            recent_events.append(event)
    return recent_events


async def download_recording(ring, auth, recording_id, device_name=None, snapshot_dir: str = "snapshots"):
    # Check snapshot_dir exists
    Path(snapshot_dir).mkdir(parents=True, exist_ok=True)
    device = get_stickup_cam(ring.devices(), device_name)
    if not device:
        await auth.async_close()
        return None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")  # TODO: use event timestamp
    filename = f"{snapshot_dir}/{device.id}_{recording_id}_{timestamp}.mp4"
    # Wait until the video is ready to download
    while True:
        try:
            await device.async_recording_download(recording_id, filename)
            break
        except Exception as e:
            print(f"[yellow]Recording not ready yet, retrying... ({e})[/yellow]")
            await asyncio.sleep(2)
    return filename
    return filename
