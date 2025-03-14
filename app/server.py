from fastapi import FastAPI
from .routers import cameras, auth, nginx, devices, devices, users
from .dependencies.db import create_indexes

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
        "name": "NGINX",
        "description": "Internal endpoints called by NGINX"
    },
    {
        "name": "Devices",
        "description": "Operations on the devices database collection. Requires admin user privilleges"
    },
    {
        "name": "Users",
        "description": "Operations on the users database collection. Requires admin user privilleges"
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


@app.on_event("startup")
async def startup():
    await create_indexes()


#=============================================
# Router inclusions
#=============================================
app.include_router(cameras.router)
app.include_router(auth.router)
app.include_router(nginx.router)
app.include_router(devices.router)
app.include_router(users.router)


#=============================================
# Main endpoints
#=============================================

@app.get("/")
async def root():
    return {"message": "FastAPI WebSocket and RTMP Server"}
