"""Tests for FoodClassifier."""

import pytest
from jeevanfit.models.core import FoodItem, NutritionalInfo
from jeevanfit.analyzers import FoodClassifier, FoodCategory


class TestFoodClassifier:
    """Test suite for FoodClassifier."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = FoodClassifier()
    
    def test_classify_healthy_food(self):
        """Test classification of a healthy food item."""
        food = FoodItem(
            name="Grilled chicken breast",
            serving_size=100,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=165,
                protein=31,
                carbohydrates=0,
                fat=3.6,
                sodium=74,
                sugar=0,
                fiber=0,
                preservatives=[],
                processing_level=1
            )
        )
        
        result = self.classifier.classify_food(food)
        
        assert result.category == FoodCategory.HEALTHY
        assert result.confidence >= 60
        assert len(result.rationale) > 0
        assert len(result.dominant_factors) > 0
    
    def test_classify_junk_food(self):
        """Test classification of junk food."""
        food = FoodItem(
            name="Candy bar",
            serving_size=50,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=250,
                protein=2,
                carbohydrates=35,
                fat=12,
                sodium=150,
                sugar=28,
                fiber=1,
                preservatives=["TBHQ"],
                processing_level=5
            )
        )
        
        result = self.classifier.classify_food(food)
        
        assert result.category == FoodCategory.JUNK
        assert result.confidence >= 60
        assert "sugar" in result.rationale.lower() or "high" in result.rationale.lower()
        assert len(result.dominant_factors) > 0
    
    def test_classify_preservative_heavy_food(self):
        """Test classification of preservative-heavy food."""
        food = FoodItem(
            name="Processed deli meat",
            serving_size=50,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=120,
                protein=10,
                carbohydrates=2,
                fat=8,
                sodium=650,
                sugar=1,
                fiber=0,
                preservatives=["sodium nitrite", "sodium benzoate", "potassium sorbate"],
                processing_level=4
            )
        )
        
        result = self.classifier.classify_food(food)
        
        assert result.category == FoodCategory.PRESERVATIVE_HEAVY
        assert result.confidence >= 60
        assert "preservative" in result.rationale.lower()
        assert "preservatives" in result.dominant_factors
    
    def test_get_fsi_parameters(self):
        """Test FSI parameter extraction."""
        food = FoodItem(
            name="Whole wheat bread",
            serving_size=2,
            unit="slices",
            nutritional_info=NutritionalInfo(
                calories=160,
                protein=8,
                carbohydrates=28,
                fat=2,
                sodium=300,
                sugar=4,
                fiber=4,
                preservatives=[],
                processing_level=2
            )
        )
        
        params = self.classifier.get_fsi_parameters(food)
        
        assert 0 <= params.nutrient_density <= 1
        assert 0 <= params.processing_score <= 1
        assert 0 <= params.preservative_load <= 1
        assert 0 <= params.sugar_content <= 1
        assert 0 <= params.sodium_level <= 1
    
    def test_classification_consistency(self):
        """Test that same food gets same classification."""
        food = FoodItem(
            name="Apple",
            serving_size=1,
            unit="medium",
            nutritional_info=NutritionalInfo(
                calories=95,
                protein=0.5,
                carbohydrates=25,
                fat=0.3,
                sodium=2,
                sugar=19,
                fiber=4,
                preservatives=[],
                processing_level=1
            )
        )
        
        result1 = self.classifier.classify_food(food)
        result2 = self.classifier.classify_food(food)
        
        assert result1.category == result2.category
        assert result1.rationale == result2.rationale
        assert result1.dominant_factors == result2.dominant_factors
    
    def test_rationale_completeness(self):
        """Test that all classifications include rationale."""
        foods = [
            FoodItem(
                name="Salad",
                serving_size=200,
                unit="g",
                nutritional_info=NutritionalInfo(
                    calories=50,
                    protein=3,
                    carbohydrates=8,
                    fat=1,
                    sodium=50,
                    sugar=3,
                    fiber=4,
                    preservatives=[],
                    processing_level=1
                )
            ),
            FoodItem(
                name="Chips",
                serving_size=50,
                unit="g",
                nutritional_info=NutritionalInfo(
                    calories=270,
                    protein=3,
                    carbohydrates=27,
                    fat=17,
                    sodium=800,
                    sugar=2,
                    fiber=2,
                    preservatives=["BHA", "BHT"],
                    processing_level=5
                )
            )
        ]
        
        for food in foods:
            result = self.classifier.classify_food(food)
            assert len(result.rationale) > 0
            assert result.rationale.strip() != ""

    def test_borderline_nutrient_density(self):
        """Test classification at nutrient density threshold boundaries."""
        # Just above healthy threshold (0.7)
        food_high = FoodItem(
            name="High nutrient food",
            serving_size=100,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=100,
                protein=8,
                carbohydrates=10,
                fat=2,
                sodium=50,
                sugar=2,
                fiber=5,
                preservatives=[],
                processing_level=1
            )
        )
        result_high = self.classifier.classify_food(food_high)
        assert result_high.category == FoodCategory.HEALTHY
        
        # Just below junk threshold (0.3)
        food_low = FoodItem(
            name="Low nutrient food",
            serving_size=100,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=300,
                protein=2,
                carbohydrates=40,
                fat=15,
                sodium=700,
                sugar=20,
                fiber=0,
                preservatives=[],
                processing_level=5
            )
        )
        result_low = self.classifier.classify_food(food_low)
        assert result_low.category == FoodCategory.JUNK
    
    def test_multiple_characteristics_food(self):
        """Test food with characteristics spanning multiple categories."""
        # High protein but also high sodium and preservatives
        food = FoodItem(
            name="Protein bar with preservatives",
            serving_size=60,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=200,
                protein=20,
                carbohydrates=15,
                fat=8,
                sodium=650,
                sugar=10,
                fiber=3,
                preservatives=["sodium benzoate", "potassium sorbate", "BHT"],
                processing_level=4
            )
        )
        
        result = self.classifier.classify_food(food)
        
        # Should be classified as preservative-heavy due to 3+ preservatives
        assert result.category == FoodCategory.PRESERVATIVE_HEAVY
        assert "preservatives" in result.dominant_factors
    
    def test_preservative_heavy_detection_exact_threshold(self):
        """Test preservative-heavy detection at exact threshold (3 preservatives)."""
        food = FoodItem(
            name="Food with exactly 3 preservatives",
            serving_size=100,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=150,
                protein=5,
                carbohydrates=20,
                fat=5,
                sodium=400,
                sugar=8,
                fiber=2,
                preservatives=["preservative1", "preservative2", "preservative3"],
                processing_level=3
            )
        )
        
        result = self.classifier.classify_food(food)
        assert result.category == FoodCategory.PRESERVATIVE_HEAVY
    
    def test_high_sugar_threshold(self):
        """Test junk classification at sugar threshold (15g)."""
        # Just above threshold
        food_high_sugar = FoodItem(
            name="Sweet snack",
            serving_size=50,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=200,
                protein=2,
                carbohydrates=30,
                fat=8,
                sodium=100,
                sugar=16,
                fiber=1,
                preservatives=[],
                processing_level=4
            )
        )
        
        result = self.classifier.classify_food(food_high_sugar)
        assert result.category == FoodCategory.JUNK
        assert "high_sugar" in result.dominant_factors
    
    def test_high_sodium_threshold(self):
        """Test junk classification at sodium threshold (600mg)."""
        food_high_sodium = FoodItem(
            name="Salty snack",
            serving_size=50,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=180,
                protein=3,
                carbohydrates=20,
                fat=10,
                sodium=650,
                sugar=2,
                fiber=1,
                preservatives=[],
                processing_level=4
            )
        )
        
        result = self.classifier.classify_food(food_high_sodium)
        assert result.category == FoodCategory.JUNK
        assert "high_sodium" in result.dominant_factors
    
    def test_ambiguous_classification_defaults_to_cautious(self):
        """Test that ambiguous foods default to more cautious category."""
        # Food that could be borderline healthy or junk
        food = FoodItem(
            name="Borderline food",
            serving_size=100,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=180,
                protein=6,
                carbohydrates=25,
                fat=6,
                sodium=350,
                sugar=8,
                fiber=3,
                preservatives=[],
                processing_level=3
            )
        )
        
        result = self.classifier.classify_food(food)
        # Should have a valid category and rationale
        assert result.category in [FoodCategory.HEALTHY, FoodCategory.JUNK]
        assert len(result.rationale) > 0
    
    def test_zero_calorie_food(self):
        """Test classification of zero-calorie food."""
        food = FoodItem(
            name="Zero calorie drink",
            serving_size=240,
            unit="ml",
            nutritional_info=NutritionalInfo(
                calories=0,
                protein=0,
                carbohydrates=0,
                fat=0,
                sodium=50,
                sugar=0,
                fiber=0,
                preservatives=["aspartame", "acesulfame K"],
                processing_level=5
            )
        )
        
        result = self.classifier.classify_food(food)
        # Should still classify (likely as preservative-heavy or junk)
        assert result.category in [FoodCategory.PRESERVATIVE_HEAVY, FoodCategory.JUNK]
        assert len(result.rationale) > 0
