document.addEventListener('DOMContentLoaded', () => {
    const addressInput = document.getElementById('addressInput');
    const submitButton = document.getElementById('submitAddress');
    const responseArea = document.getElementById('responseArea');

    if (!submitButton) {
        console.error("Submit button not found!");
        return;
    }
    if (!addressInput) {
        console.error("Address input not found!");
        return;
    }
    if (!responseArea) {
        console.error("Response area not found!");
        return;
    }

    submitButton.addEventListener('click', async () => {
        const address = addressInput.value.trim();

        if (!address) {
            responseArea.innerHTML = '<p class="error">Please enter an address.</p>';
            return;
        }

        // Clear previous response and show loading message
        responseArea.innerHTML = '<p class="loading">Loading property information...</p>';

        try {
            // Construct the API URL. Ensure the API is running on the correct port.
            // This assumes the API is served from the same origin (host:port).
            // If your FastAPI app runs on, e.g., port 8000:
            const apiUrl = `/get-property-info?address=${encodeURIComponent(address)}`;

            const response = await fetch(apiUrl);

            if (!response.ok) {
                let errorText = `API Error: ${response.status} - ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorText += `<br><pre>${JSON.stringify(errorData, null, 2)}</pre>`;
                } catch (e) {
                    // Could not parse error response as JSON
                    errorText += `<br>Could not parse error response body.`;
                }
                responseArea.innerHTML = `<p class="error">${errorText}</p>`;
                return;
            }

            const data = await response.json();

            // Display the formatted JSON response
            // Using <pre> for preformatted text which respects whitespace and is good for JSON
            responseArea.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;

        } catch (error) {
            console.error('Fetch error:', error);
            responseArea.innerHTML = `<p class="error">Failed to fetch data. Check the console for details. Is the API server running? Error: ${error.message}</p>`;
        }
    });

    // Optional: Allow pressing Enter in the input field to submit
    addressInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent default form submission if it were in a form
            submitButton.click();
        }
    });
});
