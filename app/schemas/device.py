from pydantic import BaseModel, Field
from typing import Optional, Annotated, List
from datetime import datetime, timezone
from bson import ObjectId


from pydantic.functional_validators import BeforeValidator
PyObjectId = Annotated[str, BeforeValidator(str)]


# class PyObjectId(ObjectId):
#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate

#     @classmethod
#     def validate(cls, v):
#         if not ObjectId.is_valid(v):
#             raise ValueError("Invalid ObjectId")
#         return ObjectId(v)

#     @classmethod
#     def __modify_schema__(cls, field_schema):
#         field_schema.update(type="string")



class Location(BaseModel):
    venue_name: str = Field(..., example="Prohibition Warehouse")
    address: str = Field(..., example="56 King Street North")
    city: str = Field(..., example="Waterloo")
    postal: str = Field(..., example="N2J 2X1")
    province: str = Field(..., example="Ontario")
    
    
    
class LocationUpdate(Location):
    venue_name: Optional[str] = Field(None, example="Prohibition Warehouse")
    address: Optional[str] = Field(None, example="56 King Street North")
    city: Optional[str] = Field(None, example="Waterloo")
    postal: Optional[str] = Field(None, example="N2J 2X1")
    province: Optional[str] = Field(None, example="Ontario")
    
    
    
class Metadata(BaseModel):
    location: Location
    description: str = Field(..., example="Mounted to utility mole pointing north")



class MetadataUpdate(Metadata):
    location: Optional[LocationUpdate] = None
    description: Optional[str] = Field(None, description="Updated description of the device")



class DeviceBase(BaseModel):
    device_id: str = Field(..., example="pi_0001")
    api_key: str = Field(...)
    status: Optional[str] = Field(default="active", example="active")
    revoked: Optional[bool] = Field(default=False, example=True)
    metadata: Metadata

    

class Device(DeviceBase):
    """Used for DB purposes"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: datetime | None = Field(None)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        
        
        
class DeviceCollection(BaseModel):
    """A container holding a list of `Device` instances"""
    devices: List[Device]
    
    
    
    
class DeviceUpdate(DeviceBase):
    device_id: Optional[str] = Field(None)
    api_key: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    revoked: Optional[bool] = Field(None)
    metadata: Optional[MetadataUpdate] = None
    
    

class DeviceQuery(BaseModel):
    """A model used for querying the devices collection"""
    device_id: Optional[str] = Field(None, description="Filter by device_id")
    status: Optional[str] = Field(None, description="Filter by device status")
    revoked: Optional[bool] = Field(None, description="Filter by revoked status")