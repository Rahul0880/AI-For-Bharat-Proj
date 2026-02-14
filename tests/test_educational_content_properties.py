"""Property-based tests for universal educational content using Hypothesis."""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, time

from jeevanfit.models.core import (
    FoodItem,
    NutritionalInfo,
    SleepData,
    BodyType,
    Habit,
    LifestyleInput,
    BodyTypeClassification,
    HabitType,
)
from jeevanfit.analyzers import (
    FoodClassifier,
    WaterRetentionPredictor,
    SleepAnalyzer,
    BodyTypeAnalyzer,
)


# Strategy for generating valid nutritional info
@st.composite
def nutritional_info_strategy(draw):
    """Generate valid NutritionalInfo instances."""
    return NutritionalInfo(
        calories=draw(st.floats(min_value=0, max_value=1000)),
        protein=draw(st.floats(min_value=0, max_value=100)),
        carbohydrates=draw(st.floats(min_value=0, max_value=200)),
        fat=draw(st.floats(min_value=0, max_value=100)),
        sodium=draw(st.floats(min_value=0, max_value=5000)),
        sugar=draw(st.floats(min_value=0, max_value=100)),
        fiber=draw(st.floats(min_value=0, max_value=50)),
        preservatives=draw(st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=15),
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


# Strategy for generating valid sleep data
@st.composite
def sleep_data_strategy(draw):
    """Generate valid SleepData instances."""
    bedtime_hour = draw(st.integers(min_value=20, max_value=23))
    wake_hour = draw(st.integers(min_value=5, max_value=10))
    
    return SleepData(
        duration=draw(st.floats(min_value=3.0, max_value=12.0)),
        quality=draw(st.integers(min_value=1, max_value=10)),
        bedtime=time(bedtime_hour, draw(st.integers(min_value=0, max_value=59))),
        wake_time=time(wake_hour, draw(st.integers(min_value=0, max_value=59))),
        interruptions=draw(st.integers(min_value=0, max_value=10)),
        timestamp=datetime.now()
    )


# Strategy for generating valid habits
@st.composite
def habit_strategy(draw):
    """Generate valid Habit instances."""
    habit_type = draw(st.sampled_from(list(HabitType)))
    
    return Habit(
        type=habit_type,
        intensity=draw(st.integers(min_value=1, max_value=10)),
        duration=draw(st.floats(min_value=0.1, max_value=8.0)),
        timing=time(draw(st.integers(min_value=6, max_value=22)), 
                   draw(st.integers(min_value=0, max_value=59))),
        notes=draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', max_size=50))
    )


# Strategy for generating lifestyle input
@st.composite
def lifestyle_input_strategy(draw):
    """Generate valid LifestyleInput instances."""
    # Generate food items
    food_items = draw(st.lists(food_item_strategy(), min_size=0, max_size=5))
    
    # Generate water intake
    water_intake = draw(st.floats(min_value=500, max_value=5000))
    
    # Optionally include sleep data
    sleep_data = draw(st.one_of(st.none(), sleep_data_strategy()))
    
    # Generate habits
    daily_habits = draw(st.lists(habit_strategy(), min_size=0, max_size=5))
    
    return LifestyleInput(
        food_items=food_items,
        water_intake=water_intake,
        sleep_data=sleep_data,
        daily_habits=daily_habits,
        timestamp=datetime.now(),
        user_id=draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=5, max_size=20)),
        notes=draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', max_size=100))
    )


# Strategy for generating body types
@st.composite
def body_type_strategy(draw):
    """Generate valid BodyType instances."""
    classification = draw(st.sampled_from(list(BodyTypeClassification)))
    
    return BodyType(
        classification=classification,
        characteristics=draw(st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=5, max_size=30),
            min_size=0,
            max_size=3
        )),
        user_id=draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=5, max_size=20))
    )


