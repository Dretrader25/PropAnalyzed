import httpx
import usaddress # type: ignore
from typing import Optional, Tuple, Dict, Any
from app.models.address import GeocodeResponse
from app.config.settings import Settings
import logging

logger = logging.getLogger(__name__)

async def standardize_address(address_str: str) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    """
    Standardizes the address using usaddress.
    Returns a tuple: (standardized_address_string, address_components_dict).
    Returns (None, None) if parsing fails.
    """
    try:
        # usaddress can sometimes return a list of tuples if it finds multiple parts,
        # but for a single address string, it's usually one TaggedAddress.
        # It might also raise usaddress.RepeatedLabelError if parsing is ambiguous.
        tagged_address, address_type = usaddress.tag(address_str)

        # Reconstruct a somewhat standardized string. This is a basic approach.
        # You might want a more sophisticated reconstruction based on address_type.
        # For many APIs, sending components separately is better if the API supports it.
        # For now, let's create a simple string and also return components.

        parts = []
        # Common components, order might matter for some geocoders if sending as a single string
        desired_order = ['AddressNumber', 'StreetNamePreDirectional', 'StreetName', 'StreetNamePostType',
                         'OccupancyType', 'OccupancyIdentifier', 'PlaceName', 'StateName', 'ZipCode']

        temp_parts = {comp: tagged_address.get(comp) for comp in desired_order if tagged_address.get(comp)}

        # Simple string reconstruction
        # Address line 1
        addr_line1_parts = [temp_parts.get('AddressNumber'), temp_parts.get('StreetNamePreDirectional'),
                            temp_parts.get('StreetName'), temp_parts.get('StreetNamePostType'),
                            temp_parts.get('OccupancyType'), temp_parts.get('OccupancyIdentifier')]
        addr_line1 = ' '.join(p for p in addr_line1_parts if p)
        if addr_line1:
            parts.append(addr_line1)

        # City, State ZIP
        city = temp_parts.get('PlaceName')
        state = temp_parts.get('StateName')
        zip_code = temp_parts.get('ZipCode')

        if city:
            parts.append(city)
        if state:
            parts.append(state)
        if zip_code:
            parts.append(zip_code)

        # Join parts, handling cases where city might be missing but state/zip exist
        # This reconstruction is basic. For Google, sending components is more robust.
        final_address_str = ""
        if addr_line1:
            final_address_str += addr_line1
        if city:
            final_address_str += f", {city}" if final_address_str else city
        if state:
            final_address_str += f", {state}" if final_address_str else state
        if zip_code:
            final_address_str += f" {zip_code}" if final_address_str else zip_code

        # Also return the component dictionary
        # Convert all values in tagged_address to string, as they might be other types
        component_dict = {k: str(v) for k, v in tagged_address.items()}

        return final_address_str.strip(), component_dict

    except usaddress.RepeatedLabelError as e:
        logger.warning(f"Could not parse address '{address_str}' due to repeated labels: {e}")
        return None, None
    except Exception as e:
        logger.error(f"An unexpected error occurred during address parsing for '{address_str}': {e}")
        return None, None


async def geocode_google(address_components: Dict[str, str], settings: Settings) -> Optional[GeocodeResponse]:
    """Geocodes an address using Google Maps API, prioritizing component-based geocoding."""
    if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "YOUR_GOOGLE_API_KEY_HERE":
        logger.warning("Google API key not configured.")
        return None

    params = {"key": settings.GOOGLE_API_KEY}

    # Construct address string from components for Google
    # Google prefers 'address' parameter as a single string, or 'components'
    # Let's try to build a good single string from components
    # This is just one way; Google's component geocoding might be more robust if you map
    # usaddress fields directly to Google's component filters.
    addr_parts = []
    if 'AddressNumber' in address_components and 'StreetName' in address_components:
        addr_parts.append(f"{address_components.get('AddressNumber', '')} {address_components.get('StreetNamePreDirectional','')} {address_components.get('StreetName','')} {address_components.get('StreetNamePostType','')}".strip())
    if 'PlaceName' in address_components:
        addr_parts.append(address_components['PlaceName'])
    if 'StateName' in address_components:
        addr_parts.append(address_components['StateName'])
    if 'ZipCode' in address_components:
        addr_parts.append(address_components['ZipCode'])

    address_str = ", ".join(filter(None, addr_parts))
    if not address_str:
        logger.warning("Could not construct a valid address string from components for Google.")
        return None

    params['address'] = address_str

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://maps.googleapis.com/maps/api/geocode/json", params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("status") == "OK" and data.get("results"):
            result = data["results"][0]
            location = result["geometry"]["location"]
            # Try to get a standardized address from Google's response
            formatted_address = result.get("formatted_address")
            return GeocodeResponse(
                latitude=location["lat"],
                longitude=location["lng"],
                standardized_address=formatted_address
            )
        else:
            logger.warning(f"Google Geocoding API returned status: {data.get('status')} for address: {address_str}")
            return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while calling Google Geocoding API: {e}")
        return None
    except Exception as e:
        logger.error(f"Error calling Google Geocoding API: {e}")
        return None

