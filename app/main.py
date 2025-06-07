from fastapi import FastAPI, HTTPException, Depends, Query
from typing import Optional, List
import logging
import httpx # Added for retry decorator

from .config.settings import Settings, get_settings
from .utils.logging_utils import setup_logging
from .utils.retry_utils import retry_async_function
from .utils.exceptions import ServiceUnavailableError, APIDataError, AddressNotFoundError

# Import models
from .models import (
    AddressInput,
    GeocodeResponse,
    PropertyDetails,
    ListingStatus,
    ComparableSale,
    MarketMetrics,
    UnifiedPropertyResponse
)

# Import service functions
from .services import (
    get_lat_lng,
    fetch_property_details_estated,
    fetch_property_details_zillow, # Fallback
    fetch_listing_status_rentcast,
    fetch_listing_status_zillow, # Fallback
    fetch_comps_rentcast,
    fetch_comps_zillow, # Fallback
    get_market_metrics,
    load_redfin_data # For pre-loading if desired, not directly used in endpoint
)

# Initialize logging
setup_logging() # Ensure this is called once
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Property Lead Enrichment API",
    description="Provides enriched information for a given property address.",
    version="0.1.0"
)

# --- Retryable service calls ---
# Decorate the service functions that make external calls
# Note: If a service function itself has multiple internal retries or complex logic,
#       you might only wrap the top-level call or specific sub-calls.
#       For now, we wrap the main fetching functions.

@retry_async_function(retries=2, delay_seconds=0.5, exceptions=(ServiceUnavailableError, httpx.TimeoutException, httpx.NetworkError))
async def get_lat_lng_retryable(address_input: str, settings: Settings) -> Optional[GeocodeResponse]:
    # Note: get_lat_lng already has internal fallbacks (Google -> Nominatim)
    # The retry here would be for transient network issues for the whole operation.
    # We might also want to raise ServiceUnavailableError from within get_lat_lng if both fail.
    logger.debug(f"Calling get_lat_lng for: {address_input}")
    result = await get_lat_lng(address_input, settings)
    if result is None:
        # Optional: Raise a specific error if needed here, or let it return None
        logger.warning(f"Geocoding returned None for {address_input} after retries.")
        # raise AddressNotFoundError(address=address_input, service_name="Geocoding Service")
    return result

@retry_async_function(retries=2, delay_seconds=0.5, exceptions=(ServiceUnavailableError, httpx.TimeoutException, httpx.NetworkError))
async def fetch_property_details_estated_retryable(std_address: str, settings: Settings) -> Optional[PropertyDetails]:
    logger.debug(f"Calling fetch_property_details_estated for: {std_address}")
    # In a real scenario, ensure this function can raise ServiceUnavailableError or APIDataError
    return await fetch_property_details_estated(std_address, settings)

@retry_async_function(retries=1, delay_seconds=0.5, exceptions=(ServiceUnavailableError, httpx.TimeoutException, httpx.NetworkError)) # Fewer retries for fallbacks
async def fetch_property_details_zillow_retryable(std_address: str, settings: Settings) -> Optional[PropertyDetails]:
    logger.debug(f"Calling fetch_property_details_zillow (fallback) for: {std_address}")
    return await fetch_property_details_zillow(std_address, settings)

@retry_async_function(retries=2, delay_seconds=0.5, exceptions=(ServiceUnavailableError, httpx.TimeoutException, httpx.NetworkError))
async def fetch_listing_status_rentcast_retryable(address: str, settings: Settings) -> Optional[ListingStatus]:
    logger.debug(f"Calling fetch_listing_status_rentcast for: {address}")
    return await fetch_listing_status_rentcast(address, settings)

@retry_async_function(retries=1, delay_seconds=0.5, exceptions=(ServiceUnavailableError, httpx.TimeoutException, httpx.NetworkError))
async def fetch_listing_status_zillow_retryable(std_address: str, settings: Settings) -> Optional[ListingStatus]:
    logger.debug(f"Calling fetch_listing_status_zillow (fallback) for: {std_address}")
    return await fetch_listing_status_zillow(std_address, settings)

