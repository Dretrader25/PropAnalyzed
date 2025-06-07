from pydantic import BaseModel
from typing import Optional

class MarketMetrics(BaseModel):
    source: str = "Redfin CSV"
    query_area: str # e.g., city or ZIP
    average_dom: Optional[float] = None
    median_sale_price: Optional[float] = None
    price_trends_6m: Optional[str] = None # e.g., "up 5%", "down 2%"
    inventory_level: Optional[str] = None # e.g., "low", "balanced"
    # Add more fields as necessary
