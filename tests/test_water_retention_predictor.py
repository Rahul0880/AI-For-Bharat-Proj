"""Unit tests for WaterRetentionPredictor."""

import pytest
from datetime import datetime, time

from jeevanfit.analyzers import (
    WaterRetentionPredictor,
    RetentionLevel,
    RetentionFactorType
)
from jeevanfit.models import (
    LifestyleInput,
    FoodItem,
    NutritionalInfo,
    SleepData,
    BodyType,
    BodyTypeClassification,
    Habit,
    HabitType
)


class TestWaterRetentionPredictor:
    """Test suite for WaterRetentionPredictor class."""
    
    @pytest.fixture
    def predictor(self):
        """Create a WaterRetentionPredictor instance."""
        return WaterRetentionPredictor()
    
    @pytest.fixture
    def base_lifestyle(self):
        """Create a base lifestyle input with neutral values."""
        return LifestyleInput(
            food_items=[],
            water_intake=2500,  # Optimal
            sleep_data=SleepData(
                duration=8.0,
                quality=8,
                bedtime=time(22, 0),
                wake_time=time(6, 0),
                interruptions=0,
                timestamp=datetime.now()
            ),
            daily_habits=[],
            user_id="test-user",
            timestamp=datetime.now()
        )
    
    @pytest.fixture
    def mesomorph_body_type(self):
        """Create a mesomorph body type."""
        return BodyType(
            classification=BodyTypeClassification.MESOMORPH,
            characteristics=["athletic build", "moderate metabolism"],
            user_id="test-user"
        )
    
    def test_predict_retention_low_level(self, predictor, base_lifestyle, mesomorph_body_type):
        """Test prediction with optimal conditions results in LOW retention."""
        prediction = predictor.predict_retention(base_lifestyle, mesomorph_body_type)
        
        assert prediction.level == RetentionLevel.LOW
        assert prediction.confidence >= 60
        assert prediction.confidence <= 100
        assert len(prediction.contributing_factors) >= 0
        assert prediction.explanation
    
    def test_predict_retention_high_sodium(self, predictor, base_lifestyle, mesomorph_body_type):
        """Test prediction with high sodium results in higher retention."""
        # Add high sodium food
        high_sodium_food = FoodItem(
            name="Salty snack",
            serving_size=100,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=400,
                protein=5,
                carbohydrates=50,
                fat=20,
                sodium=2500,  # Very high
                sugar=5,
                fiber=2,
                preservatives=[],
                processing_level=4
            )
        )
        base_lifestyle.food_items.append(high_sodium_food)
        
        prediction = predictor.predict_retention(base_lifestyle, mesomorph_body_type)
        
        # Should have moderate or high retention
        assert prediction.level in [RetentionLevel.MODERATE, RetentionLevel.HIGH]
        
        # Sodium should be a contributing factor
        factor_types = [f.type for f in prediction.contributing_factors]
        assert RetentionFactorType.SODIUM in factor_types
    
    def test_predict_retention_low_hydration(self, predictor, base_lifestyle, mesomorph_body_type):
        """Test prediction with low water intake."""
        base_lifestyle.water_intake = 1000  # Low
        
        prediction = predictor.predict_retention(base_lifestyle, mesomorph_body_type)
        
        # Should have some retention factors
        factor_types = [f.type for f in prediction.contributing_factors]
        assert RetentionFactorType.HYDRATION in factor_types
    
    def test_predict_retention_poor_sleep(self, predictor, base_lifestyle, mesomorph_body_type):
        """Test prediction with poor sleep quality."""
        base_lifestyle.sleep_data.quality = 3  # Poor
        base_lifestyle.sleep_data.duration = 5.0  # Short
        
        prediction = predictor.predict_retention(base_lifestyle, mesomorph_body_type)
        
        # Should have sleep as a contributing factor
        factor_types = [f.type for f in prediction.contributing_factors]
        assert RetentionFactorType.SLEEP in factor_types
    
    def test_predict_retention_high_stress(self, predictor, base_lifestyle, mesomorph_body_type):
        """Test prediction with high stress."""
        stress_habit = Habit(
            type=HabitType.STRESS,
            intensity=9,  # High stress
            duration=4.0,
            timing=time(14, 0),
            notes="Work deadline"
        )
        base_lifestyle.daily_habits.append(stress_habit)
        
        prediction = predictor.predict_retention(base_lifestyle, mesomorph_body_type)
        
        # Should have stress as a contributing factor
        factor_types = [f.type for f in prediction.contributing_factors]
        assert RetentionFactorType.STRESS in factor_types
    
    def test_predict_retention_multiple_factors(self, predictor, base_lifestyle, mesomorph_body_type):
        """Test prediction with multiple contributing factors."""
        # Add high sodium
        high_sodium_food = FoodItem(
            name="Processed meal",
            serving_size=300,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=600,
                protein=20,
                carbohydrates=60,
                fat=25,
                sodium=2000,
                sugar=10,
                fiber=3,
                preservatives=["sodium benzoate"],
                processing_level=4
            )
        )
        base_lifestyle.food_items.append(high_sodium_food)
        
        # Add poor sleep
        base_lifestyle.sleep_data.quality = 4
        base_lifestyle.sleep_data.duration = 5.5
        
        # Add stress
        base_lifestyle.daily_habits.append(
            Habit(type=HabitType.STRESS, intensity=8, duration=3.0)
        )
        
        prediction = predictor.predict_retention(base_lifestyle, mesomorph_body_type)
        
        # Should have HIGH retention with multiple factors
        assert prediction.level == RetentionLevel.HIGH
        assert len(prediction.contributing_factors) >= 2
        assert prediction.primary_factor is not None
    
    def test_body_type_sensitivity_endomorph(self, predictor, base_lifestyle):
        """Test that endomorph body type increases retention sensitivity."""
        # Add moderate sodium
        moderate_sodium_food = FoodItem(
            name="Food",
            serving_size=200,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=300,
                protein=15,
                carbohydrates=40,
                fat=10,
                sodium=1600,
                sugar=5,
                fiber=4,
                preservatives=[],
                processing_level=2
            )
        )
        base_lifestyle.food_items.append(moderate_sodium_food)
        
        # Test with mesomorph (normal sensitivity)
        mesomorph = BodyType(
            classification=BodyTypeClassification.MESOMORPH,
            characteristics=[],
            user_id="test-user"
        )
        prediction_meso = predictor.predict_retention(base_lifestyle, mesomorph)
        
        # Test with endomorph (higher sensitivity)
        endomorph = BodyType(
            classification=BodyTypeClassification.ENDOMORPH,
            characteristics=[],
            user_id="test-user"
        )
        prediction_endo = predictor.predict_retention(base_lifestyle, endomorph)
        
        # Endomorph should have same or higher retention level
        retention_order = {
            RetentionLevel.LOW: 0,
            RetentionLevel.MODERATE: 1,
            RetentionLevel.HIGH: 2
        }
        assert retention_order[prediction_endo.level] >= retention_order[prediction_meso.level]
    
    def test_analyze_retention_factors_returns_list(self, predictor, base_lifestyle):
        """Test that analyze_retention_factors returns a list."""
        factors = predictor.analyze_retention_factors(base_lifestyle)
        
        assert isinstance(factors, list)
        # With optimal conditions, should have few or no factors
        assert len(factors) >= 0
    
    def test_analyze_retention_factors_sorted_by_impact(self, predictor, base_lifestyle):
        """Test that factors are sorted by impact (highest first)."""
        # Add multiple factors with different impacts
        high_sodium_food = FoodItem(
            name="Salty food",
            serving_size=100,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=300,
                protein=10,
                carbohydrates=30,
                fat=15,
                sodium=2200,  # High impact
                sugar=5,
                fiber=2,
                preservatives=[],
                processing_level=3
            )
        )
        base_lifestyle.food_items.append(high_sodium_food)
        base_lifestyle.water_intake = 1200  # Moderate impact
        
        factors = predictor.analyze_retention_factors(base_lifestyle)
        
        # Should be sorted by impact descending
        if len(factors) > 1:
            for i in range(len(factors) - 1):
                assert factors[i].impact >= factors[i + 1].impact
    
    def test_primary_factor_identification(self, predictor, base_lifestyle, mesomorph_body_type):
        """Test that primary factor is correctly identified."""
        # Add high sodium (should be primary)
        high_sodium_food = FoodItem(
            name="Very salty food",
            serving_size=150,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=400,
                protein=12,
                carbohydrates=45,
                fat=18,
                sodium=2800,  # Very high
                sugar=8,
                fiber=3,
                preservatives=[],
                processing_level=4
            )
        )
        base_lifestyle.food_items.append(high_sodium_food)
        
        # Add low water (lower impact)
        base_lifestyle.water_intake = 1400
        
        prediction = predictor.predict_retention(base_lifestyle, mesomorph_body_type)
        
        # Primary factor should be sodium (highest impact)
        assert prediction.primary_factor.type == RetentionFactorType.SODIUM
        assert prediction.primary_factor.impact >= 2
    
    def test_prediction_without_exercise_data(self, predictor, base_lifestyle, mesomorph_body_type):
        """Test that prediction works without exercise data (Requirement 2.1)."""
        # Ensure no exercise habits
        base_lifestyle.daily_habits = [
            h for h in base_lifestyle.daily_habits
            if h.type != HabitType.EXERCISE
        ]
        
        # Should still generate valid prediction
        prediction = predictor.predict_retention(base_lifestyle, mesomorph_body_type)
        
        assert prediction.level in [RetentionLevel.LOW, RetentionLevel.MODERATE, RetentionLevel.HIGH]
        assert prediction.confidence > 0
        assert prediction.explanation
    
    def test_prediction_with_no_sleep_data(self, predictor, mesomorph_body_type):
        """Test prediction when sleep data is missing."""
        lifestyle = LifestyleInput(
            food_items=[],
            water_intake=2500,
            sleep_data=None,  # No sleep data
            daily_habits=[],
            user_id="test-user",
            timestamp=datetime.now()
        )
        
        prediction = predictor.predict_retention(lifestyle, mesomorph_body_type)
        
        # Should still work, just without sleep factor
        assert prediction.level in [RetentionLevel.LOW, RetentionLevel.MODERATE, RetentionLevel.HIGH]
        factor_types = [f.type for f in prediction.contributing_factors]
        assert RetentionFactorType.SLEEP not in factor_types
    
    def test_very_high_water_intake(self, predictor, base_lifestyle, mesomorph_body_type):
        """Test prediction with very high water intake."""
        base_lifestyle.water_intake = 5000  # Very high
        
        prediction = predictor.predict_retention(base_lifestyle, mesomorph_body_type)
        
        # Should have hydration as a factor
        factor_types = [f.type for f in prediction.contributing_factors]
        assert RetentionFactorType.HYDRATION in factor_types
    
    def test_retention_factor_has_recommendation(self, predictor, base_lifestyle):
        """Test that all retention factors include recommendations."""
        # Add high sodium to generate a factor
        high_sodium_food = FoodItem(
            name="Salty food",
            serving_size=100,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=300,
                protein=10,
                carbohydrates=30,
                fat=15,
                sodium=2100,
                sugar=5,
                fiber=2,
                preservatives=[],
                processing_level=3
            )
        )
        base_lifestyle.food_items.append(high_sodium_food)
        
        factors = predictor.analyze_retention_factors(base_lifestyle)
        
        # All factors should have recommendations
        for factor in factors:
            assert factor.recommendation
            assert len(factor.recommendation) > 0
    
    def test_confidence_calculation(self, predictor, base_lifestyle, mesomorph_body_type):
        """Test that confidence is within valid range."""
        prediction = predictor.predict_retention(base_lifestyle, mesomorph_body_type)
        
        assert 0 <= prediction.confidence <= 100
        assert prediction.confidence >= 60  # Minimum confidence threshold
