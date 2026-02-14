"""Property-based tests for WaterRetentionPredictor using Hypothesis."""

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
    WaterRetentionPredictor,
    RetentionLevel,
    RetentionFactorType,
    RetentionFactor,
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


# Strategy for generating non-exercise habits
@st.composite
def non_exercise_habit_strategy(draw):
    """Generate valid Habit instances excluding exercise."""
    habit_type = draw(st.sampled_from([
        HabitType.STRESS,
        HabitType.SCREEN_TIME,
        HabitType.CAFFEINE,
        HabitType.ALCOHOL,
        HabitType.OTHER
    ]))
    
    return Habit(
        type=habit_type,
        intensity=draw(st.integers(min_value=1, max_value=10)),
        duration=draw(st.floats(min_value=0.1, max_value=8.0)),
        timing=time(draw(st.integers(min_value=6, max_value=22)), 
                   draw(st.integers(min_value=0, max_value=59))),
        notes=draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', max_size=50))
    )


# Strategy for generating lifestyle input WITHOUT exercise
@st.composite
def lifestyle_without_exercise_strategy(draw):
    """Generate valid LifestyleInput instances without exercise habits."""
    # Generate food items
    food_items = draw(st.lists(food_item_strategy(), min_size=0, max_size=5))
    
    # Generate water intake
    water_intake = draw(st.floats(min_value=500, max_value=5000))
    
    # Optionally include sleep data
    sleep_data = draw(st.one_of(st.none(), sleep_data_strategy()))
    
    # Generate non-exercise habits only
    daily_habits = draw(st.lists(non_exercise_habit_strategy(), min_size=0, max_size=5))
    
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


