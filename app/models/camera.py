from pydantic import BaseModel

class CameraClient(BaseModel):
    id: str
    name: str
    connected: bool
    streaming: bool = False
    liveStreamURL: str = ""
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "pi_001",
                    "name": "laurier-pubOnKing-NorthCam",
                    "connected": True
                }
            ]
        }
    }
    
    def update(self, updates: dict):
        for key, value in updates.items():
            if key != "id" and hasattr(self, key):
                setattr(self, key, value)