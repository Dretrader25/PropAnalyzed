import httpx
from typing import Optional, Dict, Any
from app.models.property import PropertyDetails
from app.config.settings import Settings
import logging

logger = logging.getLogger(__name__)

def transform_estated_response(response_data: Dict[str, Any], standardized_address: str) -> Optional[PropertyDetails]:
    """Transforms Estated API response to PropertyDetails model."""
    if not response_data or not response_data.get('properties'):
        logger.warning(f"Estated response missing 'properties' for address: {standardized_address}")
        return None

    prop = response_data['properties'][0] # Assuming the first property is the one we want

    # Example mapping - This needs to be adjusted based on actual Estated API response structure
    # Refer to Estated documentation for correct field names.
    # This is a placeholder structure.
    details = prop.get('deeds', [{}])[0] # Taking the most recent deed for some info
    address_info = prop.get('address', {})
    building_info = prop.get('building', {})
    parcel_info = prop.get('parcel', {})

    beds = None
    if building_info.get('rooms', {}).get('beds_count') is not None:
        beds = int(building_info['rooms']['beds_count'])

    baths = None
    if building_info.get('rooms', {}).get('baths_total') is not None:
        # Baths can be float (e.g., 1.5)
        try:
            baths = float(building_info['rooms']['baths_total'])
        except ValueError:
            logger.warning(f"Could not parse baths_total: {building_info['rooms']['baths_total']}")


    return PropertyDetails(
        source_api="Estated",
        parcel_number=parcel_info.get('fips_code'), # Or other parcel ID from Estated
        beds=beds,
        baths=baths,
        square_footage=building_info.get('size', {}).get('gross_living_area_sq_ft'),
        lot_size_sqft=parcel_info.get('area_sq_ft'),
        year_built=building_info.get('construction', {}).get('year_built'),
        property_type=parcel_info.get('property_type_description'), # Example
        deed_history=prop.get('deeds'), # Pass full deed history if available and useful
        raw_response=prop # Store the specific property part of the response
    )

async def fetch_property_details_estated(
    standardized_address: str, # Or ideally, structured components if Estated prefers
    settings: Settings
) -> Optional[PropertyDetails]:
    """Fetches property details from the Estated API."""
    if not settings.ESTATED_API_KEY or settings.ESTATED_API_KEY == "YOUR_ESTATED_API_KEY_HERE":
        logger.warning("Estated API key not configured.")
        return None

    # Estated API endpoint and parameters need to be confirmed from their documentation.
    # This is a common structure:
    # endpoint = "https://api.estated.com/v4/property"
    # params = {
    #     "token": settings.ESTATED_API_KEY,
    #     "address": standardized_address_components.get('StreetName'), # Example: Estated might take components
    #     "city": standardized_address_components.get('PlaceName'),
    #     "state": standardized_address_components.get('StateName'),
    #     "zip_code": standardized_address_components.get('ZipCode')
    # }
    # For now, let's assume a simple address string if component details aren't passed.
    # The Estated API might require separate parameters for street, city, state, zip.
    # Using a placeholder for the actual API call structure.

    # Placeholder: Using sandbox URL for Estated if available, or a known test endpoint.
    # The actual Estated API endpoint for property data by address:
    # https://api.estated.com/property/v3?token=YOUR_TOKEN&address=123%20Main%20St&city=Denver&state=CO&zipcode=80205
    # This requires parsing the standardized_address into components.
    # For simplicity in this step, we'll assume standardized_address is sufficient or we'd need
    # to pass components from the geocoding step. Let's assume it's a full string for now.

    # A more robust implementation would parse standardized_address or use components from geocoding.
    # For this example, we'll assume the address string is what Estated needs.
    # A more robust version would parse `standardized_address` into street, city, state, zip.
    # For now, this is a simplified placeholder for the API call.

    # This is a MOCK API call structure. Replace with actual Estated API call.
    # Due to not having live API access during this task, I will simulate a response.
    # In a real scenario, this would be an actual HTTP request.
    logger.info(f"Attempting to fetch property details from Estated for: {standardized_address}")

    # SIMULATED RESPONSE - REMOVE/REPLACE WITH ACTUAL API CALL
    if "123 Main St, Anytown, CA 90210" in standardized_address: # Example successful address
        logger.info(f"SIMULATING Estated API success for: {standardized_address}")
        simulated_data = {
            "status": "success",
            "properties": [{
                "address": {"street_address": "123 Main St", "city": "Anytown", "state": "CA", "zip_code": "90210"},
                "parcel": {"fips_code": "0603712345", "area_sq_ft": 7500, "property_type_description": "Single Family Residential"},
                "building": {
                    "size": {"gross_living_area_sq_ft": 2000},
                    "rooms": {"beds_count": 3, "baths_total": 2.5},
                    "construction": {"year_built": 1985}
                },
                "deeds": [{"document_type": "Grant Deed", "recording_date": "2010-05-15"}]
            }]
        }
        return transform_estated_response(simulated_data, standardized_address)
    elif "Error Address" in standardized_address: # Example error address
         logger.warning(f"SIMULATING Estated API error for: {standardized_address}")
         return None
    else: # Simulate not found for other addresses
        logger.warning(f"SIMULATING Estated API - address not found: {standardized_address}")
        return None

    # ACTUAL API CALL (commented out, replace placeholder above)
    # headers = {"Authorization": f"Bearer {settings.ESTATED_API_KEY}"} # Or token in params
    # params = {"address": standardized_address} # This depends heavily on Estated's API
    # api_url = "YOUR_ESTATED_API_ENDPOINT_HERE"
    # try:
    #     async with httpx.AsyncClient() as client:
    #         response = await client.get(api_url, params=params, headers=headers)
    #         response.raise_for_status() # Raise an exception for bad status codes
    #         data = response.json()
    #         if data.get("status") == "success" and data.get("properties"): # Check success from Estated
    #             return transform_estated_response(data, standardized_address)
    #         else:
    #             logger.warning(f"Estated API returned non-success or no properties for {standardized_address}. Status: {data.get('status')}")
    #             return None
    # except httpx.HTTPStatusError as e:
    #     logger.error(f"HTTP error calling Estated API for {standardized_address}: {e}")
    #     return None
    # except Exception as e:
    #     logger.error(f"Generic error calling Estated API for {standardized_address}: {e}")
    #     return None
