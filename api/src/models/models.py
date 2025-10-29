from pydantic import BaseModel, Field
from typing import Union, Optional, Dict, Any

class OutboundCallPayloadModel(BaseModel):
    """Payload model for outbound call route"""
    phone_number: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    use_agent: bool = Field(default=False, description="Whether to use Azure AI Foundry Agent Service")
    persona: Optional[str] = Field(default="default", description="System message persona to use (default, recruitment)")
    
    # Legacy fields for backward compatibility
    candidate_name: Optional[str] = None
    candidate_data: Optional[Union[dict, str]] = None
    job_data: Optional[Union[dict, str]] = None
    
    # Generic data field for any additional data
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"  # Allow additional fields
