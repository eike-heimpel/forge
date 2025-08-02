from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator, PlainSerializer
from pydantic_core import core_schema
from bson import ObjectId


def utc_now() -> datetime:
    """Helper function for timezone-aware UTC datetime"""
    return datetime.now(timezone.utc)


class PyObjectId(str):
    """Custom ObjectId type for Pydantic that generates proper JSON schemas"""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        """Generate core schema for Pydantic v2"""
        def validate_object_id(v: Any) -> ObjectId:
            if isinstance(v, ObjectId):
                return v
            if isinstance(v, str) and ObjectId.is_valid(v):
                return ObjectId(v)
            raise ValueError("Invalid ObjectId format")
        
        return core_schema.no_info_after_validator_function(
            validate_object_id,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema()
        )


# ===============================
# FORGE COLLECTIONS
# ===============================

class ForgeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    COMPLETED = "COMPLETED"


class MemberRole(str, Enum):
    OWNER = "owner"
    MEMBER = "member"


class ForgeMember(BaseModel):
    userId: PyObjectId = Field(alias="_id")
    role: MemberRole


class Forge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    goal: str
    status: ForgeStatus = ForgeStatus.ACTIVE
    createdAt: datetime = Field(default_factory=utc_now)
    lastSynthesisId: Optional[PyObjectId] = None
    members: List[ForgeMember]


# ===============================
# CONTRIBUTION COLLECTIONS
# ===============================

class ContributionType(str, Enum):
    USER_MESSAGE = "USER_MESSAGE"
    AI_RESPONSE = "AI_RESPONSE"
    AI_SYNTHESIS = "AI_SYNTHESIS"


class UserMessageContent(BaseModel):
    text: str


class AIResponseContent(BaseModel):
    text: str


class AISynthesisStructured(BaseModel):
    currentState: str
    emergingConsensus: str
    outstandingQuestions: List[str]
    nextStepsNeeded: str


class AISynthesisContent(BaseModel):
    structured: AISynthesisStructured


class Contribution(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    forgeId: PyObjectId
    authorId: PyObjectId
    type: ContributionType
    createdAt: datetime = Field(default_factory=utc_now)
    content: Union[UserMessageContent, AIResponseContent, AISynthesisContent]
    sourceContributionIds: Optional[List[PyObjectId]] = []


# ===============================
# AI PROMPTS COLLECTION
# ===============================

class PromptStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class ResponseFormat(BaseModel):
    type: str  # "text" or "json_object"


class PromptParameters(BaseModel):
    model: str = "google/gemini-2.5-flash"
    temperature: float = 0.7
    max_tokens: int = 1000
    response_format: Optional[ResponseFormat] = None


class AIPrompt(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    version: int
    status: PromptStatus = PromptStatus.ACTIVE
    description: str
    parameters: PromptParameters
    expected_vars: List[str]
    template: str
    assertivenessLevel: Optional[int] = None  # For synthesis prompts


# ===============================
# AI TRIAGE RESPONSES
# ===============================

class TriageAction(str, Enum):
    LOG_ONLY = "LOG_ONLY"
    ANSWER_DIRECTLY = "ANSWER_DIRECTLY" 
    SYNTHESIZE = "SYNTHESIZE"


class TriageResponse(BaseModel):
    action: TriageAction


# ===============================
# WEBHOOK REQUEST/RESPONSE MODELS
# ===============================

class ProcessContributionRequest(BaseModel):
    forgeId: str  # String representation of ObjectId
    newContributionId: str  # String representation of ObjectId


class ProcessContributionResponse(BaseModel):
    status: str
    message: str
    contributionId: str


# ===============================
# API RESPONSE MODELS
# ===============================

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime = Field(default_factory=utc_now) 


# ===============================
# PROMPT TESTING API SCHEMAS
# ===============================

class PromptInfo(BaseModel):
    """Basic prompt information for listing/discovery"""
    name: str
    version: int
    description: str
    expected_vars: List[str]
    parameters: PromptParameters
    assertivenessLevel: Optional[int] = None


class PromptTestRequest(BaseModel):
    """Request to test a prompt with provided variables"""
    variables: Dict[str, Any]
    

class PromptTestResponse(BaseModel):
    """Response from testing a prompt"""
    prompt_name: str
    prompt_version: int
    rendered_prompt: str
    model_response: str
    execution_time_ms: int
    model_used: str
    tokens_used: Optional[int] = None
    

class PromptsListResponse(BaseModel):
    """Response listing available prompts"""
    prompts: List[PromptInfo]
    total_count: int


class PromptDetailResponse(BaseModel):
    """Detailed information about a specific prompt"""
    prompt: PromptInfo
    template_preview: str  # First 200 chars of template
    sample_variables: Dict[str, str]  # Example values for each expected var 