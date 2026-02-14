"""Food classification analyzer for JeevanFit."""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field

from jeevanfit.models.core import FoodItem, NutritionalInfo


class FoodCategory(str, Enum):
    """Food classification categories."""
    HEALTHY = "healthy"
    JUNK = "junk"
    PRESERVATIVE_HEAVY = "preservative_heavy"


class FSIParameters(BaseModel):
    """FSI/ISO-style nutritional parameters for food classification."""
    nutrient_density: float = Field(description="Nutrient density score (0-1)")
    processing_score: float = Field(description="Processing level score (0-1)")
    preservative_load: float = Field(description="Preservative load score (0-1)")
    sugar_content: float = Field(description="Sugar content score (0-1)")
    sodium_level: float = Field(description="Sodium level score (0-1)")


class FoodClassification(BaseModel):
    """Result of food classification."""
    category: FoodCategory = Field(description="Classification category")
    confidence: float = Field(ge=0, le=100, description="Confidence percentage")
    rationale: str = Field(description="Explanation of classification")
    dominant_factors: List[str] = Field(description="Key factors influencing classification")


class FoodClassifier:
    """Classifies food items based on FSI/ISO-style parameters."""
    
    # Classification thresholds
    NUTRIENT_DENSITY_HEALTHY_THRESHOLD = 0.7
    NUTRIENT_DENSITY_JUNK_THRESHOLD = 0.3
    PROCESSING_HEALTHY_MAX = 2
    PROCESSING_JUNK_MIN = 4
    PRESERVATIVE_COUNT_THRESHOLD = 3
    SUGAR_JUNK_THRESHOLD = 15  # grams per serving
    SODIUM_JUNK_THRESHOLD = 600  # mg per serving
    
    def classify_food(self, food_item: FoodItem) -> FoodClassification:
        """
        Classify a food item as healthy, junk, or preservative-heavy.
        
        Args:
            food_item: The food item to classify
            
        Returns:
            FoodClassification with category, confidence, rationale, and dominant factors
        """
        # Extract FSI parameters
        fsi_params = self.get_fsi_parameters(food_item)
        
        # Calculate scores for each category
        scores = self._calculate_category_scores(food_item, fsi_params)
        
        # Select dominant category
        category = self._select_dominant_category(scores, food_item)
        
        # Generate rationale and identify dominant factors
        rationale, dominant_factors = self._generate_rationale(
            category, food_item, fsi_params, scores
        )
        
        # Calculate confidence based on score separation
        confidence = self._calculate_confidence(scores, category)
        
        return FoodClassification(
            category=category,
            confidence=confidence,
            rationale=rationale,
            dominant_factors=dominant_factors
        )
    
    def get_fsi_parameters(self, food_item: FoodItem) -> FSIParameters:
        """
        Extract FSI/ISO-style nutritional parameters from a food item.
        
        Args:
            food_item: The food item to analyze
            
        Returns:
            FSIParameters with calculated scores
        """
        nutrition = food_item.nutritional_info
        
        # Calculate nutrient density (protein + fiber) / calories
        # Higher is better
        nutrient_density = 0.0
        if nutrition.calories > 1.0:  # Avoid division by very small numbers
            nutrient_value = nutrition.protein + nutrition.fiber
            nutrient_density = min(1.0, nutrient_value / (nutrition.calories / 100))
        
        # Processing score: normalize processing_level (1-5) to (0-1)
        # Lower is better, so invert: (5 - level) / 4
        processing_score = (5 - nutrition.processing_level) / 4.0
        
        # Preservative load: based on count and presence
        # Higher count = higher load (worse)
        preservative_count = len(nutrition.preservatives)
        preservative_load = min(1.0, preservative_count / 5.0)
        
        # Sugar content score: normalize to 0-1 scale
        # Higher sugar = higher score (worse)
        sugar_content = min(1.0, nutrition.sugar / 30.0)
        
        # Sodium level score: normalize to 0-1 scale
        # Higher sodium = higher score (worse)
        sodium_level = min(1.0, nutrition.sodium / 1000.0)
        
        return FSIParameters(
            nutrient_density=nutrient_density,
            processing_score=processing_score,
            preservative_load=preservative_load,
            sugar_content=sugar_content,
            sodium_level=sodium_level
        )
    
    def _calculate_category_scores(
        self, food_item: FoodItem, fsi_params: FSIParameters
    ) -> dict:
        """Calculate scores for each category."""
        nutrition = food_item.nutritional_info
        
        # Healthy score: high nutrient density, low processing, low preservatives
        healthy_score = (
            fsi_params.nutrient_density * 0.4 +
            fsi_params.processing_score * 0.3 +
            (1 - fsi_params.preservative_load) * 0.15 +
            (1 - fsi_params.sugar_content) * 0.075 +
            (1 - fsi_params.sodium_level) * 0.075
        )
        
        # Junk score: high calories/sugar/sodium, low nutrients, high processing
        junk_score = (
            (1 - fsi_params.nutrient_density) * 0.3 +
            (1 - fsi_params.processing_score) * 0.3 +
            fsi_params.sugar_content * 0.2 +
            fsi_params.sodium_level * 0.2
        )
        
        # Preservative-heavy score: primarily based on preservative count
        preservative_score = fsi_params.preservative_load
        
        # Apply hard thresholds
        if len(nutrition.preservatives) >= self.PRESERVATIVE_COUNT_THRESHOLD:
            preservative_score = max(preservative_score, 0.8)
        
        if nutrition.processing_level >= self.PROCESSING_JUNK_MIN:
            junk_score = max(junk_score, 0.7)
        
        if nutrition.sugar > self.SUGAR_JUNK_THRESHOLD:
            junk_score = max(junk_score, 0.6)
        
        if nutrition.sodium > self.SODIUM_JUNK_THRESHOLD:
            junk_score = max(junk_score, 0.6)
        
        return {
            FoodCategory.HEALTHY: healthy_score,
            FoodCategory.JUNK: junk_score,
            FoodCategory.PRESERVATIVE_HEAVY: preservative_score
        }
    
    def _select_dominant_category(
        self, scores: dict, food_item: FoodItem
    ) -> FoodCategory:
        """
        Select the dominant category based on threshold scores.
        Defaults to more cautious category when ambiguous.
        """
        nutrition = food_item.nutritional_info
        
        # Check for preservative-heavy first (highest priority)
        if len(nutrition.preservatives) >= self.PRESERVATIVE_COUNT_THRESHOLD:
            return FoodCategory.PRESERVATIVE_HEAVY
        
        if scores[FoodCategory.PRESERVATIVE_HEAVY] >= 0.6:
            return FoodCategory.PRESERVATIVE_HEAVY
        
        # Find category with highest score
        max_category = max(scores, key=scores.get)
        max_score = scores[max_category]
        
        # If ambiguous (scores close), default to more cautious category
        # Order of caution: JUNK > PRESERVATIVE_HEAVY > HEALTHY
        score_threshold = 0.15  # If scores within 0.15, consider ambiguous
        
        if max_category == FoodCategory.HEALTHY:
            # Check if junk score is close
            if abs(scores[FoodCategory.JUNK] - max_score) < score_threshold:
                return FoodCategory.JUNK  # More cautious
        
        return max_category
    
    def _generate_rationale(
        self,
        category: FoodCategory,
        food_item: FoodItem,
        fsi_params: FSIParameters,
        scores: dict
    ) -> tuple[str, List[str]]:
        """Generate rationale and identify dominant factors."""
        nutrition = food_item.nutritional_info
        dominant_factors = []
        
        if category == FoodCategory.HEALTHY:
            rationale_parts = []
            
            if fsi_params.nutrient_density >= self.NUTRIENT_DENSITY_HEALTHY_THRESHOLD:
                rationale_parts.append("high nutrient density")
                dominant_factors.append("nutrient_density")
            
            if nutrition.processing_level <= self.PROCESSING_HEALTHY_MAX:
                rationale_parts.append("minimal processing")
                dominant_factors.append("low_processing")
            
            if len(nutrition.preservatives) == 0:
                rationale_parts.append("no preservatives")
                dominant_factors.append("no_preservatives")
            
            if nutrition.fiber >= 3:
                rationale_parts.append("good fiber content")
                dominant_factors.append("fiber")
            
            rationale = f"Classified as healthy due to {', '.join(rationale_parts)}."
            
        elif category == FoodCategory.JUNK:
            rationale_parts = []
            
            if nutrition.sugar > self.SUGAR_JUNK_THRESHOLD:
                rationale_parts.append(f"high sugar content ({nutrition.sugar}g)")
                dominant_factors.append("high_sugar")
            
            if nutrition.sodium > self.SODIUM_JUNK_THRESHOLD:
                rationale_parts.append(f"high sodium ({nutrition.sodium}mg)")
                dominant_factors.append("high_sodium")
            
            if nutrition.processing_level >= self.PROCESSING_JUNK_MIN:
                rationale_parts.append("highly processed")
                dominant_factors.append("high_processing")
            
            if fsi_params.nutrient_density < self.NUTRIENT_DENSITY_JUNK_THRESHOLD:
                rationale_parts.append("low nutritional value")
                dominant_factors.append("low_nutrients")
            
            rationale = f"Classified as junk food due to {', '.join(rationale_parts)}."
            
        else:  # PRESERVATIVE_HEAVY
            preservative_count = len(nutrition.preservatives)
            preservative_list = ", ".join(nutrition.preservatives[:3])
            if preservative_count > 3:
                preservative_list += f", and {preservative_count - 3} more"
            
            rationale = (
                f"Classified as preservative-heavy due to {preservative_count} "
                f"preservatives detected: {preservative_list}."
            )
            dominant_factors.append("preservatives")
            
            if nutrition.processing_level >= self.PROCESSING_JUNK_MIN:
                dominant_factors.append("high_processing")
        
        # Ensure we have at least one dominant factor
        if not dominant_factors:
            dominant_factors.append("overall_composition")
        
        return rationale, dominant_factors
    
    def _calculate_confidence(self, scores: dict, category: FoodCategory) -> float:
        """Calculate confidence based on score separation."""
        category_score = scores[category]
        other_scores = [s for c, s in scores.items() if c != category]
        
        if not other_scores:
            return 95.0
        
        max_other_score = max(other_scores)
        separation = category_score - max_other_score
        
        # Map separation to confidence (0.0-0.5 separation -> 60-95% confidence)
        confidence = 60 + (separation * 70)
        return min(95.0, max(60.0, confidence))
