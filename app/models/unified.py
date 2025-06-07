from pydantic import BaseModel, Field # Add Field
from typing import Optional, List
from .address import AddressInput, GeocodeResponse
from .property import PropertyDetails, ListingStatus, ComparableSale
from .market import MarketMetrics

class UnifiedPropertyResponse(BaseModel):
    input_address: AddressInput = Field(..., description="The original address input provided by the user.")
    geocode: Optional[GeocodeResponse] = Field(None, description="Geocoding results including latitude, longitude, and standardized address.")
    details: Optional[PropertyDetails] = Field(None, description="Detailed information about the property (structure, parcel, etc.).")
    listing_info: Optional[ListingStatus] = Field(None, description="Current or last known listing status of the property.")
    comparable_sales: Optional[List[ComparableSale]] = Field(None, description="List of comparable property sales.")
    market_metrics: Optional[MarketMetrics] = Field(None, description="Market metrics for the property's area (city or ZIP).")
    errors: Optional[List[str]] = Field(None, description="A list of errors or warnings encountered during data retrieval for any part of the process.")
