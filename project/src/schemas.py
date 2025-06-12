from pydantic import BaseModel
from typing import Dict, Any

class ProfileUpdate(BaseModel):
    username: str
    email: str
    role: str

class StoreDetails(BaseModel):
    details: Dict[str, Any]

class StoreData(BaseModel):
    data: Dict[str, Any]

class SaveDatasetRequest(BaseModel):
    file_id: str
    extracted_data: Dict[str, Any]
