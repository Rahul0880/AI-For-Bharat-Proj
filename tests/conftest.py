"""Pytest configuration and shared fixtures."""

import pytest
from datetime import datetime, time
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


@pytest.fixture
def sample_nutritional_info():
    """Sample nutritional information."""
    return NutritionalInfo(
        calories=250,
        protein=10,
        carbohydrates=30,
        fat=8,
        sodium=400,
        sugar=5,
        fiber=3,
        preservatives=["sodium benzoate"],
        processing_level=3
    )


@pytest.fixture
def sample_food_item(sample_nutritional_info):
    """Sample food item."""
    return FoodItem(
        name="Whole wheat bread",
        serving_size=2,
        unit="slices",
        nutritional_info=sample_nutritional_info
    )


@pytest.fixture
def sample_sleep_data():
    """Sample sleep data."""
    return SleepData(
        duration=7.5,
        quality=8,
        bedtime=time(22, 30),
        wake_time=time(6, 0),
        interruptions=1,
        timestamp=datetime(2024, 2, 14, 6, 0)
    )


@pytest.fixture
def sample_habit():
    """Sample habit."""
    return Habit(
        type=HabitType.CAFFEINE,
        intensity=6,
        duration=0.25,
        timing=time(14, 0),
        notes="Coffee after lunch"
    )


@pytest.fixture
def sample_body_type():
    """Sample body type."""
    return BodyType(
        classification=BodyTypeClassification.MESOMORPH,
        characteristics=["athletic build", "moderate metabolism"],
        user_id="user-123"
    )


@pytest.fixture
def sample_lifestyle_input(sample_food_item, sample_sleep_data, sample_habit):
    """Sample lifestyle input."""
    return LifestyleInput(
        food_items=[sample_food_item],
        water_intake=2000,
        sleep_data=sample_sleep_data,
        daily_habits=[sample_habit],
        timestamp=datetime(2024, 2, 14, 12, 0),
        user_id="user-123",
        notes="Regular day"
    )
