"""Core data models using Pydantic for validation."""

from datetime import datetime, time
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class BodyTypeClassification(str, Enum):
    """Body type classifications."""
    ECTOMORPH = "ectomorph"
    MESOMORPH = "mesomorph"
    ENDOMORPH = "endomorph"
    MIXED = "mixed"


class HabitType(str, Enum):
    """Types of daily habits."""
    EXERCISE = "exercise"
    STRESS = "stress"
    SCREEN_TIME = "screen_time"
    CAFFEINE = "caffeine"
    ALCOHOL = "alcohol"
    OTHER = "other"


class NutritionalInfo(BaseModel):
    """Nutritional information for a food item."""
    calories: float = Field(ge=0, description="Calories per serving")
    protein: float = Field(ge=0, description="Protein in grams")
    carbohydrates: float = Field(ge=0, description="Carbohydrates in grams")
    fat: float = Field(ge=0, description="Fat in grams")
    sodium: float = Field(ge=0, description="Sodium in milligrams")
    sugar: float = Field(ge=0, description="Sugar in grams")
    fiber: float = Field(ge=0, description="Fiber in grams")
    preservatives: List[str] = Field(default_factory=list, description="List of preservatives")
    processing_level: int = Field(ge=1, le=5, description="Processing level from 1 (minimal) to 5 (highly processed)")

    class Config:
        json_schema_extra = {
            "example": {
                "calories": 250,
                "protein": 10,
                "carbohydrates": 30,
                "fat": 8,
                "sodium": 400,
                "sugar": 5,
                "fiber": 3,
                "preservatives": ["sodium benzoate"],
                "processing_level": 3
            }
        }


class FoodItem(BaseModel):
    """Represents a food item with nutritional information."""
    name: str = Field(min_length=1, description="Name of the food item")
    serving_size: float = Field(gt=0, description="Serving size amount")
    unit: str = Field(min_length=1, description="Unit of measurement (g, ml, cup, etc.)")
    nutritional_info: NutritionalInfo

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Whole wheat bread",
                "serving_size": 2,
                "unit": "slices",
                "nutritional_info": {
                    "calories": 160,
                    "protein": 8,
                    "carbohydrates": 28,
                    "fat": 2,
                    "sodium": 300,
                    "sugar": 4,
                    "fiber": 4,
                    "preservatives": [],
                    "processing_level": 2
                }
            }
        }


class SleepData(BaseModel):
    """Sleep data for a specific night."""
    duration: float = Field(ge=0, le=24, description="Sleep duration in hours")
    quality: int = Field(ge=1, le=10, description="Sleep quality rating from 1 (poor) to 10 (excellent)")
    bedtime: time = Field(description="Time went to bed")
    wake_time: time = Field(description="Time woke up")
    interruptions: int = Field(ge=0, description="Number of sleep interruptions")
    timestamp: datetime = Field(default_factory=datetime.now, description="Date of sleep")

    class Config:
        json_schema_extra = {
            "example": {
                "duration": 7.5,
                "quality": 8,
                "bedtime": "22:30:00",
                "wake_time": "06:00:00",
                "interruptions": 1,
                "timestamp": "2024-02-14T06:00:00"
            }
        }


class Habit(BaseModel):
    """Represents a daily habit or activity."""
    type: HabitType
    intensity: int = Field(ge=1, le=10, description="Intensity level from 1 (low) to 10 (high)")
    duration: Optional[float] = Field(None, ge=0, description="Duration in hours")
    timing: Optional[time] = Field(None, description="Time of day for the habit")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "caffeine",
                "intensity": 6,
                "duration": 0.25,
                "timing": "14:00:00",
                "notes": "Coffee after lunch"
            }
        }


class BodyType(BaseModel):
    """Body type information for personalized analysis."""
    classification: BodyTypeClassification
    characteristics: List[str] = Field(default_factory=list, description="Physical characteristics")
    user_id: str = Field(description="User identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "classification": "mesomorph",
                "characteristics": ["athletic build", "moderate metabolism"],
                "user_id": "user-123"
            }
        }


class LifestyleInput(BaseModel):
    """Complete lifestyle input from a user for a specific day."""
    food_items: List[FoodItem] = Field(default_factory=list, description="Foods consumed")
    water_intake: float = Field(ge=0, description="Water intake in milliliters")
    sleep_data: Optional[SleepData] = Field(None, description="Sleep information")
    daily_habits: List[Habit] = Field(default_factory=list, description="Daily habits and activities")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the entry")
    user_id: str = Field(description="User identifier")
    notes: Optional[str] = Field(None, description="Additional notes")

    @field_validator('water_intake')
    @classmethod
    def validate_water_intake(cls, v: float) -> float:
        """Validate water intake is within reasonable range."""
        if v > 10000:  # More than 10 liters seems unreasonable
            raise ValueError("Water intake seems unusually high (>10L)")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "food_items": [],
                "water_intake": 2000,
                "sleep_data": None,
                "daily_habits": [],
                "timestamp": "2024-02-14T12:00:00",
                "user_id": "user-123",
                "notes": "Regular day"
            }
        }


class ValidationError(BaseModel):
    """Represents a validation error."""
    field: str = Field(description="Field that failed validation")
    message: str = Field(description="Error message")
    suggested_fix: str = Field(description="Suggestion for fixing the error")


class ValidationResult(BaseModel):
    """Result of input validation."""
    is_valid: bool = Field(description="Whether the input is valid")
    errors: List[ValidationError] = Field(default_factory=list, description="List of validation errors")
    validated_data: Optional[LifestyleInput] = Field(None, description="Validated data if valid")