class TestWaterRetentionPredictorProperties:
    """Property-based tests for WaterRetentionPredictor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.predictor = WaterRetentionPredictor()
    
    # Feature: fitbuddy-lifestyle-assistant, Property 5: Retention prediction without exercise
    @given(
        lifestyle=lifestyle_without_exercise_strategy(),
        body_type=body_type_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_prediction_without_exercise(self, lifestyle, body_type):
        """
        Property 5: Retention prediction without exercise
        For any lifestyle input that excludes exercise data, the water 
        retention predictor should still generate a valid prediction with 
        confidence level.
        
        Validates: Requirements 2.1
        """
        # Verify no exercise habits are present
        exercise_habits = [h for h in lifestyle.daily_habits if h.type == HabitType.EXERCISE]
        assert len(exercise_habits) == 0, "Test data should not contain exercise habits"
        
        # Make prediction
        prediction = self.predictor.predict_retention(lifestyle, body_type)
        
        # Verify prediction is valid
        assert prediction is not None, "Prediction should not be None"
        
        # Verify retention level is valid
        valid_levels = {RetentionLevel.LOW, RetentionLevel.MODERATE, RetentionLevel.HIGH}
        assert prediction.level in valid_levels, \
            f"Invalid retention level: {prediction.level}. Must be one of {valid_levels}"
        
        # Verify confidence is present and within valid range
        assert prediction.confidence is not None, "Confidence should not be None"
        assert 0 <= prediction.confidence <= 100, \
            f"Confidence must be between 0 and 100, got {prediction.confidence}"
        
        # Verify prediction has an explanation
        assert prediction.explanation is not None, "Explanation should not be None"
        assert len(prediction.explanation) > 0, "Explanation should not be empty"
        
        # Verify primary factor is present
        assert prediction.primary_factor is not None, "Primary factor should not be None"
        assert isinstance(prediction.primary_factor.type, RetentionFactorType), \
            "Primary factor type must be a RetentionFactorType enum"
        
        # Verify contributing factors is a list
        assert isinstance(prediction.contributing_factors, list), \
            "Contributing factors must be a list"
        
        # Verify all contributing factors are valid
        for factor in prediction.contributing_factors:
            assert isinstance(factor.type, RetentionFactorType), \
                f"Factor type must be RetentionFactorType, got {type(factor.type)}"
            assert 1 <= factor.impact <= 10, \
                f"Factor impact must be between 1 and 10, got {factor.impact}"
            assert factor.description, "Factor description should not be empty"
            assert factor.recommendation, "Factor recommendation should not be empty"
    
    # Feature: fitbuddy-lifestyle-assistant, Property 6: Multi-factor retention influence
    @given(body_type=body_type_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_multi_factor_influence(self, body_type):
        """
        Property 6: Multi-factor retention influence
        For any lifestyle input, varying sodium content, hydration level, or 
        sleep quality independently should result in different retention 
        predictions, demonstrating all factors are considered.
        
        Validates: Requirements 2.2
        """
        # Create a controlled baseline with minimal factors
        baseline_lifestyle = LifestyleInput(
            food_items=[
                FoodItem(
                    name="low sodium food",
                    serving_size=100,
                    unit="g",
                    nutritional_info=NutritionalInfo(
                        calories=200,
                        protein=10,
                        carbohydrates=30,
                        fat=5,
                        sodium=200,  # Low sodium
                        sugar=3,
                        fiber=5,
                        preservatives=[],
                        processing_level=1
                    )
                )
            ],
            water_intake=2500,  # Optimal water
            sleep_data=SleepData(
                duration=8.0,  # Good duration
                quality=8,  # Good quality
                bedtime=time(22, 0),
                wake_time=time(6, 0),
                interruptions=0,
                timestamp=datetime.now()
            ),
            daily_habits=[],
            timestamp=datetime.now(),
            user_id="test-user",
            notes=""
        )
        
        baseline_prediction = self.predictor.predict_retention(baseline_lifestyle, body_type)
        baseline_factors = self.predictor.analyze_retention_factors(baseline_lifestyle)
        
        # Test 1: Vary sodium content significantly
        high_sodium_lifestyle = LifestyleInput(
            food_items=[
                FoodItem(
                    name="high sodium food",
                    serving_size=100,
                    unit="g",
                    nutritional_info=NutritionalInfo(
                        calories=200,
                        protein=10,
                        carbohydrates=30,
                        fat=5,
                        sodium=2500,  # Very high sodium
                        sugar=3,
                        fiber=5,
                        preservatives=[],
                        processing_level=1
                    )
                )
            ],
            water_intake=2500,  # Same water
            sleep_data=baseline_lifestyle.sleep_data,  # Same sleep
            daily_habits=[],
            timestamp=datetime.now(),
            user_id="test-user",
            notes=""
        )
        
        sodium_prediction = self.predictor.predict_retention(high_sodium_lifestyle, body_type)
        sodium_factors = self.predictor.analyze_retention_factors(high_sodium_lifestyle)
        
        # Verify sodium factor is present in high sodium case
        sodium_factor_types = [f.type for f in sodium_factors]
        assert RetentionFactorType.SODIUM in sodium_factor_types, \
            "High sodium should create a sodium retention factor"
        
        # Verify predictions differ (level, factors, or confidence)
        sodium_differs = (
            sodium_prediction.level != baseline_prediction.level or
            len(sodium_factors) != len(baseline_factors) or
            abs(sodium_prediction.confidence - baseline_prediction.confidence) > 5
        )
        assert sodium_differs, \
            "Varying sodium from 200mg to 2500mg should affect retention prediction"
        
        # Test 2: Vary hydration level significantly
        low_hydration_lifestyle = LifestyleInput(
            food_items=baseline_lifestyle.food_items,  # Same food
            water_intake=1000,  # Very low water
            sleep_data=baseline_lifestyle.sleep_data,  # Same sleep
            daily_habits=[],
            timestamp=datetime.now(),
            user_id="test-user",
            notes=""
        )
        
        hydration_prediction = self.predictor.predict_retention(low_hydration_lifestyle, body_type)
        hydration_factors = self.predictor.analyze_retention_factors(low_hydration_lifestyle)
        
        # Verify hydration factor is present in low hydration case
        hydration_factor_types = [f.type for f in hydration_factors]
        assert RetentionFactorType.HYDRATION in hydration_factor_types, \
            "Low hydration should create a hydration retention factor"
        
        # Verify predictions differ
        hydration_differs = (
            hydration_prediction.level != baseline_prediction.level or
            len(hydration_factors) != len(baseline_factors) or
            abs(hydration_prediction.confidence - baseline_prediction.confidence) > 5
        )
        assert hydration_differs, \
            "Varying water intake from 2500ml to 1000ml should affect retention prediction"
        
        # Test 3: Vary sleep quality significantly
        poor_sleep_lifestyle = LifestyleInput(
            food_items=baseline_lifestyle.food_items,  # Same food
            water_intake=2500,  # Same water
            sleep_data=SleepData(
                duration=5.0,  # Poor duration
                quality=3,  # Poor quality
                bedtime=time(22, 0),
                wake_time=time(3, 0),
                interruptions=5,
                timestamp=datetime.now()
            ),
            daily_habits=[],
            timestamp=datetime.now(),
            user_id="test-user",
            notes=""
        )
        
        sleep_prediction = self.predictor.predict_retention(poor_sleep_lifestyle, body_type)
        sleep_factors = self.predictor.analyze_retention_factors(poor_sleep_lifestyle)
        
        # Verify sleep factor is present in poor sleep case
        sleep_factor_types = [f.type for f in sleep_factors]
        assert RetentionFactorType.SLEEP in sleep_factor_types, \
            "Poor sleep should create a sleep retention factor"
        
        # Verify predictions differ
        sleep_differs = (
            sleep_prediction.level != baseline_prediction.level or
            len(sleep_factors) != len(baseline_factors) or
            abs(sleep_prediction.confidence - baseline_prediction.confidence) > 5
        )
        assert sleep_differs, \
            "Varying sleep quality from good (8/10, 8h) to poor (3/10, 5h) should affect retention prediction"
    
    # Feature: fitbuddy-lifestyle-assistant, Property 7: Primary factor identification
    @given(
        lifestyle=lifestyle_without_exercise_strategy(),
        body_type=body_type_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_primary_factor_identification(self, lifestyle, body_type):
        """
        Property 7: Primary factor identification
        For any water retention prediction, the result should identify exactly 
        one primary contributing factor from the set of analyzed factors.
        
        Validates: Requirements 2.5
        """
        # Make prediction
        prediction = self.predictor.predict_retention(lifestyle, body_type)
        
        # Verify prediction has a primary factor
        assert prediction.primary_factor is not None, \
            "Prediction must have a primary factor"
        
        # Verify primary factor is a valid RetentionFactor
        assert isinstance(prediction.primary_factor, RetentionFactor), \
            f"Primary factor must be a RetentionFactor, got {type(prediction.primary_factor)}"
        
        # Verify primary factor has a valid type
        assert isinstance(prediction.primary_factor.type, RetentionFactorType), \
            f"Primary factor type must be RetentionFactorType, got {type(prediction.primary_factor.type)}"
        
        # Verify primary factor has valid impact
        assert 1 <= prediction.primary_factor.impact <= 10, \
            f"Primary factor impact must be between 1 and 10, got {prediction.primary_factor.impact}"
        
        # Verify primary factor has description and recommendation
        assert prediction.primary_factor.description, \
            "Primary factor must have a non-empty description"
        assert prediction.primary_factor.recommendation, \
            "Primary factor must have a non-empty recommendation"
        
        # Verify there is exactly ONE primary factor (not multiple)
        # The primary factor should be in the contributing factors list
        contributing_factors = prediction.contributing_factors
        
        # If there are contributing factors, verify primary factor is among them
        # or is the only factor when no other factors exist
        if contributing_factors:
            # Primary factor should be the one with highest impact
            max_impact = max(f.impact for f in contributing_factors)
            primary_candidates = [f for f in contributing_factors if f.impact == max_impact]
            
            # Verify the primary factor matches one of the highest impact factors
            assert prediction.primary_factor.type in [f.type for f in primary_candidates], \
                "Primary factor should be one of the factors with highest impact"
            
            # Verify primary factor impact matches the maximum
            assert prediction.primary_factor.impact == max_impact, \
                f"Primary factor impact ({prediction.primary_factor.impact}) should match " \
                f"maximum impact ({max_impact}) from contributing factors"
        
        # Verify exactly one primary factor is identified (not a list)
        # This is implicit in the data structure, but we verify it's not None
        # and is a single RetentionFactor object
        assert not isinstance(prediction.primary_factor, list), \
            "Primary factor should be a single RetentionFactor, not a list"
    
    # Feature: fitbuddy-lifestyle-assistant, Property 8: Valid retention levels
    @given(
        lifestyle=lifestyle_without_exercise_strategy(),
        body_type=body_type_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_valid_retention_levels(self, lifestyle, body_type):
        """
        Property 8: Valid retention levels
        For any lifestyle input, the retention prediction should return one of 
        the valid levels: LOW, MODERATE, or HIGH.
        
        Validates: Requirements 2.4
        """
        # Make prediction
        prediction = self.predictor.predict_retention(lifestyle, body_type)
        
        # Verify prediction is not None
        assert prediction is not None, "Prediction should not be None"
        
        # Verify level is present
        assert prediction.level is not None, "Retention level should not be None"
        
        # Define the set of valid retention levels
        valid_levels = {RetentionLevel.LOW, RetentionLevel.MODERATE, RetentionLevel.HIGH}
        
        # Verify the prediction level is one of the valid levels
        assert prediction.level in valid_levels, \
            f"Retention level must be one of {[level.value for level in valid_levels]}, " \
            f"but got {prediction.level}"
        
        # Verify the level is a RetentionLevel enum instance
        assert isinstance(prediction.level, RetentionLevel), \
            f"Retention level must be a RetentionLevel enum, got {type(prediction.level)}"
        
        # Verify the level value is a valid string
        assert prediction.level.value in ["low", "moderate", "high"], \
            f"Retention level value must be 'low', 'moderate', or 'high', " \
            f"got '{prediction.level.value}'"
