from fastapi import APIRouter, Query

from ..auth.auth import get_current_device

router = APIRouter(
    prefix="/api/nginx",
    tags=["NGINX"]
)

@router.post("/publish", status_code=200)
async def on_Publish(
    call: str | None = None,
    app: str | None = None,
    name: str | None = None,
    api_key: str = Query(None, alias="api-key")
):
    """Authorizes the RTMP streamer client to start sending video stream.

    Returns:
        JSON: {"verified": True}
    """
    device = await get_current_device(api_key)
    print("Publish authorized")
    
    return {"verified": True}
    
    
    
@router.post("/end-publish", status_code=200)
async def end_Publish():
    """Indicates that the RTMP streamer client stopped sending video stream.

    Returns:
        None
    """
    
    #Change this to provide  metadata to the camera
    return {"done": True}