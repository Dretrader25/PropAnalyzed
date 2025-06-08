document.addEventListener('DOMContentLoaded', () => {
    const addressInput = document.getElementById('addressInput');
    const submitButton = document.getElementById('submitAddress');
    const responseArea = document.getElementById('responseArea'); // For raw JSON
    const loadingMessageDiv = document.getElementById('loadingMessage');
    const errorMessageDiv = document.getElementById('errorMessage');

    // --- Element Sanity Checks ---
    if (!addressInput) { console.error("Address input (#addressInput) not found!"); return; }
    if (!submitButton) { console.error("Submit button (#submitAddress) not found!"); return; }
    if (!responseArea) { console.error("Response area (#responseArea) for raw JSON not found!"); return; }
    if (!loadingMessageDiv) { console.error("Loading message div (#loadingMessage) not found!"); return; }
    if (!errorMessageDiv) { console.error("Error message div (#errorMessage) not found!"); return; }

    // --- Helper function to update text content safely ---
    function setText(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text !== null && text !== undefined && text !== '' ? text : 'N/A';
        } else {
            // console.warn(`Element with ID ${elementId} not found during setText.`); // Can be noisy
        }
    }

    // --- Function to clear all dashboard sections ---
    function clearDashboardSections() {
        // Property Overview
        setText('prop-address', 'N/A');
        setText('prop-type', 'N/A');
        setText('prop-beds', 'N/A');
        setText('prop-baths', 'N/A');
        setText('prop-sqft', 'N/A');
        setText('prop-lot-size', 'N/A');
        setText('prop-year-built', 'N/A');

        // Listing & Market Info fields (NEW)
        setText('listing-status', 'N/A');
        setText('listing-price', 'N/A');
        setText('listing-dom', 'N/A');
        setText('market-avg-dom', 'N/A');
        setText('market-median-price', 'N/A');
        setText('market-price-trend', 'N/A');
        setText('market-inventory-level', 'N/A');

        // Clear Comps Section (NEW)
        const compsTableContainer = document.getElementById('compsTableContainer');
        if (compsTableContainer) {
            compsTableContainer.innerHTML = '<p>No comparable sales data loaded yet.</p>';
        }
        setText('comps-avg-price-per-sqft', 'N/A');

        // Clear Wholesale Calculator fields (NEW)
        const arvInput = document.getElementById('calc-arv');
        if (arvInput) arvInput.value = '';
        const rehabInput = document.getElementById('calc-rehab');
        if (rehabInput) rehabInput.value = '';
        // const maoPercentageInput = document.getElementById('calc-mao-percentage'); // Keep default
        // if (maoPercentageInput) maoPercentageInput.value = '70';
        const feeInput = document.getElementById('calc-wholesale-fee');
        if (feeInput) feeInput.value = '';

        setText('calc-suggested-arv', 'N/A');
        setText('calc-mao', 'N/A');
        setText('calc-buyer-price', 'N/A');

        // Full API Response Area
        if (responseArea) { responseArea.textContent = ''; }

        // TODO: Clear other sections as they are implemented
    }

    // --- Wholesale Calculator Logic --- (NEW)
    const calcInputs = [
        document.getElementById('calc-arv'),
        document.getElementById('calc-rehab'),
        document.getElementById('calc-mao-percentage'),
        document.getElementById('calc-wholesale-fee')
    ];

    function calculateWholesaleMetrics() {
        const arv = parseFloat(document.getElementById('calc-arv').value) || 0;
        const rehab = parseFloat(document.getElementById('calc-rehab').value) || 0;
        const maoPercentage = (parseFloat(document.getElementById('calc-mao-percentage').value) || 0) / 100;
        const wholesaleFee = parseFloat(document.getElementById('calc-wholesale-fee').value) || 0;

        let mao = 0;
        let buyerPrice = 0;

        if (arv > 0 && maoPercentage > 0) {
            // Buyer's Price (Offer to End Buyer from investor perspective) = (ARV * MAO %) - Rehab.
            buyerPrice = (arv * maoPercentage) - rehab;
            // Wholesaler's MAO to seller = Buyer's Price - Wholesale Fee
            mao = buyerPrice - wholesaleFee;
        }

        // Display N/A or 0.00 if calculated value is not positive, but allow 0 if ARV was entered.
        setText('calc-mao', (arv > 0 && maoPercentage > 0) ? mao.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A');
        setText('calc-buyer-price', (arv > 0 && maoPercentage > 0) ? buyerPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A');
    }

    calcInputs.forEach(input => {
        if (input) {
            input.addEventListener('input', calculateWholesaleMetrics);
        }
    });
    // --- End of Wholesale Calculator Logic ---

    // --- Event Listener for Submit Button ---
    submitButton.addEventListener('click', async () => {
        const address = addressInput.value.trim();
        // const loadingMessageDiv = document.getElementById('loadingMessage'); // Already defined globally
        // const errorMessageDiv = document.getElementById('errorMessage'); // Already defined globally
        const fullApiResponseArea = document.getElementById('responseArea'); // For debug JSON

        if (!address) {
            errorMessageDiv.textContent = 'Please enter an address.';
            errorMessageDiv.style.display = 'block';
            loadingMessageDiv.style.display = 'none';
            clearDashboardSections(); // Clear out old data
            if (fullApiResponseArea) { fullApiResponseArea.textContent = ''; } // Clear debug area too
            return;
        }

        // Clear previous error/results and show loading message
        errorMessageDiv.style.display = 'none';
        errorMessageDiv.textContent = ''; // Clear previous text content
        errorMessageDiv.innerHTML = ''; // Clear previous HTML content
        if (fullApiResponseArea) { fullApiResponseArea.textContent = ''; } // Clear debug area too
        loadingMessageDiv.style.display = 'block';
        clearDashboardSections();

        try {
            const apiUrl = `/get-property-info?address=${encodeURIComponent(address)}`;
            const response = await fetch(apiUrl);

            loadingMessageDiv.style.display = 'none'; // Hide loading once response (or error) is received

            if (!response.ok) {
                let userErrorMsg = `API Error: ${response.status} - ${response.statusText}.`;
                let errorDetailForDebug = `Status: ${response.status}, StatusText: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    // Put detailed JSON error in the debug area
                    if (fullApiResponseArea) {
                        fullApiResponseArea.textContent = JSON.stringify(errorData, null, 2);
                    }
                    // Add a note to the user message if there's more detail
                    // userErrorMsg += " See 'Full API Response (Debug)' section for details if available.";
                    // Optionally, extract a specific message from errorData if a known format exists
                    if (errorData && typeof errorData.detail === 'string') { // FastAPI typical error string
                        userErrorMsg = `API Error: ${errorData.detail}`;
                    } else if (errorData && typeof errorData.detail === 'object') { // FastAPI validation errors
                        userErrorMsg = `API Validation Error. See debug section for details.`;
                        // Could attempt to format errorData.detail here if it's a list of loc/msg
                    } else if (errorData && typeof errorData.message === 'string') { // Other error structures
                         userErrorMsg = `API Error: ${errorData.message}`;
                    } else {
                        userErrorMsg += " See 'Full API Response (Debug)' section for details.";
                    }

                } catch (e) {
                    // Could not parse error response as JSON
                    errorDetailForDebug += "\nCould not parse error response body.";
                    if (fullApiResponseArea) {
                        fullApiResponseArea.textContent = errorDetailForDebug;
                    }
                     userErrorMsg += " Error response was not valid JSON.";
                }
                errorMessageDiv.textContent = userErrorMsg; // Set user-friendly error
                errorMessageDiv.style.display = 'block';
                return; // Stop further processing
            }

            const data = await response.json();

            // Populate Full API Response (Debug)
            if (fullApiResponseArea) {
                fullApiResponseArea.textContent = JSON.stringify(data, null, 2);
            }

            // --- Populate Property Overview Section ---
            const geocodeData = data.geocode;
            const detailsData = data.details;

            let displayAddress = 'N/A';
            if (geocodeData && geocodeData.standardized_address) {
                displayAddress = geocodeData.standardized_address;
            } else if (data.input_address && data.input_address.address) {
                displayAddress = data.input_address.address;
            } else {
                displayAddress = address; // Fallback to user's raw input if all else fails
            }
            setText('prop-address', displayAddress);

            if (detailsData) {
                setText('prop-type', detailsData.property_type);
                setText('prop-beds', detailsData.beds);
                setText('prop-baths', detailsData.baths);
                setText('prop-sqft', detailsData.square_footage ? detailsData.square_footage.toLocaleString() : 'N/A');
                setText('prop-lot-size', detailsData.lot_size_sqft ? detailsData.lot_size_sqft.toLocaleString() : 'N/A');
                setText('prop-year-built', detailsData.year_built);
            } else {
                // Fields already reset by clearDashboardSections, but good for explicitness if not clearing all.
                setText('prop-type', 'N/A');
                setText('prop-beds', 'N/A');
                setText('prop-baths', 'N/A');
                setText('prop-sqft', 'N/A');
                setText('prop-lot-size', 'N/A');
                setText('prop-year-built', 'N/A');
            }
            // --- End of Property Overview Population ---

        // --- Populate Listing & Market Info Section --- (NEW)
        const listingInfoData = data.listing_info;
        const marketMetricsData = data.market_metrics;

        if (listingInfoData) {
            setText('listing-status', listingInfoData.status);
            setText('listing-price', listingInfoData.list_price ? listingInfoData.list_price.toLocaleString() : 'N/A');
            setText('listing-dom', listingInfoData.days_on_market);
        } else {
            setText('listing-status', 'N/A');
            setText('listing-price', 'N/A');
            setText('listing-dom', 'N/A');
        }

        if (marketMetricsData) {
            setText('market-avg-dom', marketMetricsData.average_dom ? marketMetricsData.average_dom.toLocaleString(undefined, { maximumFractionDigits: 0 }) : 'N/A');
            setText('market-median-price', marketMetricsData.median_sale_price ? marketMetricsData.median_sale_price.toLocaleString() : 'N/A');
            setText('market-price-trend', marketMetricsData.price_trends_6m);
            setText('market-inventory-level', marketMetricsData.inventory_level);
        } else {
            setText('market-avg-dom', 'N/A');
            setText('market-median-price', 'N/A');
            setText('market-price-trend', 'N/A');
            setText('market-inventory-level', 'N/A');
        }
        // --- End of Listing & Market Info population ---

        // --- Populate Comparable Sales Analysis Section --- (NEW)
        const compsData = data.comparable_sales;
        const compsTableContainer = document.getElementById('compsTableContainer');
        let totalValidPricePerSqFt = 0;
        let validCompsForAvg = 0;

        if (compsTableContainer) {
            if (compsData && compsData.length > 0) {
                let tableHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Address</th>
                                <th>Sale Date</th>
                                <th>Sale Price</th>
                                <th>SqFt</th>
                                <th>Price/SqFt</th>
                                <th>Distance (mi)</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                compsData.forEach(comp => {
                    const salePrice = comp.sale_price ? parseFloat(comp.sale_price) : 0;
                    const sqft = comp.square_footage ? parseInt(comp.square_footage) : 0;
                    let pricePerSqFt = 0;
                    if (salePrice > 0 && sqft > 0) {
                        pricePerSqFt = salePrice / sqft;
                        totalValidPricePerSqFt += pricePerSqFt;
                        validCompsForAvg++;
                    }

                    tableHTML += `
                        <tr>
                            <td>${comp.address || 'N/A'}</td>
                            <td>${comp.sale_date || 'N/A'}</td>
                            <td>$${salePrice > 0 ? salePrice.toLocaleString() : 'N/A'}</td>
                            <td>${sqft > 0 ? sqft.toLocaleString() : 'N/A'}</td>
                            <td>$${pricePerSqFt > 0 ? pricePerSqFt.toFixed(2) : 'N/A'}</td>
                            <td>${comp.distance_miles !== null ? comp.distance_miles.toFixed(2) : 'N/A'}</td>
                        </tr>
                    `;
                });
                tableHTML += `</tbody></table>`;
                compsTableContainer.innerHTML = tableHTML;
            } else {
                compsTableContainer.innerHTML = '<p>No comparable sales data found.</p>';
            }
        }

        if (validCompsForAvg > 0) {
            const avgPricePerSqFt = totalValidPricePerSqFt / validCompsForAvg;
            setText('comps-avg-price-per-sqft', avgPricePerSqFt.toFixed(2));
        } else {
            setText('comps-avg-price-per-sqft', 'N/A');
        }
        // --- End of Comparable Sales Analysis population ---

        // --- Pre-fill Suggested ARV for Calculator --- (NEW)
        const propSqftText = document.getElementById('prop-sqft') ? document.getElementById('prop-sqft').textContent : null;
        const avgPricePerSqFtText = document.getElementById('comps-avg-price-per-sqft') ? document.getElementById('comps-avg-price-per-sqft').textContent : null;

        if (propSqftText && propSqftText !== 'N/A' && avgPricePerSqFtText && avgPricePerSqFtText !== 'N/A') {
            const propSqft = parseFloat(propSqftText.replace(/,/g, '')); // Remove commas for parsing
            const avgPricePerSqFt = parseFloat(avgPricePerSqFtText.replace(/,/g, '')); // Remove commas for parsing
            if (propSqft > 0 && avgPricePerSqFt > 0) {
                const suggestedArv = propSqft * avgPricePerSqFt;
                setText('calc-suggested-arv', suggestedArv.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }));

                // Optionally, prefill the ARV input field as well
                // const arvInputField = document.getElementById('calc-arv');
                // if (arvInputField) arvInputField.value = suggestedArv.toFixed(0);
            } else {
                setText('calc-suggested-arv', 'N/A');
            }
        } else {
            setText('calc-suggested-arv', 'N/A');
        }
        // Initialize calculator on load / new data (in case default values should produce a calculation or clear previous)
        calculateWholesaleMetrics();
        // --- End of Pre-fill Suggested ARV ---

        // Check for errors reported by the API in the 'errors' field of the response
        if (data.errors && data.errors.length > 0) {
            const apiErrorsMessage = "Encountered issues during data retrieval: \n- " + data.errors.join("\n- ");
            // Append these to existing error messages or show separately
            // For now, let's make them prominent if other parts succeeded.
            // If errorMessageDiv is already visible due to a major fetch error, this might be redundant or confusing.
            // So, only show these if no major fetch error occurred.
            if (errorMessageDiv.style.display === 'none') {
                 errorMessageDiv.textContent = apiErrorsMessage;
                 errorMessageDiv.style.display = 'block';
            } else {
                 // Append to existing critical error message if needed, or log to console
                 console.warn("API returned data but also includes errors:", data.errors);
                 errorMessageDiv.textContent += "\n\nAdditionally, the API reported the following issues: \n- " + data.errors.join("\n- ");
            }
        }


    } catch (error) {
        console.error('Fetch error:', error);
        loadingMessageDiv.style.display = 'none';
        errorMessageDiv.textContent = `Failed to fetch data. Check the console for details. Is the API server running? Error: ${error.message}`;
        errorMessageDiv.style.display = 'block';
        // responseArea.textContent = ''; // Already cleared at the start of try or by error handler
    }
    });

    // Optional: Allow pressing Enter in the input field to submit
    addressInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            submitButton.click();
        }
    });
});
