from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class PropertyDetails(BaseModel):
    # Example fields - these should be refined based on actual API responses
    # from Estated and Zillow to find commonality or use Optional liberally.
    source_api: Optional[str] = None # To indicate if it's from Estated or Zillow
    parcel_number: Optional[str] = None
    beds: Optional[int] = None
    baths: Optional[float] = None # Can be 1.5 baths
    square_footage: Optional[int] = None
    lot_size_sqft: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    deed_history: Optional[List[Dict[str, Any]]] = None # Define more strictly if possible
    # Add more fields as necessary
    raw_response: Optional[Dict[str, Any]] = None # To store the original API response if needed

class ListingStatus(BaseModel):
    source_api: Optional[str] = None
    is_for_sale: Optional[bool] = None
    is_for_rent: Optional[bool] = None # Rentcast specific
    status: Optional[str] = None # e.g., "For Sale", "Off Market"
    list_price: Optional[float] = None
    days_on_market: Optional[int] = None
    raw_response: Optional[Dict[str, Any]] = None

class ComparableSale(BaseModel):
    source_api: Optional[str] = None
    address: str
    sale_date: Optional[str] = None # Consider using date type after validation
    sale_price: Optional[float] = None
    beds: Optional[int] = None
    baths: Optional[float] = None
    square_footage: Optional[int] = None
    distance_miles: Optional[float] = None
    raw_response: Optional[Dict[str, Any]] = None
