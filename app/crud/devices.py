from ..dependencies.db import devices_collection
from ..schemas.device import Device

async def verify_api_key(key: str) -> Device:
    """Fetches the device with api key"""
    device = await devices_collection.find_one(
        {"api_key": key}
    )
    if device is not None:
        return Device(**device)
    return None