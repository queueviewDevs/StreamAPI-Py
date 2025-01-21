from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional
import asyncio
import uuid

app = FastAPI()

# Store connected clients
class ClientManager:
    def __init__(self):
        self.clients: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        client_id = str(uuid.uuid4())  # Generate a unique ID for each client
        self.clients[client_id] = websocket
        print(f"Client {client_id} connected.")
        return client_id

    def disconnect(self, client_id: str):
        if client_id in self.clients:
            del self.clients[client_id]
            print(f"Client {client_id} disconnected.")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.clients:
            try:
                await self.clients[client_id].send_json(message)
            except Exception as e:
                print(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        for client_id, websocket in self.clients.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to {client_id}: {e}")
                self.disconnect(client_id)


# Shared client manager
client_manager = ClientManager()

# Authentication token
AUTH_TOKEN = "secret"


class StreamCommand(BaseModel):
    stream: Optional[bool] = False  # True for start, False for stop


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    
    # Authenticate client by checking headers
    token = websocket.headers.get("Authorization")
    if token != f"Bearer {AUTH_TOKEN}":
        await websocket.close(code=4001)
        print("Authentication failed: Invalid token.")
        return

    # Connect the client
    client_id = await client_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received message from {client_id}: {data}")
            # Handle incoming messages (e.g., status updates)
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected.")
        client_manager.disconnect(client_id)
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
        client_manager.disconnect(client_id)


@app.post("/api/camera/{client_id}/stream")
async def control_camera_stream(client_id: str, command: StreamCommand):
    """
    Send a start/stop streaming command to a specific client by its ID.
    """
    if client_id not in client_manager.clients:
        return JSONResponse(
            status_code=404, content={"error": "Client not connected"}
        )

    action = "start" if command.stream else "stop"
    message = {"action": action}
    await client_manager.send_message(client_id, message)
    return {"status": f"Command '{action}' sent to client {client_id}"}


@app.get("/")
async def root():
    return {"message": "FastAPI WebSocket and RTMP Server"}
