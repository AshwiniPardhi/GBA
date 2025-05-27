import unittest
import json
from app import app, get_market_trend_adjustment, get_competitor_data_adjustment, TARGET_MARGIN, MINIMUM_MARGIN, TAX_RATE

# To run tests:
# Navigate to the root directory of the project in your terminal
# Run the command: python -m unittest app.test_app

class TestPricingCalculatorRefactored(unittest.TestCase):

    def setUp(self):
        """Set up test client and other resources."""
        self.app = app.test_client()
        self.app.testing = True
        # Base rates and multipliers for manual calculation
        self.market_multiplier = get_market_trend_adjustment()
        self.competitor_multiplier = get_competitor_data_adjustment()
        self.target_margin_rate = TARGET_MARGIN
        self.min_margin_rate = MINIMUM_MARGIN
        self.tax_rate = TAX_RATE

    def _calculate_expected_values(self, data):
        """
        Helper function to calculate expected results based on input data,
        aligned with the refactored backend logic.
        """
        cloud_infra_cost = data.get('cloud_infrastructure_cost', 0)
        license_costs_val = data.get('license_costs', 0)
        software_tool_costs_val = data.get('software_tool_costs', 0)
        support_admin_costs_val = data.get('support_admin_costs', 0)
        comm_services_cost_val = data.get('communication_services_cost', 0)

        # Calculate Subtotal Before External Adjustments
        subtotal_before_external_adjustments = (
            cloud_infra_cost + license_costs_val + software_tool_costs_val +
            support_admin_costs_val + comm_services_cost_val
        )

        # Apply Market Trend and Competitor Data Adjustments
        subtotal_after_adjustments = subtotal_before_external_adjustments * self.market_multiplier * self.competitor_multiplier
        
        total_costs_for_margin = subtotal_after_adjustments

        # Apply Margin
        final_quote_pre_tax = total_costs_for_margin / (1 - self.target_margin_rate)
        actual_margin_applied_rate = self.target_margin_rate
        
        calculated_margin_percentage = (final_quote_pre_tax - total_costs_for_margin) / final_quote_pre_tax if final_quote_pre_tax != 0 else 0

        if calculated_margin_percentage < self.min_margin_rate:
            final_quote_pre_tax = total_costs_for_margin / (1 - self.min_margin_rate)
            actual_margin_applied_rate = self.min_margin_rate
            
        margin_applied_percentage_display = actual_margin_applied_rate * 100

        # Calculate Taxation
        taxation = final_quote_pre_tax * self.tax_rate
        final_quote_with_tax = final_quote_pre_tax + taxation

        return {
            "cloud_infrastructure_costs_display": round(cloud_infra_cost, 2),
            "license_costs_display": round(license_costs_val, 2),
            "software_tool_costs_display": round(software_tool_costs_val, 2),
            "support_admin_costs_display": round(support_admin_costs_val, 2),
            "communication_services_cost_display": round(comm_services_cost_val, 2),
            "subtotal_before_margin": round(subtotal_before_external_adjustments, 2),
            "market_trend_adjustment_applied": self.market_multiplier,
            "competitor_data_adjustment_applied": self.competitor_multiplier,
            "subtotal_after_adjustments": round(subtotal_after_adjustments, 2),
            "margin_applied_percentage": round(margin_applied_percentage_display, 2),
            "total_before_tax": round(final_quote_pre_tax, 2),
            "taxation": round(taxation, 2),
            "final_quote": round(final_quote_with_tax, 2)
        }

    def test_basic_calculation_refactored(self):
        """Test a typical calculation with the new refactored inputs."""
        payload = {
            "cloud_infrastructure_cost": 200,
            "license_costs": 50,
            "software_tool_costs": 100,
            "support_admin_costs": 150,
            "communication_services_cost": 30
        } # Total sum = 530
        response = self.app.post('/calculate_price',
                                 data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        result_data = json.loads(response.data)
        
        expected_results = self._calculate_expected_values(payload)

        # Assert all new keys are present
        expected_keys = [
            "cloud_infrastructure_costs_display", "license_costs_display", 
            "software_tool_costs_display", "support_admin_costs_display", 
            "communication_services_cost_display", "subtotal_before_margin", 
            "market_trend_adjustment_applied", "competitor_data_adjustment_applied", 
            "subtotal_after_adjustments", "margin_applied_percentage", 
            "total_before_tax", "taxation", "final_quote"
        ]
        for key in expected_keys:
            self.assertIn(key, result_data, f"Key {key} missing in response")

        for key in expected_results:
            self.assertEqual(expected_results[key], result_data[key], f"Mismatch in {key}")

    def test_zero_inputs_refactored(self):
        """Test calculation with all zero inputs for the new structure."""
        payload = {
            "cloud_infrastructure_cost": 0,
            "license_costs": 0,
            "software_tool_costs": 0,
            "support_admin_costs": 0,
            "communication_services_cost": 0
        }
        response = self.app.post('/calculate_price',
                                 data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        result_data = json.loads(response.data)
        expected_results = self._calculate_expected_values(payload)
        
        # With zero cost, margin applied should be MINIMUM_MARGIN (35%) percentage, but final values are 0.
        self.assertEqual(result_data['margin_applied_percentage'], self.min_margin_rate * 100)
        self.assertEqual(result_data['final_quote'], 0)
        for key in expected_results:
            self.assertEqual(expected_results[key], result_data[key], f"Mismatch in {key} for zero inputs")


    def test_target_margin_refactored(self):
        """Test that target margin (45%) is applied for typical positive costs with new structure."""
        payload = {
            "cloud_infrastructure_cost": 100, # Non-zero cost to ensure target margin applies
            "license_costs": 10,
            "software_tool_costs": 20,
            "support_admin_costs": 30,
            "communication_services_cost": 5
        } # subtotal_before_external_adjustments = 165
        
        response = self.app.post('/calculate_price', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        result_data = json.loads(response.data)
        expected_results = self._calculate_expected_values(payload)

        self.assertGreater(expected_results['subtotal_after_adjustments'], 0)
        self.assertEqual(result_data['margin_applied_percentage'], self.target_margin_rate * 100)
        self.assertEqual(result_data['final_quote'], expected_results['final_quote'])

    def test_minimum_margin_scenario_if_subtotal_is_zero_refactored(self):
        """
        Tests if the minimum margin percentage is reported when the subtotal_after_adjustments is zero.
        """
        payload = { # All inputs are zero
            "cloud_infrastructure_cost": 0, "license_costs": 0, "software_tool_costs": 0,
            "support_admin_costs": 0, "communication_services_cost": 0
        }
        
        expected_results = self._calculate_expected_values(payload) # Helper will show min margin %
        self.assertEqual(expected_results['subtotal_after_adjustments'], 0)
        self.assertEqual(expected_results['margin_applied_percentage'], self.min_margin_rate * 100)
        self.assertEqual(expected_results['final_quote'], 0)
        
        response = self.app.post('/calculate_price', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        result_data = json.loads(response.data)
        
        self.assertEqual(result_data['margin_applied_percentage'], self.min_margin_rate * 100)
        self.assertEqual(result_data['final_quote'], 0)

    def test_adjustment_factors_application(self):
        """
        Test that market trend and competitor data adjustments are correctly applied and reported.
        """
        payload = {
            "cloud_infrastructure_cost": 1000, # Arbitrary sum for subtotal_before_external_adjustments
            "license_costs": 0,
            "software_tool_costs": 0,
            "support_admin_costs": 0,
            "communication_services_cost": 0
        }
        
        response = self.app.post('/calculate_price', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        result_data = json.loads(response.data)

        expected_subtotal_before_adjustments = 1000.00
        self.assertEqual(result_data['subtotal_before_margin'], expected_subtotal_before_adjustments)

        self.assertEqual(result_data['market_trend_adjustment_applied'], self.market_multiplier)
        self.assertEqual(result_data['competitor_data_adjustment_applied'], self.competitor_multiplier)

        expected_subtotal_after_adjustments = round(
            expected_subtotal_before_adjustments * self.market_multiplier * self.competitor_multiplier, 2
        )
        self.assertEqual(result_data['subtotal_after_adjustments'], expected_subtotal_after_adjustments)
        
        # Also check a value that depends on these adjustments
        expected_results = self._calculate_expected_values(payload)
        self.assertEqual(result_data['total_before_tax'], expected_results['total_before_tax'])

if __name__ == '__main__':
    unittest.main()
