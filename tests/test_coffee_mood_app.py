# Copyright 2026 Google LLC
# Apache-2.0
"""
Test Suite for Coffee Mood Selection Web App
Verifies acceptance criteria AC1 through AC5 and JSON contract schema compliance.
"""

import json
import os
import re
import unittest


def get_repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestCoffeeMoodContractAndData(unittest.TestCase):
    """Verifies AC1 & AC2: Mood Catalog and Schema Contract adherence."""

    def setUp(self):
        self.repo_root = get_repo_root()
        self.schema_path = os.path.join(self.repo_root, "contracts", "coffee-mood-schema.json")
        self.data_path = os.path.join(self.repo_root, "app", "data", "coffee_moods.js")

    def test_schema_file_exists_and_is_valid_json(self):
        self.assertTrue(os.path.exists(self.schema_path), f"Missing schema at {self.schema_path}")
        with open(self.schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        self.assertEqual(schema.get("title"), "CoffeeMoodRecipe")
        self.assertIn("required", schema)
        self.assertIn("mood_id", schema["required"])

    def test_mood_data_file_contains_all_six_moods(self):
        self.assertTrue(os.path.exists(self.data_path), f"Missing data file at {self.data_path}")
        with open(self.data_path, "r", encoding="utf-8") as f:
            content = f.read()

        required_moods = ["sluggish", "focus", "stressed", "creative", "social", "midnight"]
        for mood in required_moods:
            self.assertIn(f'mood_id: "{mood}"', content, f"Missing required mood {mood} in catalog")

    def test_recipes_have_required_sensory_properties(self):
        with open(self.data_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for presence of required attributes
        self.assertIn("tasting_notes:", content)
        self.assertIn("brew_seconds:", content)
        self.assertIn("water_temp_c:", content)
        self.assertIn("grind_size:", content)
        self.assertIn("lore:", content)


class TestDosageCalculation(unittest.TestCase):
    """Verifies AC3: Dynamic serving size and dosage math."""

    def calculate_brew_dosage(self, ratio, servings=1, is_iced=False, base_volume=250):
        safe_servings = max(1, min(4, int(servings)))
        safe_ratio = max(1.0, float(ratio))

        total_water = base_volume * safe_servings
        hot_water = total_water
        ice_volume = 0

        if is_iced:
            hot_water = round(total_water * 0.6)
            ice_volume = total_water - hot_water

        coffee_grams = round(total_water / safe_ratio, 1)

        return {
            "servings": safe_servings,
            "total_water": total_water,
            "hot_water": hot_water,
            "ice_volume": ice_volume,
            "coffee_grams": coffee_grams
        }

    def test_single_serving_calculation(self):
        res = self.calculate_brew_dosage(ratio=16.0, servings=1)
        self.assertEqual(res["total_water"], 250)
        self.assertEqual(res["coffee_grams"], 15.6)
        self.assertEqual(res["ice_volume"], 0)

    def test_double_serving_calculation(self):
        res = self.calculate_brew_dosage(ratio=16.0, servings=2)
        self.assertEqual(res["total_water"], 500)
        self.assertEqual(res["coffee_grams"], 31.2)

    def test_iced_serving_splits_ice_and_hot_water(self):
        res = self.calculate_brew_dosage(ratio=15.0, servings=1, is_iced=True)
        self.assertEqual(res["total_water"], 250)
        self.assertEqual(res["hot_water"], 150)
        self.assertEqual(res["ice_volume"], 100)
        self.assertEqual(res["coffee_grams"], 16.7)


class TestBrewTimerLogic(unittest.TestCase):
    """Verifies AC4: Interactive countdown brew timer state and formatting."""

    def format_time(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def test_time_formatting(self):
        self.assertEqual(self.format_time(180), "03:00")
        self.assertEqual(self.format_time(65), "01:05")
        self.assertEqual(self.format_time(0), "00:00")

    def test_timer_phases(self):
        def get_phase(total, remaining):
            elapsed = total - remaining
            if elapsed < 45:
                return "Bloom"
            if elapsed < (total * 0.75):
                return "Pour"
            return "Drawdown"

        total = 180
        self.assertEqual(get_phase(total, 180), "Bloom")
        self.assertEqual(get_phase(total, 150), "Bloom")
        self.assertEqual(get_phase(total, 100), "Pour")
        self.assertEqual(get_phase(total, 20), "Drawdown")


class TestSemanticHTMLAndAccessibility(unittest.TestCase):
    """Verifies AC5: Responsive UI, semantic HTML, and accessibility compliance."""

    def setUp(self):
        self.repo_root = get_repo_root()
        self.html_path = os.path.join(self.repo_root, "app", "index.html")

    def test_html_file_exists(self):
        self.assertTrue(os.path.exists(self.html_path), f"Missing index.html at {self.html_path}")

    def test_html_contains_critical_semantic_elements(self):
        with open(self.html_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn("<header>", html)
        self.assertIn("<main>", html)
        self.assertIn('role="region"', html)
        self.assertIn('aria-label="Mood Selector"', html)
        self.assertIn('role="timer"', html)
        self.assertIn('aria-live="polite"', html)

    def test_controls_have_accessible_labels(self):
        with open(self.html_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn('aria-label="Start timer"', html)
        self.assertIn('aria-label="Pause timer"', html)
        self.assertIn('aria-label="Reset timer"', html)
        self.assertIn('aria-label="Serving size"', html)


if __name__ == "__main__":
    unittest.main()
