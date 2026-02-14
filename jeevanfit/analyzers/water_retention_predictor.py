"""Water retention prediction analyzer for JeevanFit."""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field

from jeevanfit.models.core import LifestyleInput, BodyType, BodyTypeClassification, HabitType


class RetentionLevel(str, Enum):
    """Water retention level classifications."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class RetentionFactorType(str, Enum):
    """Types of factors contributing to water retention."""
    SODIUM = "sodium"
    HYDRATION = "hydration"
    SLEEP = "sleep"
    HORMONAL = "hormonal"
    STRESS = "stress"


class RetentionFactor(BaseModel):
    """Individual factor contributing to water retention."""
    type: RetentionFactorType = Field(description="Type of retention factor")
    impact: int = Field(ge=1, le=10, description="Impact score from 1 (low) to 10 (high)")
    description: str = Field(description="Description of the factor's influence")
    recommendation: str = Field(description="Recommendation to address this factor")


class RetentionPrediction(BaseModel):
    """Result of water retention prediction."""
    level: RetentionLevel = Field(description="Predicted retention level")
    confidence: float = Field(ge=0, le=100, description="Confidence percentage")
    primary_factor: RetentionFactor = Field(description="Primary contributing factor")
    contributing_factors: List[RetentionFactor] = Field(description="All contributing factors")
    explanation: str = Field(description="Explanation of the prediction")


class WaterRetentionPredictor:
    """Predicts water retention based on lifestyle factors."""
    
    # Thresholds for scoring
    HIGH_SODIUM_THRESHOLD = 2000  # mg per day
    MODERATE_SODIUM_THRESHOLD = 1500  # mg per day
    LOW_WATER_THRESHOLD = 1500  # ml per day
    OPTIMAL_WATER_MIN = 2000  # ml per day
    OPTIMAL_WATER_MAX = 3500  # ml per day
    VERY_HIGH_WATER_THRESHOLD = 4500  # ml per day
    POOR_SLEEP_QUALITY_THRESHOLD = 5  # quality score
    POOR_SLEEP_DURATION_THRESHOLD = 6  # hours
    HIGH_STRESS_INTENSITY = 7  # intensity score
    
    # Body type sensitivity multipliers
    BODY_TYPE_SENSITIVITY = {
        BodyTypeClassification.ECTOMORPH: 0.8,  # Less sensitive to retention
        BodyTypeClassification.MESOMORPH: 1.0,  # Normal sensitivity
        BodyTypeClassification.ENDOMORPH: 1.3,  # More sensitive to retention
        BodyTypeClassification.MIXED: 1.1,  # Slightly more sensitive
    }
    
    def predict_retention(
        self, lifestyle: LifestyleInput, body_type: BodyType
    ) -> RetentionPrediction:
        """
        Predict water retention level based on lifestyle factors.
        
        Args:
            lifestyle: User's lifestyle input data
            body_type: User's body type information
            
        Returns:
            RetentionPrediction with level, factors, and explanation
        """
        # Analyze all retention factors
        factors = self.analyze_retention_factors(lifestyle)
        
        # Calculate total retention score
        total_score = sum(factor.impact for factor in factors)
        
        # Apply body type sensitivity adjustment
        sensitivity = self.BODY_TYPE_SENSITIVITY.get(
            body_type.classification, 1.0
        )
        adjusted_score = total_score * sensitivity
        
        # Determine retention level based on adjusted score
        if adjusted_score <= 2:
            level = RetentionLevel.LOW
        elif adjusted_score <= 5:
            level = RetentionLevel.MODERATE
        else:
            level = RetentionLevel.HIGH
        
        # Identify primary factor (highest impact)
        # If no factors, create a neutral factor indicating optimal conditions
        if factors:
            primary_factor = max(factors, key=lambda f: f.impact)
        else:
            primary_factor = RetentionFactor(
                type=RetentionFactorType.HYDRATION,
                impact=1,  # Minimum valid impact
                description="All lifestyle factors are within optimal ranges.",
                recommendation="Continue maintaining your current healthy habits."
            )
        
        # Generate explanation
        explanation = self._generate_explanation(
            level, primary_factor, factors, body_type, adjusted_score
        )
        
        # Calculate confidence based on factor clarity
        confidence = self._calculate_confidence(factors, adjusted_score)
        
        return RetentionPrediction(
            level=level,
            confidence=confidence,
            primary_factor=primary_factor,
            contributing_factors=factors,
            explanation=explanation
        )
    
    def analyze_retention_factors(
        self, lifestyle: LifestyleInput
    ) -> List[RetentionFactor]:
        """
        Analyze individual factors contributing to water retention.
        
        Args:
            lifestyle: User's lifestyle input data
            
        Returns:
            List of RetentionFactor objects ranked by impact
        """
        factors = []
        
        # Calculate sodium factor
        sodium_factor = self._calculate_sodium_factor(lifestyle)
        if sodium_factor:
            factors.append(sodium_factor)
        
        # Calculate hydration factor
        hydration_factor = self._calculate_hydration_factor(lifestyle)
        if hydration_factor:
            factors.append(hydration_factor)
        
        # Calculate sleep factor
        sleep_factor = self._calculate_sleep_factor(lifestyle)
        if sleep_factor:
            factors.append(sleep_factor)
        
        # Calculate stress factor
        stress_factor = self._calculate_stress_factor(lifestyle)
        if stress_factor:
            factors.append(stress_factor)
        
        # Sort by impact (highest first)
        factors.sort(key=lambda f: f.impact, reverse=True)
        
        return factors
    
    def _calculate_sodium_factor(
        self, lifestyle: LifestyleInput
    ) -> RetentionFactor | None:
        """Calculate sodium contribution to water retention."""
        # Sum sodium from all food items
        total_sodium = sum(
            item.nutritional_info.sodium for item in lifestyle.food_items
        )
        
        if total_sodium >= self.HIGH_SODIUM_THRESHOLD:
            impact = 3  # High impact
            description = (
                f"High sodium intake ({total_sodium:.0f}mg) significantly "
                "increases water retention as your body holds water to dilute sodium."
            )
            recommendation = (
                "Reduce sodium intake by choosing fresh foods over processed ones, "
                "avoiding added salt, and reading nutrition labels carefully."
            )
        elif total_sodium >= self.MODERATE_SODIUM_THRESHOLD:
            impact = 2  # Moderate impact
            description = (
                f"Moderate sodium intake ({total_sodium:.0f}mg) may contribute "
                "to some water retention."
            )
            recommendation = (
                "Consider reducing sodium intake slightly by limiting processed foods "
                "and using herbs and spices for flavor instead of salt."
            )
        else:
            impact = 0  # Low/no impact
            description = (
                f"Sodium intake ({total_sodium:.0f}mg) is within healthy range "
                "and unlikely to cause significant water retention."
            )
            recommendation = "Continue maintaining balanced sodium intake."
        
        # Only return factor if it has meaningful impact
        if impact > 0:
            return RetentionFactor(
                type=RetentionFactorType.SODIUM,
                impact=impact,
                description=description,
                recommendation=recommendation
            )
        return None
    
    def _calculate_hydration_factor(
        self, lifestyle: LifestyleInput
    ) -> RetentionFactor | None:
        """Calculate hydration contribution to water retention."""
        water_intake = lifestyle.water_intake
        
        if water_intake < self.LOW_WATER_THRESHOLD:
            impact = 2  # Moderate impact
            description = (
                f"Low water intake ({water_intake:.0f}ml) may cause your body "
                "to retain water as a protective mechanism."
            )
            recommendation = (
                "Gradually increase water intake to 2000-3000ml per day. "
                "Drink water consistently throughout the day."
            )
        elif water_intake > self.VERY_HIGH_WATER_THRESHOLD:
            impact = 1  # Low impact
            description = (
                f"Very high water intake ({water_intake:.0f}ml) may contribute "
                "to slight water retention, though this is less common."
            )
            recommendation = (
                "Consider moderating water intake to 2000-3500ml per day unless "
                "advised otherwise by a healthcare provider."
            )
        elif water_intake < self.OPTIMAL_WATER_MIN:
            impact = 1  # Low impact
            description = (
                f"Water intake ({water_intake:.0f}ml) is slightly below optimal "
                "and may contribute minimally to retention."
            )
            recommendation = (
                "Try to increase water intake slightly to reach 2000ml per day."
            )
        else:
            # Optimal range - no factor returned
            return None
        
        return RetentionFactor(
            type=RetentionFactorType.HYDRATION,
            impact=impact,
            description=description,
            recommendation=recommendation
        )
    
    def _calculate_sleep_factor(
        self, lifestyle: LifestyleInput
    ) -> RetentionFactor | None:
        """Calculate sleep contribution to water retention."""
        if not lifestyle.sleep_data:
            return None
        
        sleep = lifestyle.sleep_data
        poor_quality = sleep.quality <= self.POOR_SLEEP_QUALITY_THRESHOLD
        poor_duration = sleep.duration < self.POOR_SLEEP_DURATION_THRESHOLD
        
        if poor_quality and poor_duration:
            impact = 2  # Moderate impact
            description = (
                f"Poor sleep quality ({sleep.quality}/10) and insufficient duration "
                f"({sleep.duration:.1f}h) disrupt hormonal balance, leading to "
                "increased water retention."
            )
            recommendation = (
                "Prioritize 7-9 hours of quality sleep. Establish a consistent "
                "bedtime routine and create a comfortable sleep environment."
            )
        elif poor_quality:
            impact = 2  # Moderate impact
            description = (
                f"Poor sleep quality ({sleep.quality}/10) can disrupt hormones "
                "that regulate fluid balance, contributing to water retention."
            )
            recommendation = (
                "Focus on improving sleep quality through better sleep hygiene, "
                "reducing screen time before bed, and managing stress."
            )
        elif poor_duration:
            impact = 1  # Low impact
            description = (
                f"Insufficient sleep duration ({sleep.duration:.1f}h) may affect "
                "fluid regulation hormones."
            )
            recommendation = (
                "Aim for 7-9 hours of sleep per night to support healthy "
                "hormonal balance."
            )
        else:
            # Good sleep - no factor returned
            return None
        
        return RetentionFactor(
            type=RetentionFactorType.SLEEP,
            impact=impact,
            description=description,
            recommendation=recommendation
        )
    
    def _calculate_stress_factor(
        self, lifestyle: LifestyleInput
    ) -> RetentionFactor | None:
        """Calculate stress contribution to water retention."""
        # Find stress habits
        stress_habits = [
            h for h in lifestyle.daily_habits
            if h.type == HabitType.STRESS
        ]
        
        if not stress_habits:
            return None
        
        # Use highest stress intensity
        max_stress = max(h.intensity for h in stress_habits)
        
        if max_stress >= self.HIGH_STRESS_INTENSITY:
            impact = 2  # Moderate impact (1-2 points)
            description = (
                f"High stress levels (intensity {max_stress}/10) trigger cortisol "
                "release, which can increase water retention and bloating."
            )
            recommendation = (
                "Practice stress management techniques such as meditation, "
                "deep breathing, regular exercise, or talking to a counselor."
            )
        elif max_stress >= 5:
            impact = 1  # Low impact
            description = (
                f"Moderate stress levels (intensity {max_stress}/10) may "
                "contribute slightly to water retention through cortisol."
            )
            recommendation = (
                "Consider incorporating stress-reduction activities into your "
                "daily routine, such as walking, yoga, or mindfulness."
            )
        else:
            # Low stress - no factor returned
            return None
        
        return RetentionFactor(
            type=RetentionFactorType.STRESS,
            impact=impact,
            description=description,
            recommendation=recommendation
        )
    
    def _generate_explanation(
        self,
        level: RetentionLevel,
        primary_factor: RetentionFactor,
        all_factors: List[RetentionFactor],
        body_type: BodyType,
        adjusted_score: float
    ) -> str:
        """Generate comprehensive explanation of the prediction."""
        # Start with level assessment
        level_descriptions = {
            RetentionLevel.LOW: "low water retention",
            RetentionLevel.MODERATE: "moderate water retention",
            RetentionLevel.HIGH: "high water retention"
        }
        
        explanation_parts = [
            f"Based on your lifestyle factors, you are experiencing "
            f"{level_descriptions[level]}."
        ]
        
        # Add primary factor
        explanation_parts.append(
            f"The primary contributing factor is {primary_factor.type.value}: "
            f"{primary_factor.description}"
        )
        
        # Add other significant factors
        other_factors = [f for f in all_factors if f != primary_factor and f.impact >= 2]
        if other_factors:
            factor_names = ", ".join(f.type.value for f in other_factors)
            explanation_parts.append(
                f"Additional contributing factors include: {factor_names}."
            )
        
        # Add body type context if sensitivity is not neutral
        sensitivity = self.BODY_TYPE_SENSITIVITY.get(
            body_type.classification, 1.0
        )
        if sensitivity > 1.0:
            explanation_parts.append(
                f"Your {body_type.classification.value} body type may have "
                "increased sensitivity to water retention factors."
            )
        elif sensitivity < 1.0:
            explanation_parts.append(
                f"Your {body_type.classification.value} body type typically has "
                "lower sensitivity to water retention factors."
            )
        
        return " ".join(explanation_parts)
    
    def _calculate_confidence(
        self, factors: List[RetentionFactor], adjusted_score: float
    ) -> float:
        """Calculate confidence based on factor clarity and score."""
        if not factors:
            return 60.0  # Low confidence with no clear factors
        
        # Higher confidence when there's a clear dominant factor
        max_impact = max(f.impact for f in factors)
        other_impacts = [f.impact for f in factors if f.impact != max_impact]
        
        if not other_impacts:
            # Only one factor - high confidence
            base_confidence = 85.0
        else:
            # Calculate separation between primary and secondary factors
            second_highest = max(other_impacts)
            separation = max_impact - second_highest
            
            # More separation = higher confidence
            base_confidence = 70.0 + (separation * 10)
        
        # Adjust based on score magnitude (extreme scores = higher confidence)
        if adjusted_score <= 1 or adjusted_score >= 7:
            base_confidence += 5
        
        return min(95.0, max(65.0, base_confidence))
