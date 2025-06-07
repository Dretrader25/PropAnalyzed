from pydantic import BaseModel
from typing import Optional, List
from .address import AddressInput, GeocodeResponse
from .property import PropertyDetails, ListingStatus, ComparableSale
from .market import MarketMetrics

class UnifiedPropertyResponse(BaseModel):
    input_address: AddressInput
    geocode: Optional[GeocodeResponse] = None
    details: Optional[PropertyDetails] = None
    listing_info: Optional[ListingStatus] = None
    comparable_sales: Optional[List[ComparableSale]] = None
    market_metrics: Optional[MarketMetrics] = None
    errors: Optional[List[str]] = None # To report any issues during data fetching
