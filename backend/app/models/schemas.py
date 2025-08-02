from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class SynthesizeRequest(BaseModel):
    forge_id: str

class SynthesizeResponse(BaseModel):
    success: bool
    message: str
    synthesis_id: Optional[str] = None
    error: Optional[str] = None

class ChatRequest(BaseModel):
    forge_id: str
    role_id: str
    message: str
    is_question: bool = False

class ChatResponse(BaseModel):
    success: bool
    message: str
    ai_response: Optional[str] = None
    error: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None 