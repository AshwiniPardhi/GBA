"""
Backend Flask application for the Pricing Calculator.

This module handles the API requests for calculating project costs based on various inputs,
applies business logic for adjustments and margins, and includes taxation.
Refactored to simplify cost categories and input structure.
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

# Margin Rates
TARGET_MARGIN = 0.45  # Target profit margin as a percentage of the selling price
MINIMUM_MARGIN = 0.35 # Minimum acceptable profit margin

# Tax Rate
TAX_RATE = 0.10       # Standard tax rate

# Cloud Pricing Data - Source of truth for cloud cost estimation parameters
# This data is mirrored from the frontend's cloudPricingData object for consistency.
# In a future enhancement, the frontend could fetch this data directly from an API endpoint.
CLOUD_PRICING_DATA_PY = {
    'azure': {
        'compute_tiers': {'basic': 50, 'general': 150, 'optimized': 300}, # Cost per instance/month
        'storage_per_gb': 0.2,  # Cost per GB/month (adjusted from original 0.5 for realism)
        'db_tiers': {'basic': 20, 'standard': 100, 'premium': 400} # Cost per DB instance/month
    },
    'aws': {
        'compute_tiers': {'basic': 55, 'general': 160, 'optimized': 310},
        'storage_per_gb': 0.22, # (adjusted from original 0.55)
        'db_tiers': {'basic': 25, 'standard': 110, 'premium': 420}
    },
    'gcp': {
        'compute_tiers': {'basic': 45, 'general': 140, 'optimized': 290},
        'storage_per_gb': 0.18, # (adjusted from original 0.45)
        'db_tiers': {'basic': 18, 'standard': 90, 'premium': 380} # (adjusted gcp db basic from 15 to 18)
    }
}

# TODO: Update this function to read from a database or a configuration file that is updated daily.
def get_market_trend_adjustment():
    """
    Placeholder for fetching market trend adjustment factor.
    This factor accounts for general market conditions.
    """
    return 1.05

# TODO: Update this function to read from a database or a configuration file that is updated daily based on competitor tracking.
def get_competitor_data_adjustment():
    """
    Placeholder for fetching competitor data adjustment factor.
    This factor accounts for pricing strategies relative to competitors.
    """
    return 0.98

@app.route('/')
def home():
    """Root endpoint to indicate the backend is running."""
    return "Pricing Calculator Backend is Running"

@app.route('/api/cloud_pricing_data', methods=['GET'])
def get_cloud_pricing_data():
    """
    API endpoint to serve the cloud pricing data.
    Allows frontend to fetch this data if needed in the future.
    """
    return jsonify(CLOUD_PRICING_DATA_PY)

@app.route('/calculate_price', methods=['POST'])
def calculate_price():
    """
    API endpoint to calculate the price based on input costs.
    Expects a JSON payload with specific cost components.
    """
    data = request.get_json()

    # Extract cost components from the JSON request data.
    # Default to 0 if a key is not present.
    cloud_infrastructure_cost = data.get('cloud_infrastructure_cost', 0)
    license_costs = data.get('license_costs', 0)
    software_tool_costs = data.get('software_tool_costs', 0)
    support_admin_costs = data.get('support_admin_costs', 0)
    communication_services_cost = data.get('communication_services_cost', 0)

    # Calculate Subtotal Before Adjustments: Sum of all direct input costs.
    subtotal_before_external_adjustments = (
        cloud_infrastructure_cost +
        license_costs +
        software_tool_costs +
        support_admin_costs +
        communication_services_cost
    )

    # Apply Market Trend and Competitor Data Adjustments
    market_trend_multiplier = get_market_trend_adjustment()
    competitor_data_multiplier = get_competitor_data_adjustment()

    subtotal_after_adjustments = subtotal_before_external_adjustments * market_trend_multiplier * competitor_data_multiplier
    
    total_costs_for_margin = subtotal_after_adjustments # This is the cost base for margin calculation

    # Apply Margin to determine the selling price before tax.
    # Price = Cost / (1 - MarginRate)
    final_quote_pre_tax = total_costs_for_margin / (1 - TARGET_MARGIN)
    actual_margin_applied_rate = TARGET_MARGIN

    # Ensure the applied margin meets the minimum required margin.
    # If total_costs_for_margin is 0, final_quote_pre_tax is 0, so calculated_margin_percentage is 0.
    calculated_margin_percentage = (final_quote_pre_tax - total_costs_for_margin) / final_quote_pre_tax if final_quote_pre_tax != 0 else 0
    
    if calculated_margin_percentage < MINIMUM_MARGIN:
        final_quote_pre_tax = total_costs_for_margin / (1 - MINIMUM_MARGIN)
        actual_margin_applied_rate = MINIMUM_MARGIN
    
    margin_applied_percentage_display = actual_margin_applied_rate * 100 # Convert to percentage for display.

    # Calculate Taxation based on the final quote before tax.
    taxation = final_quote_pre_tax * TAX_RATE
    final_quote_with_tax = final_quote_pre_tax + taxation # Total price including tax.

    # Structure the response data. All monetary values are rounded to 2 decimal places.
    response = {
        "cloud_infrastructure_costs_display": round(cloud_infrastructure_cost, 2),
        "license_costs_display": round(license_costs, 2),
        "software_tool_costs_display": round(software_tool_costs, 2),
        "support_admin_costs_display": round(support_admin_costs, 2),
        "communication_services_cost_display": round(communication_services_cost, 2),
        "subtotal_before_margin": round(subtotal_before_external_adjustments, 2), # Renamed for clarity
        "market_trend_adjustment_applied": market_trend_multiplier,
        "competitor_data_adjustment_applied": competitor_data_multiplier,
        "subtotal_after_adjustments": round(subtotal_after_adjustments, 2),
        "margin_applied_percentage": round(margin_applied_percentage_display, 2),
        "total_before_tax": round(final_quote_pre_tax, 2),
        "taxation": round(taxation, 2),
        "final_quote": round(final_quote_with_tax, 2)
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