@retry_async_function(retries=2, delay_seconds=0.5, exceptions=(ServiceUnavailableError, httpx.TimeoutException, httpx.NetworkError))
async def fetch_comps_rentcast_retryable(address: str, settings: Settings) -> Optional[List[ComparableSale]]:
    logger.debug(f"Calling fetch_comps_rentcast for: {address}")
    return await fetch_comps_rentcast(address, settings)

@retry_async_function(retries=1, delay_seconds=0.5, exceptions=(ServiceUnavailableError, httpx.TimeoutException, httpx.NetworkError))
async def fetch_comps_zillow_retryable(std_address: str, settings: Settings) -> Optional[List[ComparableSale]]:
    logger.debug(f"Calling fetch_comps_zillow (fallback) for: {std_address}")
    return await fetch_comps_zillow(std_address, settings)

# Market metrics is local, so direct call is fine, no retry needed unless it involves I/O that can fail.
# async def get_market_metrics_retryable(area: str) -> Optional[MarketMetrics]:
#    return await get_market_metrics(area)


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: Initializing settings and loading data...")
    get_settings() # Initialize settings early
    load_redfin_data() # Pre-load Redfin data into cache
    logger.info("Redfin data loaded into cache if available.")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Application is running."}

# Removed the /show-settings-test endpoint for cleaner main file.
# It can be re-added for debugging if needed.

@app.get("/", summary="Root", include_in_schema=False)
async def root():
    return {"message": "Welcome to the Property Lead Enrichment API. See /docs for API documentation."}


