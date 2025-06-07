from pydantic import BaseModel, field_validator
from typing import Optional

class AddressInput(BaseModel):
    address: str

    @field_validator('address')
    @classmethod
    def address_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Address must not be empty')
        return v

class GeocodeResponse(BaseModel):
    latitude: float
    longitude: float
    standardized_address: Optional[str] = None # If geocoder provides a standardized version
