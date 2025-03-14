from fastapi import APIRouter, HTTPException, Depends, status, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocketState
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from ..dependencies.db import devices_collection
from ..schemas.device import DeviceCollection, Device, DeviceBase, DeviceQuery, DeviceUpdate
from ..auth.auth import authenticate_websocket_user
from ..routers.cameras import client_manager

#Will authenticate and interact with devices collection

router = APIRouter(
    prefix="/api/devices",
    tags=["Devices"]
)

@router.get(
    path="/",
    response_description="Get all devices",
    response_model=DeviceCollection,
    response_model_by_alias=False
)
async def get_devices(query: DeviceQuery = Depends()) -> DeviceCollection:
    """
    List all of the devices in the database
    
    The response is unpaginated and limited to 1000 results
    """
    filters = query.model_dump(exclude_none=True)
    devices = await devices_collection.find(filters).to_list(1000)
    return DeviceCollection(devices=devices)
    


@router.get(
    path="/{id}",
    description="Get a single device",
    response_model=Device,
    response_model_by_alias=False
)
async def get_device(id: str) -> Device:
    """Get a single device by its mongo _id

    Returns:
    Device: _description_
    """
    device = await devices_collection.find_one({"_id": ObjectId(id)})
    if device:
        return device
    
    raise HTTPException(status_code=404, detail=f"Device with {id} not found")



@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """The websocket connection endpoint

    Args:
        websocket (WebSocket)
    """
    
    client_id = None
    
    try:
        device = await authenticate_websocket_user(websocket)
    
        client_id = await client_manager.connect(websocket)
        
        while websocket.client_state != WebSocketState.DISCONNECTED:
            
            data = await websocket.receive_text()
    except (HTTPException):
        print("Invalid WebSocket authentication")
        
    except WebSocketDisconnect:
        print("Client quit unexpectedly")
    
    finally:
        await client_manager.disconnect(client_id)
      
      
        
@router.post(
    path="/",
    description="Create a device",
    response_model=Device,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False
)
async def create_device(device: DeviceBase) -> Device:
    """Create a device"""
    
    device_id = device.device_id
    try:
        new_device = await devices_collection.insert_one(device.model_dump(by_alias=True, exclude=["id"]))
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail=f"A device with device_id {device_id} already exists")
    
    created_device = await devices_collection.find_one({"_id": new_device.inserted_id})
    return created_device



@router.put(
    path="/{id}",
    description="Update a device",
    response_model=Device,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False
)
async def update_device(id: str, device: DeviceUpdate) -> Device:
    """Update a device by its _id"""
    update_payload = device.model_dump(by_alias=True, exclude_none=True)
    
    if len(update_payload) >= 1:
        
        try:
            update_result = await devices_collection.find_one_and_update(
                {"_id": ObjectId(id)},
                {"$set": update_payload},
                return_document=ReturnDocument.AFTER
            )
        except DuplicateKeyError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Duplicate key error",
                    "message": "Record with given unique field value already exists",
                    "field": "device_id"
                }
            )
        
        if update_result:
            return update_result
        else:
            raise HTTPException(status_code=404, detail=f"Device with {id} not found")
    
    #Update is empty, but still return the matching document
    existing_device = await devices_collection.find_one({"_id": ObjectId(id)})
    if existing_device:
        return existing_device
    
    raise HTTPException(status_code=404, detail=f"Device with {id} not found")

@router.delete(
    path="/{id}",
    description="Delete a device"
)
async def delete_device(id: str):
    """Delete a device by it's _id"""
    delete_result = await devices_collection.delete_one({"_id": ObjectId(id)})
    
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    raise HTTPException(status_code=404, detail=f"Device with {id} not found")