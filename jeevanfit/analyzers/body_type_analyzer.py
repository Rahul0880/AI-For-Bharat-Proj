"""Body type analyzer for JeevanFit."""

from enum import Enum
from typing import List
from pydantic import BaseModel, Field

from jeevanfit.models.core import BodyType, BodyTypeClassification, LifestyleInput


class MetabolicRate(str, Enum):
    """Base metabolic rate categories."""
    FAST = "fast"
    MODERATE = "moderate"
    SLOW = "slow"


class MetabolicProfile(BaseModel):
    """Metabolic characteristics for a body type."""
    base_metabolic_rate: MetabolicRate = Field(description="Base metabolic rate")
    carb_sensitivity: int = Field(ge=1, le=10, description="Carbohydrate sensitivity (1=low, 10=high)")
    fat_storage_tendency: int = Field(ge=1, le=10, description="Fat storage tendency (1=low, 10=high)")
    muscle_gain_potential: int = Field(ge=1, le=10, description="Muscle gain potential (1=low, 10=high)")
    recovery_speed: int = Field(ge=1, le=10, description="Recovery speed (1=slow, 10=fast)")


class NutritionalNeeds(BaseModel):
    """Nutritional needs tailored to body type."""
    protein_ratio: float = Field(ge=0, le=100, description="Recommended protein percentage")
    carb_ratio: float = Field(ge=0, le=100, description="Recommended carbohydrate percentage")
    fat_ratio: float = Field(ge=0, le=100, description="Recommended fat percentage")
    meal_frequency: str = Field(description="Recommended meal frequency")
    hydration_guidance: str = Field(description="Hydration recommendations")


class BodyTypeRecommendation(BaseModel):
    """A personalized recommendation for body type."""
    priority: str = Field(description="Priority level: HIGH, MEDIUM, or LOW")
    action: str = Field(description="Recommended action")
    rationale: str = Field(description="Explanation for the recommendation")
    expected_impact: str = Field(description="Expected impact of following the recommendation")


class BodyTypeInsight(BaseModel):
    """Body type-specific insights and recommendations."""
    metabolic_response: str = Field(description="How metabolism responds to lifestyle changes")
    fat_storage_pattern: str = Field(description="Fat storage patterns for this body type")
    energy_utilization: str = Field(description="How energy is utilized")
    nutritional_needs: NutritionalNeeds = Field(description="Specific nutritional needs")
    lifestyle_recommendations: List[BodyTypeRecommendation] = Field(description="Personalized recommendations")


