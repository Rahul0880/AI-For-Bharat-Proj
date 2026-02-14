"""Property-based tests for BodyTypeAnalyzer using Hypothesis."""

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
    BodyTypeAnalyzer,
    MetabolicRate,
    MetabolicProfile,
    NutritionalNeeds,
    BodyTypeInsight,
    BodyTypeRecommendation,
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


class TestBodyTypeAnalyzerProperties:
    """Property-based tests for BodyTypeAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = BodyTypeAnalyzer()
    
    # Feature: fitbuddy-lifestyle-assistant, Property 14: Body type insight completeness
    @given(
        body_type=body_type_strategy(),
        lifestyle=lifestyle_input_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_insight_completeness(self, body_type, lifestyle):
        """
        Property 14: Body type insight completeness
        For any body type and lifestyle input, the analysis should explain 
        all three aspects: metabolism effects, fat storage patterns, and 
        energy level impacts.
        
        Validates: Requirements 4.1
        """
        # Analyze body type
        insight = self.analyzer.analyze_body_type(body_type, lifestyle)
        
        # Verify insight is not None
        assert insight is not None, "Insight should not be None"
        
        # Verify insight is a BodyTypeInsight instance
        assert isinstance(insight, BodyTypeInsight), \
            f"Insight must be a BodyTypeInsight, got {type(insight)}"
        
        # 1. Verify metabolic response is present and non-empty
        assert insight.metabolic_response is not None, \
            "Metabolic response should not be None"
        assert isinstance(insight.metabolic_response, str), \
            f"Metabolic response must be a string, got {type(insight.metabolic_response)}"
        assert len(insight.metabolic_response) > 0, \
            "Metabolic response should not be empty"
        assert len(insight.metabolic_response) > 20, \
            f"Metabolic response should be substantive (>20 chars), got {len(insight.metabolic_response)} chars"
        
        # 2. Verify fat storage pattern is present and non-empty
        assert insight.fat_storage_pattern is not None, \
            "Fat storage pattern should not be None"
        assert isinstance(insight.fat_storage_pattern, str), \
            f"Fat storage pattern must be a string, got {type(insight.fat_storage_pattern)}"
        assert len(insight.fat_storage_pattern) > 0, \
            "Fat storage pattern should not be empty"
        assert len(insight.fat_storage_pattern) > 20, \
            f"Fat storage pattern should be substantive (>20 chars), got {len(insight.fat_storage_pattern)} chars"
        
        # 3. Verify energy utilization is present and non-empty
        assert insight.energy_utilization is not None, \
            "Energy utilization should not be None"
        assert isinstance(insight.energy_utilization, str), \
            f"Energy utilization must be a string, got {type(insight.energy_utilization)}"
        assert len(insight.energy_utilization) > 0, \
            "Energy utilization should not be empty"
        assert len(insight.energy_utilization) > 20, \
            f"Energy utilization should be substantive (>20 chars), got {len(insight.energy_utilization)} chars"
        
        # Verify all three aspects are distinct (not the same text)
        assert insight.metabolic_response != insight.fat_storage_pattern, \
            "Metabolic response and fat storage pattern should be different"
        assert insight.metabolic_response != insight.energy_utilization, \
            "Metabolic response and energy utilization should be different"
        assert insight.fat_storage_pattern != insight.energy_utilization, \
            "Fat storage pattern and energy utilization should be different"
        
        # Verify nutritional needs are present
        assert insight.nutritional_needs is not None, \
            "Nutritional needs should not be None"
        
        # Verify recommendations are present
        assert insight.lifestyle_recommendations is not None, \
            "Lifestyle recommendations should not be None"
        assert isinstance(insight.lifestyle_recommendations, list), \
            "Lifestyle recommendations must be a list"

    # Feature: fitbuddy-lifestyle-assistant, Property 15: Body type personalization
    @given(lifestyle=lifestyle_input_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_body_type_personalization(self, lifestyle):
        """
        Property 15: Body type personalization
        For any identical lifestyle input analyzed with different body types, 
        the resulting insights and recommendations should differ in meaningful 
        ways reflecting metabolic differences.
        
        Validates: Requirements 4.2, 4.4
        """
        # Create body types for each classification
        ectomorph = BodyType(
            classification=BodyTypeClassification.ECTOMORPH,
            characteristics=["fast metabolism", "lean build"],
            user_id="test-user-ecto"
        )
        
        mesomorph = BodyType(
            classification=BodyTypeClassification.MESOMORPH,
            characteristics=["athletic build", "moderate metabolism"],
            user_id="test-user-meso"
        )
        
        endomorph = BodyType(
            classification=BodyTypeClassification.ENDOMORPH,
            characteristics=["slower metabolism", "higher fat storage"],
            user_id="test-user-endo"
        )
        
        # Analyze the same lifestyle with different body types
        ecto_insight = self.analyzer.analyze_body_type(ectomorph, lifestyle)
        meso_insight = self.analyzer.analyze_body_type(mesomorph, lifestyle)
        endo_insight = self.analyzer.analyze_body_type(endomorph, lifestyle)
        
        # Verify all insights are valid
        assert ecto_insight is not None, "Ectomorph insight should not be None"
        assert meso_insight is not None, "Mesomorph insight should not be None"
        assert endo_insight is not None, "Endomorph insight should not be None"
        
        # 1. Verify metabolic responses differ
        assert ecto_insight.metabolic_response != meso_insight.metabolic_response, \
            "Ectomorph and mesomorph should have different metabolic responses"
        assert ecto_insight.metabolic_response != endo_insight.metabolic_response, \
            "Ectomorph and endomorph should have different metabolic responses"
        assert meso_insight.metabolic_response != endo_insight.metabolic_response, \
            "Mesomorph and endomorph should have different metabolic responses"
        
        # 2. Verify fat storage patterns differ
        assert ecto_insight.fat_storage_pattern != meso_insight.fat_storage_pattern, \
            "Ectomorph and mesomorph should have different fat storage patterns"
        assert ecto_insight.fat_storage_pattern != endo_insight.fat_storage_pattern, \
            "Ectomorph and endomorph should have different fat storage patterns"
        assert meso_insight.fat_storage_pattern != endo_insight.fat_storage_pattern, \
            "Mesomorph and endomorph should have different fat storage patterns"
        
        # 3. Verify energy utilization differs
        assert ecto_insight.energy_utilization != meso_insight.energy_utilization, \
            "Ectomorph and mesomorph should have different energy utilization"
        assert ecto_insight.energy_utilization != endo_insight.energy_utilization, \
            "Ectomorph and endomorph should have different energy utilization"
        assert meso_insight.energy_utilization != endo_insight.energy_utilization, \
            "Mesomorph and endomorph should have different energy utilization"
        
        # 4. Verify nutritional needs differ meaningfully
        ecto_ratios = (
            ecto_insight.nutritional_needs.protein_ratio,
            ecto_insight.nutritional_needs.carb_ratio,
            ecto_insight.nutritional_needs.fat_ratio
        )
        meso_ratios = (
            meso_insight.nutritional_needs.protein_ratio,
            meso_insight.nutritional_needs.carb_ratio,
            meso_insight.nutritional_needs.fat_ratio
        )
        endo_ratios = (
            endo_insight.nutritional_needs.protein_ratio,
            endo_insight.nutritional_needs.carb_ratio,
            endo_insight.nutritional_needs.fat_ratio
        )
        
        assert ecto_ratios != meso_ratios, \
            "Ectomorph and mesomorph should have different macronutrient ratios"
        assert ecto_ratios != endo_ratios, \
            "Ectomorph and endomorph should have different macronutrient ratios"
        assert meso_ratios != endo_ratios, \
            "Mesomorph and endomorph should have different macronutrient ratios"
        
        # 5. Verify recommendations differ
        ecto_actions = {rec.action for rec in ecto_insight.lifestyle_recommendations}
        meso_actions = {rec.action for rec in meso_insight.lifestyle_recommendations}
        endo_actions = {rec.action for rec in endo_insight.lifestyle_recommendations}
        
        assert ecto_actions != meso_actions or ecto_actions != endo_actions or meso_actions != endo_actions, \
            "At least some recommendations should differ across body types"
        
        # 6. Verify metabolic profiles differ
        ecto_profile = self.analyzer.get_metabolic_profile(ectomorph)
        meso_profile = self.analyzer.get_metabolic_profile(mesomorph)
        endo_profile = self.analyzer.get_metabolic_profile(endomorph)
        
        assert ecto_profile.base_metabolic_rate == MetabolicRate.FAST, \
            "Ectomorph should have fast metabolic rate"
        assert meso_profile.base_metabolic_rate == MetabolicRate.MODERATE, \
            "Mesomorph should have moderate metabolic rate"
        assert endo_profile.base_metabolic_rate == MetabolicRate.SLOW, \
            "Endomorph should have slow metabolic rate"
        
        assert ecto_profile.carb_sensitivity != endo_profile.carb_sensitivity, \
            "Ectomorph and endomorph should have different carb sensitivity"
        
        assert ecto_profile.fat_storage_tendency != endo_profile.fat_storage_tendency, \
            "Ectomorph and endomorph should have different fat storage tendencies"
        
        assert ecto_profile.fat_storage_tendency < endo_profile.fat_storage_tendency, \
            "Ectomorph should have lower fat storage tendency than endomorph"
        
        assert ecto_profile.carb_sensitivity < endo_profile.carb_sensitivity, \
            "Ectomorph should have lower carb sensitivity than endomorph"

    # Feature: fitbuddy-lifestyle-assistant, Property 16: Nutritional needs inclusion
    @given(
        body_type=body_type_strategy(),
        lifestyle=lifestyle_input_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_nutritional_needs_inclusion(self, body_type, lifestyle):
        """
        Property 16: Nutritional needs inclusion
        For any body type analysis, the result should include specific 
        nutritional needs guidance including macronutrient ratios or meal 
        frequency recommendations.
        
        Validates: Requirements 4.3
        """
        # Analyze body type
        insight = self.analyzer.analyze_body_type(body_type, lifestyle)
        
        # Verify insight is not None
        assert insight is not None, "Insight should not be None"
        
        # Verify nutritional needs are present
        assert insight.nutritional_needs is not None, \
            "Nutritional needs should not be None"
        
        # Verify nutritional needs is a NutritionalNeeds instance
        assert isinstance(insight.nutritional_needs, NutritionalNeeds), \
            f"Nutritional needs must be a NutritionalNeeds instance, got {type(insight.nutritional_needs)}"
        
        # 1. Verify macronutrient ratios are present and valid
        # Protein ratio
        assert insight.nutritional_needs.protein_ratio is not None, \
            "Protein ratio should not be None"
        assert isinstance(insight.nutritional_needs.protein_ratio, (int, float)), \
            f"Protein ratio must be numeric, got {type(insight.nutritional_needs.protein_ratio)}"
        assert 0 <= insight.nutritional_needs.protein_ratio <= 100, \
            f"Protein ratio must be between 0 and 100, got {insight.nutritional_needs.protein_ratio}"
        assert insight.nutritional_needs.protein_ratio > 0, \
            "Protein ratio should be greater than 0 (must include some protein)"
        
        # Carb ratio
        assert insight.nutritional_needs.carb_ratio is not None, \
            "Carb ratio should not be None"
        assert isinstance(insight.nutritional_needs.carb_ratio, (int, float)), \
            f"Carb ratio must be numeric, got {type(insight.nutritional_needs.carb_ratio)}"
        assert 0 <= insight.nutritional_needs.carb_ratio <= 100, \
            f"Carb ratio must be between 0 and 100, got {insight.nutritional_needs.carb_ratio}"
        assert insight.nutritional_needs.carb_ratio > 0, \
            "Carb ratio should be greater than 0 (must include some carbs)"
        
        # Fat ratio
        assert insight.nutritional_needs.fat_ratio is not None, \
            "Fat ratio should not be None"
        assert isinstance(insight.nutritional_needs.fat_ratio, (int, float)), \
            f"Fat ratio must be numeric, got {type(insight.nutritional_needs.fat_ratio)}"
        assert 0 <= insight.nutritional_needs.fat_ratio <= 100, \
            f"Fat ratio must be between 0 and 100, got {insight.nutritional_needs.fat_ratio}"
        assert insight.nutritional_needs.fat_ratio > 0, \
            "Fat ratio should be greater than 0 (must include some fat)"
        
        # Verify ratios sum to 100 (or close to it, allowing for rounding)
        total_ratio = (
            insight.nutritional_needs.protein_ratio +
            insight.nutritional_needs.carb_ratio +
            insight.nutritional_needs.fat_ratio
        )
        assert 99 <= total_ratio <= 101, \
            f"Macronutrient ratios should sum to approximately 100%, got {total_ratio}%"
        
        # 2. Verify meal frequency recommendation is present and non-empty
        assert insight.nutritional_needs.meal_frequency is not None, \
            "Meal frequency should not be None"
        assert isinstance(insight.nutritional_needs.meal_frequency, str), \
            f"Meal frequency must be a string, got {type(insight.nutritional_needs.meal_frequency)}"
        assert len(insight.nutritional_needs.meal_frequency) > 0, \
            "Meal frequency should not be empty"
        assert len(insight.nutritional_needs.meal_frequency) > 5, \
            f"Meal frequency should be substantive (>5 chars), got {len(insight.nutritional_needs.meal_frequency)} chars"
        
        # Verify meal frequency contains numeric information (e.g., "3-4 meals")
        assert any(char.isdigit() for char in insight.nutritional_needs.meal_frequency), \
            f"Meal frequency should include numeric guidance, got: {insight.nutritional_needs.meal_frequency}"
        
        # 3. Verify hydration guidance is present and non-empty
        assert insight.nutritional_needs.hydration_guidance is not None, \
            "Hydration guidance should not be None"
        assert isinstance(insight.nutritional_needs.hydration_guidance, str), \
            f"Hydration guidance must be a string, got {type(insight.nutritional_needs.hydration_guidance)}"
        assert len(insight.nutritional_needs.hydration_guidance) > 0, \
            "Hydration guidance should not be empty"
        assert len(insight.nutritional_needs.hydration_guidance) > 10, \
            f"Hydration guidance should be substantive (>10 chars), got {len(insight.nutritional_needs.hydration_guidance)} chars"
        
        # Verify hydration guidance contains numeric information (e.g., "2-3 liters")
        assert any(char.isdigit() for char in insight.nutritional_needs.hydration_guidance), \
            f"Hydration guidance should include numeric recommendations, got: {insight.nutritional_needs.hydration_guidance}"
        
        # 4. Verify nutritional needs are body-type specific
        # Get metabolic profile to verify consistency
        metabolic_profile = self.analyzer.get_metabolic_profile(body_type)
        
        # For ectomorphs (fast metabolism), carb ratio should be higher
        if body_type.classification == BodyTypeClassification.ECTOMORPH:
            assert insight.nutritional_needs.carb_ratio >= 50, \
                f"Ectomorphs should have higher carb ratio (>=50%), got {insight.nutritional_needs.carb_ratio}%"
        
        # For endomorphs (slow metabolism), protein ratio should be higher, carb ratio lower
        if body_type.classification == BodyTypeClassification.ENDOMORPH:
            assert insight.nutritional_needs.protein_ratio >= 30, \
                f"Endomorphs should have higher protein ratio (>=30%), got {insight.nutritional_needs.protein_ratio}%"
            assert insight.nutritional_needs.carb_ratio <= 30, \
                f"Endomorphs should have lower carb ratio (<=30%), got {insight.nutritional_needs.carb_ratio}%"
        
        # 5. Verify all nutritional guidance is specific and actionable
        # Check that the guidance is not generic placeholder text
        assert "TODO" not in insight.nutritional_needs.meal_frequency.upper(), \
            "Meal frequency should not contain placeholder text"
        assert "TODO" not in insight.nutritional_needs.hydration_guidance.upper(), \
            "Hydration guidance should not contain placeholder text"
        
        # Verify guidance is specific (contains concrete numbers or ranges)
        # Meal frequency should mention specific meal counts
        meal_keywords = ["meal", "time", "day", "frequent"]
        assert any(keyword in insight.nutritional_needs.meal_frequency.lower() for keyword in meal_keywords), \
            f"Meal frequency should mention meals or timing, got: {insight.nutritional_needs.meal_frequency}"
        
        # Hydration guidance should mention water or hydration
        hydration_keywords = ["water", "liter", "hydrat", "fluid", "ml"]
        assert any(keyword in insight.nutritional_needs.hydration_guidance.lower() for keyword in hydration_keywords), \
            f"Hydration guidance should mention water or hydration, got: {insight.nutritional_needs.hydration_guidance}"