async def geocode_nominatim(address_str: str) -> Optional[GeocodeResponse]:
    """Geocodes an address string using Nominatim (backup)."""
    # Important: Nominatim has a strict usage policy (max 1 req/sec, no bulk).
    # https://operations.osmfoundation.org/policies/nominatim/
    headers = {"User-Agent": "PropertyLeadEnrichmentApp/1.0 (your-email@example.com)"} # Be sure to set a proper User-Agent
    params = {"q": address_str, "format": "json", "limit": 1}
    try:
        async with httpx.AsyncClient() as client:
            # Add a small delay if this is used too frequently, though ideally it's a fallback
            # await asyncio.sleep(1) # If making many calls, respect rate limits
            response = await client.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        if data: # Nominatim returns a list
            result = data[0]
            # Nominatim provides display_name which is a form of standardized address
            return GeocodeResponse(
                latitude=float(result["lat"]),
                longitude=float(result["lon"]),
                standardized_address=result.get("display_name")
            )
        else:
            logger.warning(f"Nominatim could not geocode address: {address_str}")
            return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while calling Nominatim API: {e}")
        return None
    except Exception as e:
        logger.error(f"Error calling Nominatim API: {e}")
        return None

async def get_lat_lng(address_input: str, settings: Settings) -> Optional[GeocodeResponse]:
    """
    Main function to get latitude and longitude.
    It standardizes the address and then tries Google Maps API, falling back to Nominatim.
    """
    standardized_address_str, address_components = await standardize_address(address_input)

    if not address_components and not standardized_address_str:
        logger.warning(f"Failed to standardize address: {address_input}")
        # Fallback to trying the original address string if standardization completely fails
        address_to_try_nominatim = address_input
    else:
        # Prefer components for Google if available, else the string form
        address_to_try_nominatim = standardized_address_str if standardized_address_str else address_input


    # Try Google first if components are available (more reliable) or if a key is set
    if address_components and settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "YOUR_GOOGLE_API_KEY_HERE":
        geocode_result = await geocode_google(address_components, settings)
        if geocode_result:
            logger.info(f"Successfully geocoded with Google: {address_input}")
            return geocode_result
        else:
            logger.warning(f"Failed to geocode with Google for components of: {address_input}. Trying Nominatim with string: {address_to_try_nominatim}")
    elif standardized_address_str and settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "YOUR_GOOGLE_API_KEY_HERE":
        # Fallback to Google with the string if components weren't ideal but we have a standardized string
        # This is a simplified version; a real Google integration might solely rely on components
        # or a more carefully constructed address string.
        # For now, let's assume the component-based `geocode_google` is the primary path.
        # If it failed, we'll go to Nominatim.
        pass # Covered by the component check mostly

    # Fallback to Nominatim
    logger.info(f"Attempting geocoding with Nominatim for: {address_to_try_nominatim}")
    geocode_result_nominatim = await geocode_nominatim(address_to_try_nominatim)
    if geocode_result_nominatim:
        logger.info(f"Successfully geocoded with Nominatim: {address_to_try_nominatim}")
        return geocode_result_nominatim

    logger.error(f"Failed to geocode address '{address_input}' with all available providers.")
    return None
