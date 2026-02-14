"""Educational Content Engine for translating technical analysis to accessible language."""

import re
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from jeevanfit.insights.insight_generator import Insight


class ConfidenceLevel(str, Enum):
    """Confidence level for cause-effect relationships."""
    WELL_ESTABLISHED = "well_established"
    SUPPORTED = "supported"
    THEORETICAL = "theoretical"


class ResourceType(str, Enum):
    """Type of educational resource."""
    ARTICLE = "article"
    VIDEO = "video"
    INFOGRAPHIC = "infographic"


class CauseEffectPair(BaseModel):
    """Represents a cause-effect relationship in educational content."""
    cause: str = Field(description="The lifestyle factor or habit")
    effect: str = Field(description="The body response or outcome")
    mechanism: str = Field(description="How the cause leads to the effect")
    confidence: ConfidenceLevel = Field(description="Scientific confidence level")


class EducationalResource(BaseModel):
    """Additional educational resource for learning."""
    title: str = Field(description="Resource title")
    description: str = Field(description="Brief description")
    type: ResourceType = Field(description="Type of resource")
    url: str = Field(description="URL to the resource")


class EducationalContent(BaseModel):
    """Educational content translated from technical analysis."""
    main_message: str = Field(description="Primary educational message")
    explanation: str = Field(description="Detailed explanation in accessible language")
    cause_effect: List[CauseEffectPair] = Field(
        default_factory=list,
        description="Cause-effect relationships"
    )
    learn_more: List[EducationalResource] = Field(
        default_factory=list,
        description="Additional learning resources"
    )
    disclaimer: str = Field(description="Educational disclaimer")


