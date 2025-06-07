class ServiceUnavailableError(Exception):
    """Custom exception for when an external service is unavailable."""
    def __init__(self, service_name: str, message: str = ""):
        self.service_name = service_name
        self.message = message or f"{service_name} is unavailable or failed."
        super().__init__(self.message)

class APIDataError(Exception):
    """Custom exception for errors related to external API data (e.g., unexpected format)."""
    def __init__(self, service_name: str, message: str = ""):
        self.service_name = service_name
        self.message = message or f"Error processing data from {service_name}."
        super().__init__(self.message)

class AddressNotFoundError(Exception):
    """Custom exception for when an address cannot be processed or found by a service."""
    def __init__(self, address: str, service_name: str, message: str = ""):
        self.address = address
        self.service_name = service_name
        self.message = message or f"Address '{address}' not found or invalid for {service_name}."
        super().__init__(self.message)
