import json
from pathlib import Path

from ring_doorbell import Auth, AuthenticationError, Requires2FAError, Ring

from nestcam.config import RING_PASSWORD, RING_USERNAME

user_agent = "landinglens-streamlit-demo"
cache_file = Path(user_agent + ".token.cache")


def token_updated(token):
    cache_file.write_text(json.dumps(token))


def otp_callback():
    auth_code = input("2FA code: ")
    return auth_code


async def get_authenticated_ring():
    if cache_file.is_file():
        auth = Auth(user_agent, json.loads(cache_file.read_text()), token_updated)
        ring = Ring(auth)
        try:
            await ring.async_create_session()
        except AuthenticationError:
            auth = await do_auth()
            ring = Ring(auth)
    else:
        auth = await do_auth()
        ring = Ring(auth)
    return ring, auth


async def do_auth():
    auth = Auth(user_agent, None, token_updated)
    try:
        await auth.async_fetch_token(RING_USERNAME, RING_PASSWORD)
    except Requires2FAError:
        await auth.async_fetch_token(RING_USERNAME, RING_PASSWORD, otp_callback())
    return auth
    return auth