@app.get("/get-property-info", response_model=UnifiedPropertyResponse, summary="Get Enriched Property Information")
async def get_property_information(
    address: str = Query(..., description="The full street address to look up (e.g., '123 Main St, Anytown, CA 90210').", example="123 Main St, Anytown, CA 90210"),
    settings: Settings = Depends(get_settings)
):
    """
    Provides comprehensive information about a property based on its address.
    This includes geocoding, property details, listing status, comparable sales, and market metrics.
    """
    logger.info(f"Received request for address: {address}")

    input_address_model = AddressInput(address=address)
    errors_list: List[str] = []

    # 1. Geocoding
    geocode_data: Optional[GeocodeResponse] = None
    standardized_address_for_api_calls: str = address # Default to original if geocoding fails to standardize
    city_for_market_metrics: Optional[str] = None
    zip_for_market_metrics: Optional[str] = None

    try:
        geocode_data = await get_lat_lng_retryable(address, settings)
        if geocode_data and geocode_data.standardized_address:
            standardized_address_for_api_calls = geocode_data.standardized_address
            logger.info(f"Standardized address: {standardized_address_for_api_calls}")
            # Attempt to parse city/zip from standardized address for market metrics
            # This is a simplistic parsing. `usaddress` components from geocode_service would be better
            parts = standardized_address_for_api_calls.split(',')
            if len(parts) >= 2: # City, State ZIP or City, State
                city_candidate = parts[-2].strip()
                # Further split state and zip if present
                state_zip_parts = parts[-1].strip().split(' ')
                if len(state_zip_parts) > 1 and state_zip_parts[-1].isdigit():
                    zip_for_market_metrics = state_zip_parts[-1]
                    # Potentially take city_candidate if it's not the state
                    if not any(char.isdigit() for char in city_candidate) and len(city_candidate) > 2 : # basic check
                         city_for_market_metrics = city_candidate
                elif len(state_zip_parts) == 1 and not any(char.isdigit() for char in state_zip_parts[0]) and len(state_zip_parts[0]) > 2: # Only state
                     city_for_market_metrics = city_candidate

        elif geocode_data: # Geocoded but no specific standardized address string returned apart from lat/lng
            logger.info(f"Geocoded to Lat: {geocode_data.latitude}, Lng: {geocode_data.longitude}. Using original address for APIs.")
        else:
            errors_list.append("Geocoding failed or returned no data.")
            logger.warning(f"Geocoding completely failed for address: {address}")
            # Decide if we should proceed or raise HTTP error. For now, proceed and report error.
    except AddressNotFoundError as e:
        logger.warning(f"AddressNotFoundError during geocoding: {e}")
        errors_list.append(f"Geocoding error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during geocoding for {address}: {e}", exc_info=True)
        errors_list.append(f"An unexpected error occurred during geocoding: {str(e)}")

    # Use standardized address for subsequent calls if available
    address_for_services = standardized_address_for_api_calls

    # 2. Property Details
    property_details_data: Optional[PropertyDetails] = None
    try:
        property_details_data = await fetch_property_details_estated_retryable(address_for_services, settings)
        if not property_details_data:
            logger.info(f"Estated details not found for {address_for_services}, trying Zillow fallback.")
            errors_list.append("Primary property details source (Estated) returned no data. Attempting fallback.")
            # property_details_data = await fetch_property_details_zillow_retryable(address_for_services, settings) # This is a placeholder
            # if not property_details_data:
            #     errors_list.append("Fallback property details source (Zillow) also returned no data.")
    except Exception as e:
        logger.error(f"Error fetching property details for {address_for_services}: {e}", exc_info=True)
        errors_list.append(f"Error fetching property details: {str(e)}")


    # 3. Listing Status
    listing_status_data: Optional[ListingStatus] = None
    try:
        listing_status_data = await fetch_listing_status_rentcast_retryable(address_for_services, settings)
        # No Zillow fallback for listing status as it's deprecated and likely non-functional.
        if not listing_status_data:
             errors_list.append("Listing status source (RentCast) returned no data.")
    except Exception as e:
        logger.error(f"Error fetching listing status for {address_for_services}: {e}", exc_info=True)
        errors_list.append(f"Error fetching listing status: {str(e)}")


    # 4. Comparable Sales
    comparable_sales_data: Optional[List[ComparableSale]] = None
    try:
        comparable_sales_data = await fetch_comps_rentcast_retryable(address_for_services, settings)
        # No Zillow fallback for comps for now due to ZPID requirement.
        if comparable_sales_data is None: # Explicitly check for None vs empty list
             errors_list.append("Comparable sales source (RentCast) returned no data or failed.")
        elif not comparable_sales_data: # Empty list
             logger.info(f"No comparable sales found by RentCast for {address_for_services}")
             # errors_list.append("No comparable sales found by RentCast.") # Optional: report empty list as an "error" or note
    except Exception as e:
        logger.error(f"Error fetching comparable sales for {address_for_services}: {e}", exc_info=True)
        errors_list.append(f"Error fetching comparable sales: {str(e)}")


    # 5. Market Metrics
    market_metrics_data: Optional[MarketMetrics] = None
    # Prioritize ZIP code for market metrics if available, then city
    area_for_metrics = zip_for_market_metrics or city_for_market_metrics
    if area_for_metrics:
        try:
            logger.info(f"Fetching market metrics for area: {area_for_metrics}")
            market_metrics_data = await get_market_metrics(area_for_metrics)
            if not market_metrics_data:
                errors_list.append(f"No market metrics found for area: {area_for_metrics}.")
        except Exception as e:
            logger.error(f"Error fetching market metrics for {area_for_metrics}: {e}", exc_info=True)
            errors_list.append(f"Error fetching market metrics: {str(e)}")
    else:
        logger.warning(f"Could not determine city or ZIP from address '{standardized_address_for_api_calls}' for market metrics.")
        errors_list.append("Could not determine city/ZIP for market metrics from the provided address after geocoding.")


    # If critical data is missing (e.g. geocoding completely failed and we have no details)
    # we might want to throw an HTTPException earlier.
    # For now, we compile all data and errors.
    if not geocode_data and not property_details_data and not listing_status_data:
         logger.warning(f"No significant data could be fetched for address: {address}")
         # Consider raising HTTPException here if this is unacceptable
         # raise HTTPException(status_code=404, detail=f"Could not retrieve any information for address: {address}. Errors: {'; '.join(errors_list)}")


    return UnifiedPropertyResponse(
        input_address=input_address_model,
        geocode=geocode_data,
        details=property_details_data,
        listing_info=listing_status_data,
        comparable_sales=comparable_sales_data,
        market_metrics=market_metrics_data,
        errors=errors_list if errors_list else None # Only include errors field if there are errors
    )
