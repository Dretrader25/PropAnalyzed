import httpx
from typing import Optional, List, Dict, Any
from app.models.property import ComparableSale
from app.config.settings import Settings
import logging

logger = logging.getLogger(__name__)

def transform_rentcast_comp_response(comp_data: Dict[str, Any], source_address: str) -> Optional[ComparableSale]:
    """Transforms a single RentCast comparable sale item to ComparableSale model."""
    if not comp_data:
        return None

    # Example mapping - Adjust based on actual RentCast API response structure for comps
    # (e.g. from https://developers.rentcast.io/reference/retrievepropertycomparablesales)

    # Assuming comp_data is one item from the list of comparables
    return ComparableSale(
        source_api="RentCast",
        address=comp_data.get('formattedAddress', 'N/A'), # Or construct from components
        sale_date=comp_data.get('lastSaleDate'), # Ensure date format consistency
        sale_price=comp_data.get('lastSalePrice'),
        beds=comp_data.get('bedrooms'),
        baths=comp_data.get('bathrooms'), # RentCast uses 'bathrooms'
        square_footage=comp_data.get('livingArea'), # RentCast uses 'livingArea'
        distance_miles=comp_data.get('distance'), # RentCast provides 'distance' in miles
        raw_response=comp_data
    )

async def fetch_comps_rentcast(
    address: str, # RentCast API takes a street address for the subject property
    settings: Settings
) -> Optional[List[ComparableSale]]:
    """Fetches comparable sales from the RentCast API using address."""
    if not settings.RENTCAST_API_KEY or settings.RENTCAST_API_KEY == "YOUR_RENTCAST_API_KEY_HERE":
        logger.warning("RentCast API key not configured for comps.")
        return None

    # RentCast API endpoint for retrieving comparable sales:
    # GET https://api.rentcast.io/v1/properties/comps?address={address}
    # Optional params: radius, daysBack, propertyTypes, etc.
    api_url = "https://api.rentcast.io/v1/properties/comps"
    params = {"address": address, "radius": 5, "daysBack": 180} # Example params
    headers = {"X-Api-Key": settings.RENTCAST_API_KEY, "accept": "application/json"}

    logger.info(f"Attempting to fetch comparable sales from RentCast for: {address}")

    # SIMULATED RESPONSE - REMOVE/REPLACE WITH ACTUAL API CALL
    if "123 Main St, Anytown, CA 90210" in address: # Example successful address
        logger.info(f"SIMULATING RentCast Comps API success for: {address}")
        simulated_data = [
            {
                "id": "comp1", "formattedAddress": "10 Market St, Anytown, CA 90210", "lastSaleDate": "2023-05-10",
                "lastSalePrice": 480000, "bedrooms": 3, "bathrooms": 2, "livingArea": 1950, "distance": 0.5
            },
            {
                "id": "comp2", "formattedAddress": "20 Ocean Ave, Anytown, CA 90210", "lastSaleDate": "2023-04-15",
                "lastSalePrice": 510000, "bedrooms": 4, "bathrooms": 2.5, "livingArea": 2100, "distance": 0.8
            }
        ]
        comps_list = [transform_rentcast_comp_response(c, address) for c in simulated_data]
        return [comp for comp in comps_list if comp is not None]
    elif "No Comps St, Anytown, CA" in address:
         logger.info(f"SIMULATING RentCast Comps API - no comps for: {address}")
         return []
    else: # Simulate not found or error for other addresses
        logger.warning(f"SIMULATING RentCast Comps API - address not found or error for: {address}")
        return None


    # ACTUAL API CALL (commented out, replace placeholder above)
    # try:
    #     async with httpx.AsyncClient() as client:
    #         response = await client.get(api_url, params=params, headers=headers)
    #         response.raise_for_status()
    #         data = response.json() # RentCast comps endpoint returns a list of comp objects
    #
    #         if data and isinstance(data, list):
    #             transformed_comps = [transform_rentcast_comp_response(item, address) for item in data]
    #             return [comp for comp in transformed_comps if comp is not None] # Filter out None results
    #         elif isinstance(data, list) and not data: # Empty list is a valid response (no comps)
    #              logger.info(f"RentCast returned no comparable sales for {address}")
    #              return []
    #         else:
    #             logger.warning(f"RentCast Comps API returned unexpected data for {address}. Response: {data}")
    #             return None
    # except httpx.HTTPStatusError as e:
    #     logger.error(f"HTTP error calling RentCast Comps API for {address}: {e}. Response: {e.response.text if e.response else 'No response text'}")
    #     return None
    # except Exception as e:
    #     logger.error(f"Generic error calling RentCast Comps API for {address}: {e}")
    #     return None
