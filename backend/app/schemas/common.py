"""Standard API error shape and common response models."""
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error_code: str
    message: str
