import pytest
from app.utils.exceptions import ServiceUnavailableError, APIDataError, AddressNotFoundError

def test_service_unavailable_error():
    err = ServiceUnavailableError(service_name="TestService")
    assert err.service_name == "TestService"
    assert str(err) == "TestService is unavailable or failed."

    err_with_msg = ServiceUnavailableError(service_name="AnotherService", message="Custom downtime message")
    assert err_with_msg.service_name == "AnotherService"
    assert str(err_with_msg) == "Custom downtime message"

def test_api_data_error():
    err = APIDataError(service_name="TestAPI")
    assert err.service_name == "TestAPI"
    assert str(err) == "Error processing data from TestAPI."

    err_with_msg = APIDataError(service_name="AnotherAPI", message="Invalid data format")
    assert err_with_msg.service_name == "AnotherAPI"
    assert str(err_with_msg) == "Invalid data format"

def test_address_not_found_error():
    err = AddressNotFoundError(address="123 Main St", service_name="GeoService")
    assert err.address == "123 Main St"
    assert err.service_name == "GeoService"
    assert str(err) == "Address '123 Main St' not found or invalid for GeoService."

    err_with_msg = AddressNotFoundError(address="Unknown Rd", service_name="MapService", message="Specific not found reason")
    assert err_with_msg.address == "Unknown Rd"
    assert err_with_msg.service_name == "MapService"
    assert str(err_with_msg) == "Specific not found reason"
