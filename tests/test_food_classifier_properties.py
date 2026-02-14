"""Property-based tests for FoodClassifier using Hypothesis."""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from jeevanfit.models.core import FoodItem, NutritionalInfo
from jeevanfit.analyzers import FoodClassifier, FoodCategory


# Strategy for generating valid nutritional info
@st.composite
def nutritional_info_strategy(draw):
    """Generate valid NutritionalInfo instances."""
    return NutritionalInfo(
        calories=draw(st.floats(min_value=0, max_value=1000)),
        protein=draw(st.floats(min_value=0, max_value=100)),
        carbohydrates=draw(st.floats(min_value=0, max_value=200)),
        fat=draw(st.floats(min_value=0, max_value=100)),
        sodium=draw(st.floats(min_value=0, max_value=2000)),
        sugar=draw(st.floats(min_value=0, max_value=100)),
        fiber=draw(st.floats(min_value=0, max_value=50)),
        preservatives=draw(st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=3, max_size=15),
            min_size=0,
            max_size=5
        )),
        processing_level=draw(st.integers(min_value=1, max_value=5))
    )


# Strategy for generating valid food items
@st.composite
def food_item_strategy(draw):
    """Generate valid FoodItem instances."""
    return FoodItem(
        name=draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=1, max_size=30)),
        serving_size=draw(st.floats(min_value=0.1, max_value=1000)),
        unit=draw(st.sampled_from(['g', 'ml', 'oz', 'cup', 'tbsp', 'piece'])),
        nutritional_info=draw(nutritional_info_strategy())
    )


class TestFoodClassifierProperties:
    """Property-based tests for FoodClassifier."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = FoodClassifier()
    
    # Feature: fitbuddy-lifestyle-assistant, Property 1: Food classification consistency
    @given(food_item=food_item_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_classification_consistency(self, food_item):
        """
        Property 1: Food classification consistency
        For any food item with identical nutritional parameters, 
        classifying it multiple times should always produce the same 
        category and rationale.
        
        Validates: Requirements 1.4
        """
        result1 = self.classifier.classify_food(food_item)
        result2 = self.classifier.classify_food(food_item)
        
        assert result1.category == result2.category, \
            f"Category mismatch: {result1.category} != {result2.category}"
        assert result1.rationale == result2.rationale, \
            f"Rationale mismatch: {result1.rationale} != {result2.rationale}"
        assert result1.dominant_factors == result2.dominant_factors, \
            f"Dominant factors mismatch: {result1.dominant_factors} != {result2.dominant_factors}"

    # Feature: fitbuddy-lifestyle-assistant, Property 2: Classification rationale completeness
    @given(food_item=food_item_strategy())
    @settings(max_examples=100)
    def test_rationale_completeness(self, food_item):
        """
        Property 2: Classification rationale completeness
        For any food item that is classified, the classification result 
        should include a non-empty rationale explaining the categorization.
        
        Validates: Requirements 1.2
        """
        result = self.classifier.classify_food(food_item)
        
        assert result.rationale is not None, "Rationale should not be None"
        assert len(result.rationale) > 0, "Rationale should not be empty"
        assert result.rationale.strip() != "", "Rationale should not be just whitespace"
        
        # Rationale should contain meaningful content (at least 10 characters)
        assert len(result.rationale.strip()) >= 10, \
            f"Rationale too short: '{result.rationale}'"

    # Feature: fitbuddy-lifestyle-assistant, Property 4: Valid classification categories
    @given(food_item=food_item_strategy())
    @settings(max_examples=100)
    def test_valid_categories(self, food_item):
        """
        Property 4: Valid classification categories
        For any food item, the classification result should be one of 
        the three valid categories: HEALTHY, JUNK, or PRESERVATIVE_HEAVY.
        
        Validates: Requirements 1.1
        """
        result = self.classifier.classify_food(food_item)
        
        valid_categories = {FoodCategory.HEALTHY, FoodCategory.JUNK, FoodCategory.PRESERVATIVE_HEAVY}
        assert result.category in valid_categories, \
            f"Invalid category: {result.category}. Must be one of {valid_categories}"
        
        # Also verify it's a proper FoodCategory enum value
        assert isinstance(result.category, FoodCategory), \
            f"Category must be a FoodCategory enum, got {type(result.category)}"
