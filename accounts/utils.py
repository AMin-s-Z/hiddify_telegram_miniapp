import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def verify_telegram_init_data(init_data_str: str, bot_token: str, max_age_seconds: int = 120) -> dict:
    if not bot_token:
        raise ValueError("Bot token is not configured")

    pairs = dict(parse_qsl(init_data_str, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise ValueError("hash is missing")

    # Build data_check_string: 'key=value' lines sorted lexicographically by key
    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs.keys()))

    # For Telegram Web Apps, secret key is HMAC_SHA256 with key 'WebAppData' over the bot token
    # secret_key = HMAC_SHA256(key='WebAppData', data=bot_token)
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

    # Calculate signature
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != received_hash:
        raise ValueError("invalid hash")

    auth_date_str = pairs.get("auth_date", "0")
    try:
        auth_date = int(auth_date_str)
    except ValueError:
        raise ValueError("invalid auth_date")

    if abs(int(time.time()) - auth_date) > max_age_seconds:
        raise ValueError("stale auth_date")

    user_json = pairs.get("user")
    if not user_json:
        raise ValueError("user missing in init data")

    try:
        user_data = json.loads(user_json)
    except json.JSONDecodeError:
        raise ValueError("invalid user json")

    return {
        "raw": pairs,
        "user": user_data,
    } 