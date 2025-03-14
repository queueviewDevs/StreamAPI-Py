from fastapi import WebSocket, HTTPException, WebSocketDisconnect
from starlette.websockets import WebSocketState
from typing import Dict
from .camera import CameraClient
from .general import StreamCommand

# Store connected clients
class ClientManager:
    def __init__(self):
        self.clients: Dict[int, CameraClient] = {}
        self.websockets: Dict[int, WebSocket] = {}

        
    def getClients(self):
        """Get a list of all connected camera clients

        Returns:
            list[CameraClient]: List of camera clients
        """
        
        return list(self.clients.values())
    
    def getClient(self, client_id: int) -> CameraClient:
        """Get a specific camera client by its ID

        Args:
            client_id (int): camera client ID

        Returns:
            CameraClient: The camera client object
        """
        
        cam = self.clients.get(client_id)
        if cam is None:
            raise HTTPException(status_code=404, detail=f"Camera id {client_id} currently not connected")
        return cam
    
    
    def updateClient(self, client_id: int, client_data: dict) -> CameraClient:
        """Update a client"""
          
        self.clients[client_id].update(client_data)
        return self.clients[client_id]
    

    async def connect(self, websocket: WebSocket):
        """Now storing websocket in separate dict, need to implement logic for camera to 
        make a secondary call with its metadata to be stored in the clients dict"""

        await websocket.accept()
        identification = await websocket.receive_json()

        client_id = identification.get("id")
        self.clients[client_id] = CameraClient(
            id=client_id,
            name=identification.get("name"),
            connected=identification.get("connected"),
            streaming=identification.get("streaming"),
            liveStreamURL=identification.get("liveStreamURL")
        )
        
        self.websockets[client_id] = websocket
        
        print(f"Client {client_id} connected.")
        return client_id

    async def disconnect(self, client_id: str):
        try:
            if client_id in self.websockets:
                if self.websockets[client_id].client_state != WebSocketState.DISCONNECTED:
                    await self.websockets[client_id].close()
                
                del self.websockets[client_id]
                del self.clients[client_id]
                print(f"Client {client_id} disconnected!")
            
        except WebSocketDisconnect:
            print("Websocket disconnect error")
        except HTTPException as http_err:
            print(http_err.detail)

    async def send_message(self, client_id: int, message: dict):
        """Send a message to a raspberry pi camera client

        Args:
            client_id (int): _description_
            message (dict): _description_
        """
        if client_id not in self.clients:
            raise HTTPException(status_code=404, detail=f"Camera id {client_id} currently not connected")
        
        websocket = self.websockets.get(client_id)
        if websocket is None or websocket.client_state == WebSocketState.DISCONNECTED:
            raise HTTPException(status_code=404, detail=f"WebSocket for camera id {client_id} is not connected")
        try:
            await websocket.send_json(message)
        except WebSocketDisconnect:
            print(f"WebSocket disconnected for client {client_id}")
            await self.disconnect(client_id)
        except Exception as e:
            print(f"Error sending message to {client_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Internal system error when sending command to camera id {client_id}")
                
    async def send_command(self, client_id: int, command: StreamCommand):
        """Send a command to a raspberry pi camera client. To be implemented

        Args:
            client_id (int): _description_
            command (StreamCommand): _description_
        """
        pass

    async def broadcast(self, message: dict):
        for client_id, websocket in self.websockets.items:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to {client_id}: {e}")
                