class BodyTypeAnalyzer:
    """Analyzes body type and provides personalized metabolic insights."""
    
    def analyze_body_type(
        self, body_type: BodyType, lifestyle: LifestyleInput
    ) -> BodyTypeInsight:
        """
        Provide body type-specific insights based on lifestyle input.
        
        Args:
            body_type: The user's body type information
            lifestyle: The user's lifestyle input data
            
        Returns:
            BodyTypeInsight with personalized analysis and recommendations
        """
        # Get metabolic profile for the body type
        metabolic_profile = self.get_metabolic_profile(body_type)
        
        # Generate body type-specific insights
        metabolic_response = self._generate_metabolic_response(
            body_type.classification, lifestyle, metabolic_profile
        )
        
        fat_storage_pattern = self._generate_fat_storage_pattern(
            body_type.classification, lifestyle
        )
        
        energy_utilization = self._generate_energy_utilization(
            body_type.classification, lifestyle, metabolic_profile
        )
        
        # Get nutritional needs
        nutritional_needs = self._get_nutritional_needs(body_type.classification)
        
        # Generate personalized recommendations
        recommendations = self._generate_recommendations(
            body_type.classification, lifestyle, metabolic_profile
        )
        
        return BodyTypeInsight(
            metabolic_response=metabolic_response,
            fat_storage_pattern=fat_storage_pattern,
            energy_utilization=energy_utilization,
            nutritional_needs=nutritional_needs,
            lifestyle_recommendations=recommendations
        )
    
    def get_metabolic_profile(self, body_type: BodyType) -> MetabolicProfile:
        """
        Get metabolic characteristics for a body type.
        
        Args:
            body_type: The user's body type information
            
        Returns:
            MetabolicProfile with body type-specific characteristics
        """
        classification = body_type.classification
        
        if classification == BodyTypeClassification.ECTOMORPH:
            return MetabolicProfile(
                base_metabolic_rate=MetabolicRate.FAST,
                carb_sensitivity=3,  # Low sensitivity, high tolerance
                fat_storage_tendency=2,  # Low tendency
                muscle_gain_potential=4,  # Moderate-low potential
                recovery_speed=7  # Fast recovery
            )
        
        elif classification == BodyTypeClassification.MESOMORPH:
            return MetabolicProfile(
                base_metabolic_rate=MetabolicRate.MODERATE,
                carb_sensitivity=5,  # Moderate sensitivity
                fat_storage_tendency=5,  # Moderate tendency
                muscle_gain_potential=8,  # High potential
                recovery_speed=8  # Fast recovery
            )
        
        elif classification == BodyTypeClassification.ENDOMORPH:
            return MetabolicProfile(
                base_metabolic_rate=MetabolicRate.SLOW,
                carb_sensitivity=8,  # High sensitivity, lower tolerance
                fat_storage_tendency=8,  # High tendency
                muscle_gain_potential=6,  # Moderate-high potential
                recovery_speed=5  # Moderate recovery
            )
        
        else:  # MIXED
            return MetabolicProfile(
                base_metabolic_rate=MetabolicRate.MODERATE,
                carb_sensitivity=5,
                fat_storage_tendency=5,
                muscle_gain_potential=6,
                recovery_speed=6
            )
    
    def _generate_metabolic_response(
        self,
        classification: BodyTypeClassification,
        lifestyle: LifestyleInput,
        profile: MetabolicProfile
    ) -> str:
        """Generate metabolic response explanation."""
        if classification == BodyTypeClassification.ECTOMORPH:
            response = (
                "Your fast metabolism means your body burns calories quickly. "
                "Lifestyle changes like increased food intake will be processed rapidly, "
                "requiring consistent high-calorie consumption to maintain or gain weight. "
            )
            
            # Analyze current intake
            total_calories = sum(
                item.nutritional_info.calories for item in lifestyle.food_items
            )
            if total_calories < 2000:
                response += (
                    "Your current calorie intake may be insufficient for your metabolic rate. "
                    "Consider increasing meal frequency and portion sizes."
                )
            
        elif classification == BodyTypeClassification.MESOMORPH:
            response = (
                "Your moderate metabolism provides balanced energy processing. "
                "Your body responds efficiently to lifestyle changes, allowing for "
                "effective weight management and muscle development with appropriate nutrition. "
            )
            
            # Check balance
            if lifestyle.food_items:
                total_protein = sum(
                    item.nutritional_info.protein for item in lifestyle.food_items
                )
                if total_protein < 60:
                    response += (
                        "Increasing protein intake could enhance your natural muscle-building potential."
                    )
            
        elif classification == BodyTypeClassification.ENDOMORPH:
            response = (
                "Your slower metabolism means your body conserves energy efficiently. "
                "Lifestyle changes require careful attention to portion control and food quality, "
                "as your body tends to store excess calories more readily. "
            )
            
            # Analyze carb intake
            total_carbs = sum(
                item.nutritional_info.carbohydrates for item in lifestyle.food_items
            )
            if total_carbs > 200:
                response += (
                    "Your current carbohydrate intake is relatively high. "
                    "Consider moderating carb portions and focusing on complex carbohydrates."
                )
        
        else:  # MIXED
            response = (
                "Your mixed body type exhibits characteristics of multiple classifications. "
                "Your metabolism shows moderate efficiency with balanced responses to dietary changes. "
                "Focus on finding the right balance of macronutrients that works for your unique physiology."
            )
        
        return response
    
    def _generate_fat_storage_pattern(
        self,
        classification: BodyTypeClassification,
        lifestyle: LifestyleInput
    ) -> str:
        """Generate fat storage pattern explanation."""
        if classification == BodyTypeClassification.ECTOMORPH:
            pattern = (
                "Your body has a low tendency to store fat. "
                "Even with higher calorie intake, fat accumulation is minimal. "
                "This means you can tolerate more dietary flexibility, but it also "
                "makes it challenging to build energy reserves."
            )
            
        elif classification == BodyTypeClassification.MESOMORPH:
            pattern = (
                "Your body stores fat in a balanced manner, typically distributed evenly. "
                "You can gain or lose fat relatively easily with dietary adjustments. "
                "Maintaining a balanced diet helps prevent unwanted fat accumulation "
                "while supporting muscle development."
            )
            
        elif classification == BodyTypeClassification.ENDOMORPH:
            pattern = (
                "Your body has a higher tendency to store fat, particularly around the midsection. "
                "This is an evolutionary advantage for energy storage, but requires mindful "
                "eating habits to maintain desired body composition. "
                "Focus on nutrient-dense, lower-calorie foods and consistent meal timing."
            )
            
        else:  # MIXED
            pattern = (
                "Your fat storage pattern shows mixed characteristics. "
                "You may store fat moderately, with distribution varying based on lifestyle factors. "
                "Pay attention to how your body responds to different foods and adjust accordingly."
            )
        
        return pattern
    
    def _generate_energy_utilization(
        self,
        classification: BodyTypeClassification,
        lifestyle: LifestyleInput,
        profile: MetabolicProfile
    ) -> str:
        """Generate energy utilization explanation."""
        if classification == BodyTypeClassification.ECTOMORPH:
            energy = (
                "Your body utilizes energy rapidly, burning through calories quickly. "
                "You may experience energy fluctuations if meals are spaced too far apart. "
                "Frequent, smaller meals help maintain stable energy levels throughout the day."
            )
            
            # Check meal frequency
            if len(lifestyle.food_items) < 3:
                energy += (
                    " Consider increasing meal frequency to 4-6 smaller meals "
                    "to maintain consistent energy."
                )
            
        elif classification == BodyTypeClassification.MESOMORPH:
            energy = (
                "Your body utilizes energy efficiently with good balance between "
                "immediate use and storage. You maintain stable energy levels with "
                "regular meals and respond well to varied macronutrient ratios."
            )
            
        elif classification == BodyTypeClassification.ENDOMORPH:
            energy = (
                "Your body is efficient at conserving energy, which can lead to "
                "feeling sluggish if consuming too many simple carbohydrates. "
                "Focus on complex carbs and protein to maintain steady energy levels "
                "without excess storage."
            )
            
            # Check for high sugar
            total_sugar = sum(
                item.nutritional_info.sugar for item in lifestyle.food_items
            )
            if total_sugar > 50:
                energy += (
                    " Your current sugar intake is high, which may cause energy crashes. "
                    "Reducing sugar and increasing protein can help stabilize energy."
                )
        
        else:  # MIXED
            energy = (
                "Your energy utilization shows moderate efficiency. "
                "You benefit from balanced meals with a mix of macronutrients "
                "to maintain stable energy throughout the day."
            )
        
        return energy
    
    def _get_nutritional_needs(
        self, classification: BodyTypeClassification
    ) -> NutritionalNeeds:
        """Get nutritional needs for body type."""
        if classification == BodyTypeClassification.ECTOMORPH:
            return NutritionalNeeds(
                protein_ratio=25.0,
                carb_ratio=55.0,
                fat_ratio=20.0,
                meal_frequency="5-6 smaller meals throughout the day",
                hydration_guidance=(
                    "Aim for 2.5-3 liters daily. Higher calorie intake requires more hydration."
                )
            )
        
        elif classification == BodyTypeClassification.MESOMORPH:
            return NutritionalNeeds(
                protein_ratio=30.0,
                carb_ratio=40.0,
                fat_ratio=30.0,
                meal_frequency="3-4 balanced meals with optional snacks",
                hydration_guidance=(
                    "Aim for 2-2.5 liters daily, adjusting for activity level."
                )
            )
        
        elif classification == BodyTypeClassification.ENDOMORPH:
            return NutritionalNeeds(
                protein_ratio=35.0,
                carb_ratio=25.0,
                fat_ratio=40.0,
                meal_frequency="3-4 moderate meals, avoid late-night eating",
                hydration_guidance=(
                    "Aim for 2-3 liters daily. Good hydration supports metabolism."
                )
            )
        
        else:  # MIXED
            return NutritionalNeeds(
                protein_ratio=30.0,
                carb_ratio=40.0,
                fat_ratio=30.0,
                meal_frequency="3-4 balanced meals per day",
                hydration_guidance=(
                    "Aim for 2-2.5 liters daily, adjusting based on activity."
                )
            )
    
    def _generate_recommendations(
        self,
        classification: BodyTypeClassification,
        lifestyle: LifestyleInput,
        profile: MetabolicProfile
    ) -> List[BodyTypeRecommendation]:
        """Generate personalized recommendations."""
        recommendations = []
        
        if classification == BodyTypeClassification.ECTOMORPH:
            recommendations.append(BodyTypeRecommendation(
                priority="HIGH",
                action="Increase calorie intake with nutrient-dense foods",
                rationale=(
                    "Your fast metabolism requires higher calorie consumption "
                    "to maintain energy and support body functions"
                ),
                expected_impact=(
                    "Better energy stability, reduced fatigue, and easier weight maintenance"
                )
            ))
            
            recommendations.append(BodyTypeRecommendation(
                priority="MEDIUM",
                action="Eat frequent, smaller meals (5-6 per day)",
                rationale=(
                    "Frequent meals help maintain stable blood sugar and energy levels "
                    "given your rapid metabolism"
                ),
                expected_impact=(
                    "More consistent energy throughout the day, reduced hunger spikes"
                )
            ))
            
            if lifestyle.water_intake < 2500:
                recommendations.append(BodyTypeRecommendation(
                    priority="MEDIUM",
                    action="Increase water intake to 2.5-3 liters daily",
                    rationale=(
                        "Higher calorie intake and fast metabolism require adequate hydration"
                    ),
                    expected_impact=(
                        "Better nutrient absorption and metabolic function"
                    )
                ))
        
        elif classification == BodyTypeClassification.MESOMORPH:
            recommendations.append(BodyTypeRecommendation(
                priority="HIGH",
                action="Maintain balanced macronutrient ratios (30% protein, 40% carbs, 30% fat)",
                rationale=(
                    "Your body responds well to balanced nutrition, supporting both "
                    "muscle maintenance and energy needs"
                ),
                expected_impact=(
                    "Optimal body composition, sustained energy, and efficient recovery"
                )
            ))
            
            total_protein = sum(
                item.nutritional_info.protein for item in lifestyle.food_items
            )
            if total_protein < 80:
                recommendations.append(BodyTypeRecommendation(
                    priority="MEDIUM",
                    action="Increase protein intake to support muscle maintenance",
                    rationale=(
                        "Your body type has high muscle-building potential that benefits "
                        "from adequate protein"
                    ),
                    expected_impact=(
                        "Better muscle tone, improved recovery, and sustained metabolism"
                    )
                ))
        
        elif classification == BodyTypeClassification.ENDOMORPH:
            recommendations.append(BodyTypeRecommendation(
                priority="HIGH",
                action="Focus on portion control and lower carbohydrate intake",
                rationale=(
                    "Your slower metabolism and higher carb sensitivity mean excess "
                    "carbohydrates are more readily stored as fat"
                ),
                expected_impact=(
                    "Better weight management, more stable energy, reduced fat storage"
                )
            ))
            
            recommendations.append(BodyTypeRecommendation(
                priority="HIGH",
                action="Prioritize protein and healthy fats in meals",
                rationale=(
                    "Higher protein and fat ratios help maintain satiety and support "
                    "metabolism without excess carbohydrate storage"
                ),
                expected_impact=(
                    "Reduced hunger, better blood sugar control, improved body composition"
                )
            ))
            
            total_sugar = sum(
                item.nutritional_info.sugar for item in lifestyle.food_items
            )
            if total_sugar > 40:
                recommendations.append(BodyTypeRecommendation(
                    priority="MEDIUM",
                    action="Reduce sugar intake and choose complex carbohydrates",
                    rationale=(
                        "Your body type is more sensitive to simple sugars, which can "
                        "lead to energy crashes and increased fat storage"
                    ),
                    expected_impact=(
                        "More stable energy levels, reduced cravings, better weight control"
                    )
                ))
        
        else:  # MIXED
            recommendations.append(BodyTypeRecommendation(
                priority="HIGH",
                action="Experiment with macronutrient ratios to find your optimal balance",
                rationale=(
                    "Mixed body types benefit from personalized nutrition that may "
                    "vary from standard recommendations"
                ),
                expected_impact=(
                    "Discovery of your unique nutritional needs for optimal energy and composition"
                )
            ))
            
            recommendations.append(BodyTypeRecommendation(
                priority="MEDIUM",
                action="Track how different foods affect your energy and body composition",
                rationale=(
                    "Understanding your individual responses helps tailor your diet effectively"
                ),
                expected_impact=(
                    "Better self-awareness and more effective dietary choices"
                )
            ))
        
        return recommendations
