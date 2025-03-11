from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from .routers import cameras, auth
from .models.clients import *
from .dependencies.auth import authenticate_websocket_user
from .dependencies.config import init_db

description = """
This is a camera client controller API that allows you to interface with the mobile raspberry pi clients.

The initial release version of the API allows you to:
* List all connected camera clients
* Get a specific camera metadata client by its ID
* Send commands to RPi camera clients
"""

tags_metadata = [
    {
        "name": "Cameras",
        "description": "Operations with camera clients"
    },
    {
        "name": "Internal",
        "description": "Internal endpoints called by NGINX"
    }
]

app = FastAPI(
    title="The camera client controller API",
    description=description,
    version="0.1.0",
    contact={
        "name": "Eric Muzzo",
        "email": "ericm02@me.com"
    },
    openapi_tags=tags_metadata
)

# from .dependencies.config import test, populate
@app.on_event("startup")
def on_startup():
    init_db()
    # populate()
    # test()

#=============================================
# Router inclusions
#=============================================
app.include_router(cameras.router)
app.include_router(auth.router)


#=============================================
# Main endpoints
#=============================================

@app.get("/")
async def root():
    return {"message": "FastAPI WebSocket and RTMP Server"}


@app.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """The websocket connection endpoint

    Args:
        websocket (WebSocket)
    """
    
    client_id = None
    
    try:
        await authenticate_websocket_user(websocket)
    
        client_id = await cameras.client_manager.connect(websocket)
        
        while websocket.client_state != WebSocketState.DISCONNECTED:
            
            data = await websocket.receive_text()
    except (HTTPException):
        print("Invalid WebSocket authentication")
        
    except WebSocketDisconnect:
        print("Client quit unexpectedly")
    
    finally:
        await cameras.client_manager.disconnect(client_id)