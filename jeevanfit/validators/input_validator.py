"""Input validation and sanitization for JeevanFit."""

import re
from typing import Any, Dict, List
from datetime import datetime
from pydantic import ValidationError as PydanticValidationError

from jeevanfit.models.core import (
    LifestyleInput,
    ValidationResult,
    ValidationError,
    FoodItem,
    SleepData,
    Habit
)


class InputValidator:
    """Validates and sanitizes user lifestyle inputs."""
    
    # Patterns for detecting potential injection attacks
    INJECTION_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers
        r'(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)',  # SQL keywords
        r'(\|\||&&|;|\$\()',  # Shell injection
    ]
    
    def __init__(self):
        """Initialize the InputValidator."""
        self.injection_regex = re.compile('|'.join(self.INJECTION_PATTERNS), re.IGNORECASE)
    
    def validate_input(self, input_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate lifestyle input for completeness and consistency.
        
        Args:
            input_data: Dictionary containing lifestyle input data
            
        Returns:
            ValidationResult with validation status and any errors
            
        Requirements: 6.1, 6.2
        """
        errors: List[ValidationError] = []
        
        # Check for required fields
        required_fields = ['user_id', 'water_intake']
        for field in required_fields:
            if field not in input_data or input_data[field] is None:
                errors.append(ValidationError(
                    field=field,
                    message=f"Required field '{field}' is missing",
                    suggested_fix=f"Please provide a value for '{field}'"
                ))
        
        # Check for at least some meaningful data
        has_food = input_data.get('food_items') and len(input_data.get('food_items', [])) > 0
        has_sleep = input_data.get('sleep_data') is not None
        has_habits = input_data.get('daily_habits') and len(input_data.get('daily_habits', [])) > 0
        
        if not (has_food or has_sleep or has_habits):
            errors.append(ValidationError(
                field='general',
                message="Input must contain at least one of: food items, sleep data, or daily habits",
                suggested_fix="Please provide food items, sleep information, or daily habits to analyze"
            ))
        
        # If there are basic validation errors, return early
        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                validated_data=None
            )
        
        # Try to parse with Pydantic for detailed validation
        try:
            lifestyle_input = LifestyleInput(**input_data)
            
            # Additional consistency checks
            consistency_errors = self._check_consistency(lifestyle_input)
            if consistency_errors:
                errors.extend(consistency_errors)
                return ValidationResult(
                    is_valid=False,
                    errors=errors,
                    validated_data=None
                )
            
            return ValidationResult(
                is_valid=True,
                errors=[],
                validated_data=lifestyle_input
            )
            
        except PydanticValidationError as e:
            # Convert Pydantic validation errors to our format
            for error in e.errors():
                field_path = '.'.join(str(loc) for loc in error['loc'])
                errors.append(ValidationError(
                    field=field_path,
                    message=error['msg'],
                    suggested_fix=self._get_fix_suggestion(field_path, error)
                ))
            
            return ValidationResult(
                is_valid=False,
                errors=errors,
                validated_data=None
            )
    
    def sanitize_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize and normalize input data.
        
        Args:
            input_data: Raw input data dictionary
            
        Returns:
            Sanitized input data dictionary
            
        Requirements: 6.1, 6.2
        """
        sanitized = input_data.copy()
        
        # Sanitize string fields recursively
        sanitized = self._sanitize_strings(sanitized)
        
        # Normalize numeric values
        if 'water_intake' in sanitized and sanitized['water_intake'] is not None:
            sanitized['water_intake'] = float(sanitized['water_intake'])
        
        # Ensure timestamp is present
        if 'timestamp' not in sanitized or sanitized['timestamp'] is None:
            sanitized['timestamp'] = datetime.now().isoformat()
        
        # Normalize food items
        if 'food_items' in sanitized and sanitized['food_items']:
            sanitized['food_items'] = [
                self._sanitize_food_item(item) for item in sanitized['food_items']
            ]
        
        # Normalize habits
        if 'daily_habits' in sanitized and sanitized['daily_habits']:
            sanitized['daily_habits'] = [
                self._sanitize_habit(habit) for habit in sanitized['daily_habits']
            ]
        
        return sanitized
    
    def _check_consistency(self, lifestyle_input: LifestyleInput) -> List[ValidationError]:
        """
        Check for logical consistency in the input data.
        
        Args:
            lifestyle_input: Validated LifestyleInput object
            
        Returns:
            List of consistency validation errors
        """
        errors: List[ValidationError] = []
        
        # Check sleep data consistency
        if lifestyle_input.sleep_data:
            sleep = lifestyle_input.sleep_data
            
            # Check if duration matches bedtime/wake time difference
            # (This is a simplified check - real implementation would handle day boundaries)
            if sleep.duration > 24:
                errors.append(ValidationError(
                    field='sleep_data.duration',
                    message='Sleep duration cannot exceed 24 hours',
                    suggested_fix='Please provide a sleep duration between 0 and 24 hours'
                ))
            
            # Check quality vs interruptions consistency
            if sleep.quality >= 8 and sleep.interruptions > 5:
                errors.append(ValidationError(
                    field='sleep_data',
                    message='High sleep quality (8+) with many interruptions (>5) seems inconsistent',
                    suggested_fix='Please verify sleep quality rating or number of interruptions'
                ))
        
        # Check for duplicate food items (potential data entry error)
        if lifestyle_input.food_items:
            food_names = [item.name.lower().strip() for item in lifestyle_input.food_items]
            if len(food_names) != len(set(food_names)):
                errors.append(ValidationError(
                    field='food_items',
                    message='Duplicate food items detected',
                    suggested_fix='If you consumed the same food multiple times, consider combining them or adding notes to distinguish'
                ))
            
            # Check for extreme nutritional values
            for idx, item in enumerate(lifestyle_input.food_items):
                if item.nutritional_info:
                    nutritional = item.nutritional_info
                    
                    # Check for unrealistic calorie values
                    if nutritional.calories > 5000:
                        errors.append(ValidationError(
                            field=f'food_items[{idx}].nutritional_info.calories',
                            message=f'Calorie value {nutritional.calories} is unrealistically high for a single food item',
                            suggested_fix='Please verify the calorie value is correct (typical range: 0-5000 per serving)'
                        ))
                    
                    # Check for unrealistic protein values
                    if nutritional.protein > 200:
                        errors.append(ValidationError(
                            field=f'food_items[{idx}].nutritional_info.protein',
                            message=f'Protein value {nutritional.protein}g is unrealistically high for a single food item',
                            suggested_fix='Please verify the protein value is correct (typical range: 0-200g per serving)'
                        ))
                    
                    # Check for unrealistic carbohydrate values
                    if nutritional.carbohydrates > 500:
                        errors.append(ValidationError(
                            field=f'food_items[{idx}].nutritional_info.carbohydrates',
                            message=f'Carbohydrate value {nutritional.carbohydrates}g is unrealistically high for a single food item',
                            suggested_fix='Please verify the carbohydrate value is correct (typical range: 0-500g per serving)'
                        ))
                    
                    # Check for unrealistic fat values
                    if nutritional.fat > 200:
                        errors.append(ValidationError(
                            field=f'food_items[{idx}].nutritional_info.fat',
                            message=f'Fat value {nutritional.fat}g is unrealistically high for a single food item',
                            suggested_fix='Please verify the fat value is correct (typical range: 0-200g per serving)'
                        ))
                    
                    # Check for unrealistic sodium values
                    if nutritional.sodium > 5000:
                        errors.append(ValidationError(
                            field=f'food_items[{idx}].nutritional_info.sodium',
                            message=f'Sodium value {nutritional.sodium}mg is unrealistically high for a single food item',
                            suggested_fix='Please verify the sodium value is correct (typical range: 0-5000mg per serving)'
                        ))
        
        return errors
    
    def _sanitize_strings(self, data: Any) -> Any:
        """
        Recursively sanitize string values in data structure.
        
        Args:
            data: Data to sanitize (can be dict, list, str, or other)
            
        Returns:
            Sanitized data
        """
        if isinstance(data, dict):
            return {key: self._sanitize_strings(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_strings(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data
    
    def _sanitize_string(self, value: str) -> str:
        """
        Sanitize a single string value.
        
        Args:
            value: String to sanitize
            
        Returns:
            Sanitized string
        """
        # Strip leading/trailing whitespace
        sanitized = value.strip()
        
        # Remove potential injection patterns
        if self.injection_regex.search(sanitized):
            # Remove matched patterns
            sanitized = self.injection_regex.sub('', sanitized)
        
        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    def _sanitize_food_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize a food item dictionary.
        
        Args:
            item: Food item dictionary
            
        Returns:
            Sanitized food item dictionary
        """
        sanitized = item.copy()
        
        # Ensure name is sanitized
        if 'name' in sanitized:
            sanitized['name'] = self._sanitize_string(str(sanitized['name']))
        
        # Ensure numeric values are properly typed
        if 'serving_size' in sanitized:
            sanitized['serving_size'] = float(sanitized['serving_size'])
        
        # Sanitize nutritional info
        if 'nutritional_info' in sanitized:
            nutritional = sanitized['nutritional_info']
            for key in ['calories', 'protein', 'carbohydrates', 'fat', 'sodium', 'sugar', 'fiber']:
                if key in nutritional:
                    nutritional[key] = float(nutritional[key])
            
            if 'processing_level' in nutritional:
                nutritional['processing_level'] = int(nutritional['processing_level'])
            
            if 'preservatives' in nutritional and isinstance(nutritional['preservatives'], list):
                nutritional['preservatives'] = [
                    self._sanitize_string(str(p)) for p in nutritional['preservatives']
                ]
        
        return sanitized
    
    def _sanitize_habit(self, habit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize a habit dictionary.
        
        Args:
            habit: Habit dictionary
            
        Returns:
            Sanitized habit dictionary
        """
        sanitized = habit.copy()
        
        # Ensure intensity is an integer
        if 'intensity' in sanitized:
            sanitized['intensity'] = int(sanitized['intensity'])
        
        # Ensure duration is a float if present
        if 'duration' in sanitized and sanitized['duration'] is not None:
            sanitized['duration'] = float(sanitized['duration'])
        
        # Sanitize notes if present
        if 'notes' in sanitized and sanitized['notes'] is not None:
            sanitized['notes'] = self._sanitize_string(str(sanitized['notes']))
        
        return sanitized
    
    def _get_fix_suggestion(self, field: str, error: Dict[str, Any]) -> str:
        """
        Generate a helpful fix suggestion based on the validation error.
        
        Args:
            field: Field that failed validation
            error: Pydantic error dictionary
            
        Returns:
            Suggested fix message
        """
        error_type = error.get('type', '')
        
        if 'missing' in error_type:
            return f"Please provide a value for '{field}'"
        elif 'type_error' in error_type:
            expected_type = error.get('type', 'correct type')
            return f"Please provide a valid {expected_type} for '{field}'"
        elif 'value_error' in error_type:
            if 'greater_than' in error_type:
                return f"Please provide a value greater than the minimum for '{field}'"
            elif 'less_than' in error_type:
                return f"Please provide a value less than the maximum for '{field}'"
            else:
                return f"Please provide a valid value for '{field}'"
        else:
            return f"Please check the value for '{field}' and ensure it meets the requirements"
