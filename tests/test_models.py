"""Unit tests for core data models."""

import pytest
from datetime import datetime, time
from pydantic import ValidationError as PydanticValidationError

from jeevanfit.models import (
    FoodItem,
    NutritionalInfo,
    SleepData,
    BodyType,
    Habit,
    LifestyleInput,
    BodyTypeClassification,
    HabitType,
)


class TestNutritionalInfo:
    """Tests for NutritionalInfo model."""

    def test_valid_nutritional_info(self):
        """Test creating valid nutritional info."""
        info = NutritionalInfo(
            calories=100,
            protein=5,
            carbohydrates=15,
            fat=3,
            sodium=200,
            sugar=2,
            fiber=1,
            preservatives=[],
            processing_level=1
        )
        assert info.calories == 100
        assert info.processing_level == 1

    def test_negative_values_rejected(self):
        """Test that negative nutritional values are rejected."""
        with pytest.raises(PydanticValidationError):
            NutritionalInfo(
                calories=-100,
                protein=5,
                carbohydrates=15,
                fat=3,
                sodium=200,
                sugar=2,
                fiber=1,
                preservatives=[],
                processing_level=1
            )

    def test_invalid_processing_level(self):
        """Test that processing level outside 1-5 range is rejected."""
        with pytest.raises(PydanticValidationError):
            NutritionalInfo(
                calories=100,
                protein=5,
                carbohydrates=15,
                fat=3,
                sodium=200,
                sugar=2,
                fiber=1,
                preservatives=[],
                processing_level=6
            )


class TestFoodItem:
    """Tests for FoodItem model."""

    def test_valid_food_item(self, sample_nutritional_info):
        """Test creating valid food item."""
        food = FoodItem(
            name="Apple",
            serving_size=1,
            unit="medium",
            nutritional_info=sample_nutritional_info
        )
        assert food.name == "Apple"
        assert food.serving_size == 1

    def test_empty_name_rejected(self, sample_nutritional_info):
        """Test that empty food name is rejected."""
        with pytest.raises(PydanticValidationError):
            FoodItem(
                name="",
                serving_size=1,
                unit="medium",
                nutritional_info=sample_nutritional_info
            )

    def test_zero_serving_size_rejected(self, sample_nutritional_info):
        """Test that zero serving size is rejected."""
        with pytest.raises(PydanticValidationError):
            FoodItem(
                name="Apple",
                serving_size=0,
                unit="medium",
                nutritional_info=sample_nutritional_info
            )


class TestSleepData:
    """Tests for SleepData model."""

    def test_valid_sleep_data(self):
        """Test creating valid sleep data."""
        sleep = SleepData(
            duration=8.0,
            quality=9,
            bedtime=time(22, 0),
            wake_time=time(6, 0),
            interruptions=0,
            timestamp=datetime.now()
        )
        assert sleep.duration == 8.0
        assert sleep.quality == 9

    def test_invalid_duration(self):
        """Test that duration outside 0-24 range is rejected."""
        with pytest.raises(PydanticValidationError):
            SleepData(
                duration=25.0,
                quality=9,
                bedtime=time(22, 0),
                wake_time=time(6, 0),
                interruptions=0,
                timestamp=datetime.now()
            )

    def test_invalid_quality(self):
        """Test that quality outside 1-10 range is rejected."""
        with pytest.raises(PydanticValidationError):
            SleepData(
                duration=8.0,
                quality=11,
                bedtime=time(22, 0),
                wake_time=time(6, 0),
                interruptions=0,
                timestamp=datetime.now()
            )


class TestHabit:
    """Tests for Habit model."""

    def test_valid_habit(self):
        """Test creating valid habit."""
        habit = Habit(
            type=HabitType.EXERCISE,
            intensity=7,
            duration=1.0,
            timing=time(18, 0),
            notes="Evening run"
        )
        assert habit.type == HabitType.EXERCISE
        assert habit.intensity == 7

    def test_invalid_intensity(self):
        """Test that intensity outside 1-10 range is rejected."""
        with pytest.raises(PydanticValidationError):
            Habit(
                type=HabitType.EXERCISE,
                intensity=11,
                duration=1.0
            )


class TestBodyType:
    """Tests for BodyType model."""

    def test_valid_body_type(self):
        """Test creating valid body type."""
        body_type = BodyType(
            classification=BodyTypeClassification.ECTOMORPH,
            characteristics=["lean", "fast metabolism"],
            user_id="user-456"
        )
        assert body_type.classification == BodyTypeClassification.ECTOMORPH
        assert len(body_type.characteristics) == 2


class TestLifestyleInput:
    """Tests for LifestyleInput model."""

    def test_valid_lifestyle_input(self, sample_food_item, sample_sleep_data, sample_habit):
        """Test creating valid lifestyle input."""
        lifestyle = LifestyleInput(
            food_items=[sample_food_item],
            water_intake=2500,
            sleep_data=sample_sleep_data,
            daily_habits=[sample_habit],
            timestamp=datetime.now(),
            user_id="user-789"
        )
        assert len(lifestyle.food_items) == 1
        assert lifestyle.water_intake == 2500

    def test_excessive_water_intake_rejected(self, sample_food_item):
        """Test that excessive water intake is rejected."""
        with pytest.raises(PydanticValidationError):
            LifestyleInput(
                food_items=[sample_food_item],
                water_intake=15000,  # More than 10L
                sleep_data=None,
                daily_habits=[],
                timestamp=datetime.now(),
                user_id="user-789"
            )

    def test_empty_lifestyle_input(self):
        """Test creating lifestyle input with minimal data."""
        lifestyle = LifestyleInput(
            food_items=[],
            water_intake=0,
            sleep_data=None,
            daily_habits=[],
            timestamp=datetime.now(),
            user_id="user-minimal"
        )
        assert len(lifestyle.food_items) == 0
        assert lifestyle.water_intake == 0
