from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Response, Depends, status
from ..models.clients import *
from ..dependencies.auth import get_current_active_user

# Authentication token
AUTH_TOKEN = "secret"

router = APIRouter(
    prefix="/api/cameras",
    tags=["Cameras"],
    dependencies=[Depends(get_current_active_user)]
)

# Shared client manager
client_manager = ClientManager()

#---------------Reusable functions and constants----------------
#Will probably move these elsewhere later

cam_cmd_suc_doc_response = {
    200: {
        "description": "Command sent successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Command 'start' sent to client 1"
                }
            }
        }
    }
}

cam_not_found_doc_response = {
    404: {
        "description": "Camera with the given id not found",
        "content": {
            "application/json": {
                "example": {
                    "message": "Camera id 1 currently not connected"
                }
            }
        }
    }
}

cam_cmd_err_doc_response = {
    500: {
        "description": "Camera Communication Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Internal system error when sending command to camera id 1"
                }
            }
        }
    }
}


#---------------End of Reusable functions and constants----------------




@router.get("/", status_code=200)
async def get_cameras() -> list[CameraClient]:
    """Get a list of all connected camera clients

    Returns:
        list[CameraClient]: A list of CameraClient objects containing the camera's metadata
    """
    
    return client_manager.getClients()



@router.get("/{id}", status_code=200, responses=cam_not_found_doc_response)
async def get_camera(id: int) -> CameraClient:
    """Get the metadata of a specific camera client

    Args:
        camera_id (int): The id of the camera client

    Returns:
        CameraClient: A CameraClient object containing the camera's metadata
    """
    
    return client_manager.getClient(id)


@router.put("/{id}", status_code=status.HTTP_200_OK, response_model=CameraClient, responses=cam_not_found_doc_response)
async def update_camera(id: int, data: dict):
    
    print("Update data:", data)
    updated_client = client_manager.updateClient(id, data)
    print("Updated client:", updated_client)
    return updated_client

@router.put("/stream", status_code=200, responses={
    **cam_cmd_suc_doc_response,
    **cam_cmd_err_doc_response
})
async def stream_command_all(command: StreamCommand):
    """Actives/deactivates the stream for all connected clients. Need to implement higher permissions for this"""
    
    action = "start" if command.stream else "stop"
    message = {"action": action}
    await client_manager.broadcast(message)
    return {"status": f"Command '{action}' broadcasted to all clients"}



@router.put("/{id}/stream", status_code=200, responses={
    **cam_cmd_suc_doc_response,
    **cam_not_found_doc_response,
    **cam_cmd_err_doc_response
})
async def stream_command(id: int, command: StreamCommand):
    """
    Start/stop the streaming of a particular client
    """

    action = "start" if command.stream else "stop"
    message = {"action": action}
    await client_manager.send_message(id, message)
    return {"status": f"Command '{action}' sent to client {id}"}



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
    return {}

def testauth():
    pass

@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """The websocket connection endpoint

    Args:
        websocket (WebSocket)
    """
    print("Inside the endpoint")
    await client_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Data received: {data}")
            #await some other client manager function
    except WebSocketDisconnect:
        await client_manager.disconnect(websocket)