class EducationalContentEngine:
    """
    Translates technical analysis into accessible educational content.
    
    Ensures all content:
    - Uses accessible language for non-experts
    - Avoids medical diagnosis terminology
    - Includes cause-effect explanations
    - Contains appropriate disclaimers
    """
    
    # Forbidden medical terms that should not appear in output
    FORBIDDEN_MEDICAL_TERMS = [
        "diagnosis",
        "diagnose",
        "diagnosed",
        "diagnosing",
        "treatment",
        "treat",
        "treating",
        "treated",
        "cure",
        "cured",
        "curing",
        "disease",
        "disorder",
        "condition",
        "prescribe",
        "prescribed",
        "prescribing",
        "medication",
        "medicine",
        "drug",
        "therapy",
        "therapeutic",
    ]
    
    # Mapping of medical terms to educational alternatives
    TERM_REPLACEMENTS = {
        "diagnosis": "observation",
        "diagnose": "observe",
        "diagnosed": "observed",
        "diagnosing": "observing",
        "treatment": "approach",
        "treat": "address",
        "treating": "addressing",
        "treated": "addressed",
        "cure": "improve",
        "cured": "improved",
        "curing": "improving",
        "disease": "pattern",
        "disorder": "pattern",
        "condition": "situation",
        "prescribe": "suggest",
        "prescribed": "suggested",
        "prescribing": "suggesting",
        "medication": "supplement",
        "medicine": "supplement",
        "drug": "substance",
        "therapy": "practice",
        "therapeutic": "beneficial",
    }
    
    # Standard disclaimer for health-related content
    STANDARD_DISCLAIMER = (
        "JeevanFit is an educational tool for habit awareness, not a medical device. "
        "This information is for educational purposes only and should not be considered "
        "medical advice. If you have health concerns, please consult a healthcare professional."
    )
    
    def translate_to_educational(self, insight: Insight) -> EducationalContent:
        """
        Convert technical analysis insight to accessible educational content.
        
        Args:
            insight: Technical insight from analyzers
            
        Returns:
            EducationalContent: Accessible educational content with explanations
        """
        # Extract and translate the main message
        main_message = self._create_main_message(insight)
        
        # Create detailed explanation
        explanation = self._create_explanation(insight)
        
        # Extract or create cause-effect pairs
        cause_effect_pairs = self._extract_cause_effect(insight)
        
        # Check for health concerns and add professional consultation recommendation
        if self._detect_health_concern(insight):
            explanation = self._add_consultation_recommendation(explanation)
        
        # Ensure all content is non-medical
        main_message = self.ensure_non_medical(main_message)
        explanation = self.ensure_non_medical(explanation)
        
        # Clean cause-effect pairs
        for pair in cause_effect_pairs:
            pair.cause = self.ensure_non_medical(pair.cause)
            pair.effect = self.ensure_non_medical(pair.effect)
            pair.mechanism = self.ensure_non_medical(pair.mechanism)
        
        return EducationalContent(
            main_message=main_message,
            explanation=explanation,
            cause_effect=cause_effect_pairs,
            learn_more=[],  # Can be populated with relevant resources
            disclaimer=self.STANDARD_DISCLAIMER
        )
    
    def ensure_non_medical(self, content: str) -> str:
        """
        Validate content doesn't contain medical diagnosis language.
        Replace problematic terms with educational alternatives.
        
        Args:
            content: Text content to validate and clean
            
        Returns:
            str: Content with medical terms replaced
        """
        if not content:
            return content
        
        cleaned_content = content
        
        # Replace each forbidden term with its educational alternative
        for medical_term, replacement in self.TERM_REPLACEMENTS.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(medical_term) + r'\b'
            cleaned_content = re.sub(
                pattern,
                replacement,
                cleaned_content,
                flags=re.IGNORECASE
            )
        
        return cleaned_content
    
    def _create_main_message(self, insight: Insight) -> str:
        """Create the main educational message from insight."""
        # Use the insight summary as base, make it more educational
        if insight.actionable:
            return f"Your {insight.category.lower()} patterns suggest opportunities for improvement. {insight.summary}"
        else:
            return f"Understanding your {insight.category.lower()}: {insight.summary}"
    
    def _create_explanation(self, insight: Insight) -> str:
        """Create detailed explanation from insight details."""
        # Start with the insight details
        explanation = insight.details
        
        # Add context about why this matters
        context = self._add_wellness_context(insight.category)
        
        return f"{explanation} {context}"
    
    def _add_wellness_context(self, category: str) -> str:
        """Add context explaining why a category matters for wellness."""
        context_map = {
            "Nutrition": "Understanding how different foods affect your body helps you make informed dietary choices that support your energy levels and overall wellness.",
            "Hydration": "Proper hydration and water balance are essential for many body functions, including temperature regulation, nutrient transport, and waste removal.",
            "Sleep & Recovery": "Quality sleep is fundamental to physical recovery, mental clarity, and overall health. Your sleep patterns directly impact how you feel and function during the day.",
            "Metabolism": "Your body's metabolic characteristics influence how you process nutrients and respond to lifestyle changes. Understanding these patterns helps you tailor your habits effectively.",
            "Lifestyle Patterns": "Recognizing patterns in your daily habits empowers you to make intentional changes that align with your wellness goals.",
        }
        
        return context_map.get(category, "Understanding your lifestyle patterns helps you make informed decisions about your health and wellness.")
    
    def _extract_cause_effect(self, insight: Insight) -> List[CauseEffectPair]:
        """Extract or create cause-effect pairs from insight."""
        cause_effect_pairs = []
        
        # Parse the details to identify cause-effect relationships
        # This is a simplified implementation - could be enhanced with NLP
        
        # Look for common patterns in the details
        details_lower = insight.details.lower()
        
        # Example patterns based on category
        if "food" in insight.category.lower() or "nutrition" in insight.category.lower():
            if "sodium" in details_lower or "salt" in details_lower:
                cause_effect_pairs.append(CauseEffectPair(
                    cause="High sodium intake from processed foods",
                    effect="Increased water retention and bloating",
                    mechanism="Sodium causes your body to hold onto extra water to maintain proper fluid balance",
                    confidence=ConfidenceLevel.WELL_ESTABLISHED
                ))
        
        if "sleep" in insight.category.lower():
            if "caffeine" in details_lower:
                cause_effect_pairs.append(CauseEffectPair(
                    cause="Caffeine consumption in the evening",
                    effect="Reduced sleep quality and difficulty falling asleep",
                    mechanism="Caffeine blocks adenosine receptors in the brain, which normally promote sleepiness",
                    confidence=ConfidenceLevel.WELL_ESTABLISHED
                ))
        
        if "hydration" in insight.category.lower() or "water" in insight.category.lower():
            if "retention" in details_lower:
                cause_effect_pairs.append(CauseEffectPair(
                    cause="Lifestyle factors affecting fluid balance",
                    effect="Changes in water retention levels",
                    mechanism="Your body adjusts water retention based on sodium intake, hydration status, and hormonal signals",
                    confidence=ConfidenceLevel.SUPPORTED
                ))
        
        # If no specific pairs were identified, create a general one
        if not cause_effect_pairs:
            cause_effect_pairs.append(CauseEffectPair(
                cause="Your daily lifestyle habits",
                effect="Observable patterns in how your body responds",
                mechanism="Consistent habits create predictable physiological responses that you can learn to recognize and adjust",
                confidence=ConfidenceLevel.SUPPORTED
            ))
        
        return cause_effect_pairs
    
    def _detect_health_concern(self, insight: Insight) -> bool:
        """
        Detect if insight indicates potential health concerns that warrant 
        professional consultation.
        
        Args:
            insight: The insight to analyze
            
        Returns:
            bool: True if health concerns are detected
        """
        # Keywords that indicate concerning patterns
        concern_indicators = [
            'severe', 'extreme', 'chronic', 'persistent', 'significant',
            'very high', 'very low', 'excessive', 'insufficient',
            'poor quality', 'disrupted', 'irregular', 'abnormal'
        ]
        
        # Check insight details and summary for concerning patterns
        combined_text = (insight.summary + " " + insight.details).lower()
        
        # Check for concern indicators
        for indicator in concern_indicators:
            if indicator in combined_text:
                return True
        
        # Check for high priority insights with specific categories
        if insight.priority.value == "high":
            concerning_categories = ['sleep', 'hydration', 'nutrition']
            if any(cat in insight.category.lower() for cat in concerning_categories):
                # High priority in these categories may indicate concerns
                return True
        
        return False
    
    def _add_consultation_recommendation(self, explanation: str) -> str:
        """
        Add a recommendation to consult a healthcare professional.
        
        Args:
            explanation: The current explanation text
            
        Returns:
            str: Explanation with consultation recommendation added
        """
        consultation_text = (
            " We recommend consulting with a healthcare professional to discuss "
            "these patterns and get personalized guidance for your situation."
        )
        
        return explanation + consultation_text
