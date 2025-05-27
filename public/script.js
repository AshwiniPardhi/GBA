/**
 * Frontend JavaScript for the Pricing Calculator.
 *
 * This script handles:
 * 1. Dynamic cloud cost estimation based on user inputs.
 * 2. Capturing user input from the HTML form for other cost categories.
 * 3. Sending the input data to the backend API via a POST request.
 * 4. Receiving the calculation results from the backend.
 * 5. Displaying the results in the appropriate HTML elements on the page.
 */

const cloudPricingData = {
    azure: {
        compute_tiers: { basic: 50, general: 150, optimized: 300 }, // Cost per instance per month
        storage_per_gb: 0.2, // Cost per GB per month - Adjusted for more realistic small values
        db_tiers: { basic: 20, standard: 100, premium: 400 } // Cost per DB instance per month
    },
    aws: {
        compute_tiers: { basic: 55, general: 160, optimized: 310 },
        storage_per_gb: 0.22,
        db_tiers: { basic: 25, standard: 110, premium: 420 }
    },
    gcp: {
        compute_tiers: { basic: 45, general: 140, optimized: 290 },
        storage_per_gb: 0.18,
        db_tiers: { basic: 18, standard: 90, premium: 380 }
    }
};

let currentEstimatedCloudCost = 0;

// Function to calculate estimated cloud cost
function calculateEstimatedCloudCost() {
    const selectedProvider = document.querySelector('input[name="cloud_provider_selector"]:checked').value;
    const providerInputs = document.getElementById(`${selectedProvider}_inputs`);
    const pricing = cloudPricingData[selectedProvider];

    if (!providerInputs || !pricing) {
        console.error("Selected provider inputs or pricing data not found:", selectedProvider);
        currentEstimatedCloudCost = 0;
        document.getElementById('estimated_cloud_cost_display').innerText = '$0.00';
        return 0;
    }

    const computeInstances = parseFloat(providerInputs.querySelector(`input[name="${selectedProvider}_compute_instances"]`).value) || 0;
    const computeTier = providerInputs.querySelector(`select[name="${selectedProvider}_compute_tier"]`).value;
    const storageGB = parseFloat(providerInputs.querySelector(`input[name="${selectedProvider}_storage_gb"]`).value) || 0;
    const dbInstances = parseFloat(providerInputs.querySelector(`input[name="${selectedProvider}_db_instances"]`).value) || 0;
    const dbTier = providerInputs.querySelector(`select[name="${selectedProvider}_db_tier"]`).value;

    let cost = 0;
    cost += computeInstances * (pricing.compute_tiers[computeTier] || 0);
    cost += storageGB * (pricing.storage_per_gb || 0);
    cost += dbInstances * (pricing.db_tiers[dbTier] || 0);

    currentEstimatedCloudCost = cost;
    document.getElementById('estimated_cloud_cost_display').innerText = `$${cost.toFixed(2)}`;
    return cost;
}

// Event listeners for cloud provider selection
document.querySelectorAll('input[name="cloud_provider_selector"]').forEach(radio => {
    radio.addEventListener('change', function() {
        document.querySelectorAll('.provider_inputs').forEach(div => div.style.display = 'none');
        const selectedProviderDiv = document.getElementById(`${this.value}_inputs`);
        if (selectedProviderDiv) {
            selectedProviderDiv.style.display = 'block';
        }
        calculateEstimatedCloudCost(); // Recalculate when provider changes
    });
});

// Attach event listeners to all cloud input fields
document.querySelectorAll('.provider_inputs input, .provider_inputs select').forEach(input => {
    input.addEventListener('input', calculateEstimatedCloudCost); // For number inputs
    input.addEventListener('change', calculateEstimatedCloudCost); // For select dropdowns
});


// Calculate button click handler
document.getElementById('calculate_button').addEventListener('click', function() {
    // Get the final estimated cloud cost
    const totalEstimatedCloudCost = currentEstimatedCloudCost;

    // Get values from other manual input fields
    const licenseCosts = parseFloat(document.getElementById('license_costs_input').value) || 0;
    const softwareToolCosts = parseFloat(document.getElementById('software_tool_costs_input').value) || 0;
    const supportAdminCosts = parseFloat(document.getElementById('support_admin_costs_input').value) || 0;
    const communicationServicesCost = parseFloat(document.getElementById('communication_services_cost_input').value) || 0;

    // Construct the JSON payload for the backend
    const data = {
        cloud_infrastructure_cost: totalEstimatedCloudCost,
        license_costs: licenseCosts,
        software_tool_costs: softwareToolCosts,
        support_admin_costs: supportAdminCosts,
        communication_services_cost: communicationServicesCost
    };

    // Log the data being sent to the backend for debugging purposes.
    console.log('Sending data:', JSON.stringify(data, null, 2));

    // Perform a POST request to the backend API to calculate prices.
    fetch('http://127.0.0.1:5000/calculate_price', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(results => {
        console.log('Received results:', results);

        // Update the HTML elements to display the calculation results.
        document.getElementById('cloud_infrastructure_costs_display').innerText = `Cloud Infrastructure Costs: $${results.cloud_infrastructure_costs_display.toFixed(2)}`;
        document.getElementById('license_costs_display').innerText = `License Costs: $${results.license_costs_display.toFixed(2)}`;
        document.getElementById('software_tool_costs_display').innerText = `Software Tool Costs: $${results.software_tool_costs_display.toFixed(2)}`;
        document.getElementById('support_admin_costs_display').innerText = `Support & Admin Costs: $${results.support_admin_costs_display.toFixed(2)}`;
        document.getElementById('communication_services_cost_display').innerText = `Communication Services Cost: $${results.communication_services_cost_display.toFixed(2)}`;
        
        document.getElementById('subtotal_display').innerText = `Subtotal (Before Adjustments): $${results.subtotal_before_margin.toFixed(2)}`;
        document.getElementById('market_trend_display').innerText = `Market Trend Adjustment Factor: ${results.market_trend_adjustment_applied.toFixed(2)}x`;
        document.getElementById('competitor_data_display').innerText = `Competitor Data Adjustment Factor: ${results.competitor_data_adjustment_applied.toFixed(2)}x`;
        document.getElementById('subtotal_after_adjustments_display').innerText = `Subtotal (After Adjustments): $${results.subtotal_after_adjustments.toFixed(2)}`;
        
        document.getElementById('margin_display').innerText = `Margin Applied: ${results.margin_applied_percentage.toFixed(2)}%`;
        document.getElementById('total_before_tax_display').innerText = `Total (Before Tax): $${results.total_before_tax.toFixed(2)}`;
        document.getElementById('tax_display').innerText = `Taxation (10%): $${results.taxation.toFixed(2)}`;
        document.getElementById('final_quote_display').innerText = `Final Quote: $${results.final_quote.toFixed(2)}`;
    })
    .catch(error => {
        console.error('Error during fetch:', error);
        document.getElementById('final_quote_display').innerText = 'Error calculating price. Check console for details.';
    });
});

// Initial setup on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set default provider (e.g., Azure) to be visible
    document.getElementById('azure_selector').checked = true; // Ensure radio is checked
    document.querySelectorAll('.provider_inputs').forEach(div => div.style.display = 'none');
    document.getElementById('azure_inputs').style.display = 'block';
    
    // Calculate initial estimated cloud cost
    calculateEstimatedCloudCost();
});
