import pytest
import logging
from app.utils.logging_utils import setup_logging
import io
import sys

def test_setup_logging_writes_to_stdout():
    # Redirect stdout to capture log output
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()

    try:
        # Configure logging to DEBUG and it should use our new stdout
        setup_logging(level=logging.DEBUG)
        assert logging.getLogger().getEffectiveLevel() == logging.DEBUG

        # Log a message using a child logger
        test_logger = logging.getLogger("stdout_test_logger")
        test_logger.setLevel(logging.DEBUG) # Ensure child logger also passes DEBUG messages

        test_logger.info("Info message for stdout test.")
        test_logger.debug("Debug message for stdout test.")

        # Get the captured output
        log_content = captured_output.getvalue()

        # Check if the messages are in the captured output
        # We also implicitly check the formatter this way
        assert "stdout_test_logger - INFO - Info message for stdout test." in log_content
        assert "stdout_test_logger - DEBUG - Debug message for stdout test." in log_content

        # Check that the initial configuration message is also there
        assert "app.utils.logging_utils - INFO - Logging configured with level DEBUG." in log_content

    finally:
        # Restore stdout
        sys.stdout = old_stdout

    # Optionally, reset logging for other tests if needed,
    # though pytest usually isolates tests.
    # setup_logging(level=logging.INFO)
