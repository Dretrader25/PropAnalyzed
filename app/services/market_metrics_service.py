import pandas as pd
from typing import Optional
from app.models.market import MarketMetrics
import logging
import os # For path joining

logger = logging.getLogger(__name__)

# Define the path to the CSV file relative to the project root
# This assumes the 'data' directory is at the same level as 'app'
REDFIN_CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'dummy_redfin_market_data.csv')


_market_data_cache: Optional[pd.DataFrame] = None

def load_redfin_data(filepath: str = REDFIN_CSV_PATH) -> Optional[pd.DataFrame]:
    """Loads Redfin market data from a CSV file into a pandas DataFrame."""
    global _market_data_cache
    if _market_data_cache is not None:
        logger.info("Returning cached Redfin market data.")
        return _market_data_cache

    try:
        if not os.path.exists(filepath):
            logger.error(f"Redfin data CSV not found at path: {filepath}")
            # In a real app, you might try to download it here or raise a critical error.
            return None

        df = pd.read_csv(filepath)
        logger.info(f"Successfully loaded Redfin market data from {filepath}. Shape: {df.shape}")
        _market_data_cache = df
        return df
    except FileNotFoundError:
        logger.error(f"Redfin data CSV not found at path: {filepath}")
        return None
    except pd.errors.EmptyDataError:
        logger.error(f"Redfin data CSV is empty at path: {filepath}")
        return None
    except Exception as e:
        logger.error(f"Error loading Redfin data CSV from {filepath}: {e}")
        return None

def get_market_metrics_from_df(
    area_identifier: str, # Can be city name or ZIP code
    df: Optional[pd.DataFrame]
) -> Optional[MarketMetrics]:
    """
    Retrieves market metrics for a given city or ZIP code from the DataFrame.
    The CSV is expected to have 'Region', 'Metric', 'Value' columns.
    'Period' column can be used for more advanced filtering if needed.
    """
    if df is None or df.empty:
        logger.warning("Market data DataFrame is not loaded or is empty.")
        return None

    try:
        # Filter data for the specific region (city or ZIP)
        # Assuming 'Region' column in CSV contains city names or ZIP codes
        region_data = df[df['Region'].astype(str).str.lower() == area_identifier.lower()]

        if region_data.empty:
            logger.info(f"No market data found for area: {area_identifier}")
            return None

        # Assuming the latest period's data is most relevant if multiple periods exist.
        # For simplicity, if there are multiple periods, this will pivot based on the first one it finds.
        # A more robust solution would sort by 'Period' and take the latest.
        # Or, the CSV should be pre-processed to only contain latest data per region.

        # Pivot the table to get metrics as columns for the selected region
        # Taking the first available period's data if multiple exist for the region
        # This is a simplified pivot; error handling for missing metrics is needed.

        metrics = {}
        # Iterate over unique metrics for the region to populate the dictionary
        for _, row in region_data.iterrows():
            metrics[row['Metric']] = row['Value']

        if not metrics:
             logger.info(f"No metrics parsed for area: {area_identifier} from available data.")
             return None

        # Construct the MarketMetrics Pydantic model
        # Convert types as necessary, Pydantic will also validate.
        avg_dom_raw = metrics.get('Average DOM')
        median_price_raw = metrics.get('Median Sale Price')

        avg_dom = None
        if avg_dom_raw is not None:
            try:
                avg_dom = float(avg_dom_raw)
            except ValueError:
                logger.warning(f"Could not convert 'Average DOM' value '{avg_dom_raw}' to float for {area_identifier}")

        median_price = None
        if median_price_raw is not None:
            try:
                median_price = float(median_price_raw)
            except ValueError:
                logger.warning(f"Could not convert 'Median Sale Price' value '{median_price_raw}' to float for {area_identifier}")


        return MarketMetrics(
            source="Redfin CSV", # Or be more specific if possible
            query_area=area_identifier,
            average_dom=avg_dom,
            median_sale_price=median_price,
            price_trends_6m=str(metrics.get('Price Trend (6m)')) if metrics.get('Price Trend (6m)') is not None else None,
            inventory_level=str(metrics.get('Inventory Level')) if metrics.get('Inventory Level') is not None else None
            # Note: The Pydantic model will convert to string if necessary,
            # but explicit str() ensures it's handled if source is not string.
        )
    except Exception as e:
        logger.error(f"Error processing market data for {area_identifier}: {e}")
        return None

# Example function to be called by the main endpoint/orchestrator
async def get_market_metrics(area_identifier: str) -> Optional[MarketMetrics]:
    """Loads data (if not already cached) and retrieves metrics."""
    market_df = load_redfin_data() # Uses default path, loads/caches on first call
    if market_df is None:
        return None # Error already logged by load_redfin_data

    return get_market_metrics_from_df(area_identifier, market_df)
