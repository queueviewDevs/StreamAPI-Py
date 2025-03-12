from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response, Depends, status

router = APIRouter(
    prefix="/api/nginx",
    tags=["NGINX"]
)

@router.post("/publish", status_code=200)
async def on_Publish():
    """Authorizes the RTMP streamer client to start sending video stream.

    Returns:
        JSON: {"verified": True}
    """
    
    #Change this to provide metadata to the camera
    return {"verified": True}
    
    
    
@router.post("/end-publish", status_code=200)
async def end_Publish():
    """Indicates that the RTMP streamer client stopped sending video stream.

    Returns:
        None
    """
    
    #Change this to provide  metadata to the camera
    return {"done": True}