# Property Lead Enrichment API

This FastAPI application provides an API endpoint to enrich property information based on a given address. It aggregates data from various sources, including geocoding services, property details providers, listing status APIs, comparable sales data, and market metrics.

## Features

*   **Geocoding**: Converts address to latitude/longitude (Google Maps API, Nominatim fallback).
*   **Property Details**: Fetches detailed property attributes (Estated API primary).
*   **Listing Status**: Retrieves current listing status (RentCast API primary).
*   **Comparable Sales**: Finds recent comparable property sales (RentCast API primary).
*   **Market Metrics**: Provides local market statistics (from CSV data, e.g., Redfin).
*   **Unified JSON Response**: All information is aggregated into a single, structured JSON response.

## Setup and Configuration

### 1. API Keys (Environment Variables / Replit Secrets)

This application requires API keys for several external services. These should be set as environment variables. If using [Replit](https://replit.com/), store these in the "Secrets" tab.

*   `ESTATED_API_KEY`: Your API key for Estated (for property details).
*   `GOOGLE_API_KEY`: Your API key for Google Geocoding API.
*   `RENTCAST_API_KEY`: Your API key for RentCast (for listing status, comps, etc.).
*   `ZWSID`: (Optional) Your Zillow Web Service ID, if you intend to implement and use Zillow fallbacks.

**Example for Replit Secrets:**
Go to the "Secrets" tab in your Replit workspace and add new secrets with the keys above and their corresponding values.

For local development (not on Replit), you can create a `.env` file in the project root and `pydantic-settings` will load it (ensure `.env` is in your `.gitignore`):
```env
ESTATED_API_KEY="your_estated_key"
GOOGLE_API_KEY="your_google_key"
RENTCAST_API_KEY="your_rentcast_key"
ZWSID="your_zwsid"
```

### 2. Dependencies

The necessary Python packages are listed in `requirements.txt`. Install them using pip:

```bash
pip install -r requirements.txt
```

### 3. Market Data CSV (Optional - for Market Metrics)

The market metrics service currently reads data from `data/dummy_redfin_market_data.csv`.
To use your own data:
1.  Place your CSV file (e.g., `redfin_data.csv`) in the `data/` directory.
2.  Update the `REDFIN_CSV_PATH` variable in `app/services/market_metrics_service.py` to point to your file.
Ensure your CSV has at least 'Region', 'Metric', and 'Value' columns, where 'Region' can be a city or ZIP code.

## Running the Application

You can run the application using Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*   `--reload`: Enables auto-reloading when code changes (for development).
*   `--host 0.0.0.0`: Makes the server accessible externally (e.g., within Replit's environment).
*   `--port 8000`: Specifies the port. Replit often uses port 8080 by default for its web output. Adjust if needed.

If on Replit, the default run command might already be configured, or you can set it in the `.replit` file.

## API Usage

Once the application is running, you can access the API documentation (powered by Swagger UI) at:

`http://localhost:8000/docs` (or your Replit URL + `/docs`)

### Example Request

Send a GET request to the `/get-property-info` endpoint:

`http://localhost:8000/get-property-info?address=123%20Main%20St,%20Anytown,%20CA%2090210`

Replace the address with the one you want to query.

## HTML Frontend

A simple HTML frontend is available for interacting with the API directly from your browser. This is useful for quick tests and demonstrations.

**Accessing the Frontend:**

1.  Ensure the FastAPI application is running (see "Running the Application" section).
2.  Open your web browser and navigate to: `http://localhost:8000/ui` (replace `localhost:8000` with your actual host and port if different).

**Using the Frontend:**

1.  Enter a property address into the input field.
2.  Click the "Get Property Info" button.
3.  The API response (or any errors) will be displayed in a formatted JSON view on the page.

## Project Structure

*   `app/`: Main application module.
    *   `main.py`: FastAPI application instance and main endpoint.
    *   `config/`: Configuration settings (API keys via `pydantic-settings`).
    *   `models/`: Pydantic models for data validation and structuring.
    *   `services/`: Business logic for interacting with external APIs and data sources.
    *   `utils/`: Utility functions (logging, retries, custom exceptions).
*   `data/`: Directory for data files (e.g., market metrics CSV).
*   `requirements.txt`: Python dependencies.
*   `README.md`: This file.

## Important Notes on API Simulations

Currently, the calls to external APIs (Estated, Google Geocoding, Nominatim, RentCast) within the respective service files are **simulated**. This means they return pre-defined dummy data for specific addresses (like "123 Main St, Anytown, CA 90210") and do not make actual external HTTP requests.

To make the application fully functional, you will need to:
1.  Replace the simulated logic with actual `httpx.AsyncClient` calls to the live API endpoints.
2.  Ensure your API keys are correctly configured in the environment (Replit Secrets or `.env` file).
3.  Thoroughly test the integration with each live API, including error handling and response parsing, based on their official documentation.
