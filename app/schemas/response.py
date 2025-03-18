from typing import Optional, Any
from pydantic import BaseModel, Field


class ResponseMetaSchema(BaseModel):
    """
    Schema for the meta information in API responses.
    """
    status: str = Field(..., description="Description of the status code")
    status_code: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Status description")
    details: Optional[str] = Field(None, description="Additional details or error information")



class ResponseSchema(BaseModel):
    """
    Schema for the standardized API response.
    """
    data: Optional[Any] = Field(None, description="Response data payload")
    meta: ResponseMetaSchema = Field(..., description="Response metadata")