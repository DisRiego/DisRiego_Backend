from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DisableLotRequest(BaseModel):
    details: Optional[str] = None

class HistoryEntry(BaseModel):
    id: int
    action: str
    details: Optional[str] = None
    timestamp: datetime
    user: dict

    class Config:
        from_attributes = True

class LotHistoryResponse(BaseModel):
    success: bool
    data: List[HistoryEntry]

class DisableLotResponse(BaseModel):
    success: bool
    data: dict

    class Config:
        from_attributes = True