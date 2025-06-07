import pytest
import asyncio
import logging
from unittest.mock import Mock, patch # Mock is part of unittest but commonly used with pytest

from app.utils.retry_utils import retry_async_function

# Configure basic logging for test output visibility if needed
# logging.basicConfig(level=logging.INFO)

class CustomTestException(Exception):
    pass

class AnotherCustomTestException(Exception):
    pass

@pytest.mark.asyncio
async def test_retry_success_on_first_attempt():
    mock_successful_func = Mock(return_value=asyncio.Future())
    mock_successful_func.return_value.set_result("success")

    @retry_async_function(retries=3, delay_seconds=0.1)
    async def func_to_test():
        return await mock_successful_func()

    result = await func_to_test()
    assert result == "success"
    mock_successful_func.assert_called_once()

@pytest.mark.asyncio
async def test_retry_fails_then_succeeds():
    mock_func = Mock()
    # Simulate failure on first call, then success
    mock_func.side_effect = [CustomTestException("Failed attempt"), asyncio.Future()]
    # The future must be set for the successful call
    # We can't set it directly in side_effect list if it's created there, so we do it this way:
    successful_future = asyncio.Future()
    successful_future.set_result("success after retry")
    mock_func.side_effect = [CustomTestException("Failed attempt"), successful_future]


    @retry_async_function(retries=3, delay_seconds=0.01, exceptions=(CustomTestException,))
    async def func_to_test():
        return await mock_func()

    result = await func_to_test()
    assert result == "success after retry"
    assert mock_func.call_count == 2

@pytest.mark.asyncio
async def test_retry_exhausts_retries_and_fails():
    mock_failing_func = Mock(side_effect=CustomTestException("Persistent failure"))

    @retry_async_function(retries=2, delay_seconds=0.01, exceptions=(CustomTestException,))
    async def func_to_test():
        return await mock_failing_func()

    with pytest.raises(CustomTestException) as excinfo:
        await func_to_test()

    assert "Persistent failure" in str(excinfo.value)
    assert mock_failing_func.call_count == 3 # Initial call + 2 retries

@pytest.mark.asyncio
async def test_retry_only_on_specified_exceptions():
    mock_func = Mock()
    # First, raise an exception that should be retried
    # Then, raise an exception that should NOT be retried
    mock_func.side_effect = [CustomTestException("Retry this"), AnotherCustomTestException("Do not retry this")]

    @retry_async_function(retries=3, delay_seconds=0.01, exceptions=(CustomTestException,))
    async def func_to_test():
        return await mock_func()

    with pytest.raises(AnotherCustomTestException) as excinfo:
        await func_to_test()

    assert "Do not retry this" in str(excinfo.value)
    # Called once for CustomTestException (failed, will retry), then once for AnotherCustomTestException (failed, will not retry)
    # The retry for CustomTestException would have happened, but the next call immediately raises the non-retryable one.
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_retry_no_retries_on_success():
    mock_successful_func = Mock(return_value=asyncio.Future())
    mock_successful_func.return_value.set_result("immediate success")

    @retry_async_function(retries=0, delay_seconds=0.01) # Retries set to 0
    async def func_to_test():
        return await mock_successful_func()

    result = await func_to_test()
    assert result == "immediate success"
    mock_successful_func.assert_called_once()

@pytest.mark.asyncio
async def test_retry_fails_with_zero_retries():
    mock_failing_func = Mock(side_effect=CustomTestException("Failure"))

    @retry_async_function(retries=0, delay_seconds=0.01, exceptions=(CustomTestException,))
    async def func_to_test():
        return await mock_failing_func()

    with pytest.raises(CustomTestException):
        await func_to_test()
    mock_failing_func.assert_called_once() # Only the initial attempt