class TestEducationalContentProperties:
    """Property-based tests for universal educational content across all analyzers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.food_classifier = FoodClassifier()
        self.water_predictor = WaterRetentionPredictor()
        self.sleep_analyzer = SleepAnalyzer()
        self.body_type_analyzer = BodyTypeAnalyzer()
    
    # Feature: fitbuddy-lifestyle-assistant, Property 17: Universal educational content
    @given(
        food_item=food_item_strategy(),
        lifestyle=lifestyle_input_strategy(),
        body_type=body_type_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_universal_educational_content(self, food_item, lifestyle, body_type):
        """
        Property 17: Universal educational content
        For any analysis result from any analyzer (food, water, sleep, body type), 
        the output should include educational content explaining underlying 
        cause-and-effect relationships.
        
        Validates: Requirements 5.1
        """
        # Cause-effect indicators to look for in educational content
        cause_effect_indicators = [
            'affect', 'impact', 'influence', 'cause', 'result', 'lead',
            'disrupt', 'interfere', 'improve', 'reduce', 'increase',
            'factor', 'primary', 'contributing', 'because', 'due to',
            'help', 'support', 'promote', 'enhance', 'benefit'
        ]
        
        # Test 1: Food Classifier - should have rationale with educational content
        food_result = self.food_classifier.classify_food(food_item)
        
        assert food_result.rationale is not None, \
            "Food classification must include a rationale"
        assert len(food_result.rationale) > 0, \
            "Food classification rationale should not be empty"
        assert len(food_result.rationale.strip()) >= 20, \
            f"Food classification rationale should be educational (>=20 chars), " \
            f"got {len(food_result.rationale)} chars: '{food_result.rationale}'"
        
        # Verify rationale contains cause-effect language
        rationale_lower = food_result.rationale.lower()
        has_cause_effect = any(indicator in rationale_lower for indicator in cause_effect_indicators)
        assert has_cause_effect, \
            f"Food classification rationale should explain cause-effect relationships. " \
            f"Expected words like 'affect', 'impact', 'cause', etc. " \
            f"Got: '{food_result.rationale}'"
        
        # Test 2: Water Retention Predictor - should have explanation with educational content
        water_result = self.water_predictor.predict_retention(lifestyle, body_type)
        
        assert water_result.explanation is not None, \
            "Water retention prediction must include an explanation"
        assert len(water_result.explanation) > 0, \
            "Water retention explanation should not be empty"
        assert len(water_result.explanation.strip()) >= 30, \
            f"Water retention explanation should be educational (>=30 chars), " \
            f"got {len(water_result.explanation)} chars: '{water_result.explanation}'"
        
        # Verify explanation contains cause-effect language
        explanation_lower = water_result.explanation.lower()
        has_cause_effect = any(indicator in explanation_lower for indicator in cause_effect_indicators)
        assert has_cause_effect, \
            f"Water retention explanation should explain cause-effect relationships. " \
            f"Expected words like 'affect', 'impact', 'cause', etc. " \
            f"Got: '{water_result.explanation}'"
        
        # Test 3: Sleep Analyzer - should have explanation with educational content
        # Ensure lifestyle has sleep data
        if lifestyle.sleep_data is None:
            lifestyle.sleep_data = SleepData(
                duration=7.0,
                quality=6,
                bedtime=time(22, 0),
                wake_time=time(5, 0),
                interruptions=1,
                timestamp=datetime.now()
            )
        
        sleep_result = self.sleep_analyzer.analyze_sleep(lifestyle.sleep_data, lifestyle)
        
        assert sleep_result.explanation is not None, \
            "Sleep analysis must include an explanation"
        assert len(sleep_result.explanation) > 0, \
            "Sleep analysis explanation should not be empty"
        assert len(sleep_result.explanation.strip()) >= 40, \
            f"Sleep analysis explanation should be educational (>=40 chars), " \
            f"got {len(sleep_result.explanation)} chars: '{sleep_result.explanation}'"
        
        # Verify explanation contains cause-effect language
        sleep_explanation_lower = sleep_result.explanation.lower()
        has_cause_effect = any(indicator in sleep_explanation_lower for indicator in cause_effect_indicators)
        assert has_cause_effect, \
            f"Sleep analysis explanation should explain cause-effect relationships. " \
            f"Expected words like 'affect', 'impact', 'cause', etc. " \
            f"Got: '{sleep_result.explanation}'"
        
        # Test 4: Body Type Analyzer - should have educational content in multiple fields
        body_result = self.body_type_analyzer.analyze_body_type(body_type, lifestyle)
        
        # Check metabolic_response field
        assert body_result.metabolic_response is not None, \
            "Body type analysis must include metabolic_response"
        assert len(body_result.metabolic_response) > 0, \
            "Body type metabolic_response should not be empty"
        assert len(body_result.metabolic_response.strip()) >= 30, \
            f"Body type metabolic_response should be educational (>=30 chars), " \
            f"got {len(body_result.metabolic_response)} chars: '{body_result.metabolic_response}'"
        
        # Check fat_storage_pattern field
        assert body_result.fat_storage_pattern is not None, \
            "Body type analysis must include fat_storage_pattern"
        assert len(body_result.fat_storage_pattern) > 0, \
            "Body type fat_storage_pattern should not be empty"
        
        # Check energy_utilization field
        assert body_result.energy_utilization is not None, \
            "Body type analysis must include energy_utilization"
        assert len(body_result.energy_utilization) > 0, \
            "Body type energy_utilization should not be empty"
        
        # Verify at least one of the body type fields contains cause-effect language
        body_content = (
            body_result.metabolic_response.lower() + " " +
            body_result.fat_storage_pattern.lower() + " " +
            body_result.energy_utilization.lower()
        )
        has_cause_effect = any(indicator in body_content for indicator in cause_effect_indicators)
        assert has_cause_effect, \
            f"Body type analysis should explain cause-effect relationships. " \
            f"Expected words like 'affect', 'impact', 'cause', etc. in metabolic_response, " \
            f"fat_storage_pattern, or energy_utilization fields."
