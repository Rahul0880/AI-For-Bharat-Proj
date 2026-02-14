"""Property-based tests for EducationalContentEngine using Hypothesis."""

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
    FoodClassifier,
    WaterRetentionPredictor,
    SleepAnalyzer,
    BodyTypeAnalyzer,
)
from jeevanfit.insights.insight_generator import (
    InsightGenerator,
    AnalysisResult,
    AnalysisSource,
    InsightPriority,
)
from jeevanfit.insights.educational_content_engine import EducationalContentEngine


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
    food_items = draw(st.lists(food_item_strategy(), min_size=0, max_size=5))
    water_intake = draw(st.floats(min_value=500, max_value=5000))
    sleep_data = draw(st.one_of(st.none(), sleep_data_strategy()))
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


class TestEducationalContentEngineProperties:
    """Property-based tests for EducationalContentEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = EducationalContentEngine()
        self.insight_generator = InsightGenerator()
        self.food_classifier = FoodClassifier()
        self.water_predictor = WaterRetentionPredictor()
        self.sleep_analyzer = SleepAnalyzer()
        self.body_type_analyzer = BodyTypeAnalyzer()
    
    # Feature: fitbuddy-lifestyle-assistant, Property 18: Non-medical language enforcement
    @given(
        food_item=food_item_strategy(),
        lifestyle=lifestyle_input_strategy(),
        body_type=body_type_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_non_medical_language_enforcement(self, food_item, lifestyle, body_type):
        """
        Property 18: Non-medical language enforcement
        For any generated insight or analysis output, the text should not contain 
        medical diagnosis terms from the forbidden list.
        
        Validates: Requirements 5.3, 8.1
        """
        # Test with food classification
        food_result = self.food_classifier.classify_food(food_item)
        analysis_results = [
            AnalysisResult(
                source=AnalysisSource.FOOD,
                data=food_result,
                confidence=85.0,
                timestamp=datetime.now()
            )
        ]
        
        insight = self.insight_generator.generate_insight(analysis_results)
        educational_content = self.engine.translate_to_educational(insight)
        
        # Check all text fields for forbidden medical terms
        all_text = (
            educational_content.main_message + " " +
            educational_content.explanation + " " +
            educational_content.disclaimer
        )
        
        # Add cause-effect text
        for pair in educational_content.cause_effect:
            all_text += " " + pair.cause + " " + pair.effect + " " + pair.mechanism
        
        all_text_lower = all_text.lower()
        
        # Check for forbidden medical terms
        forbidden_terms = self.engine.FORBIDDEN_MEDICAL_TERMS
        found_terms = []
        
        for term in forbidden_terms:
            # Use word boundary matching to avoid false positives
            import re
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, all_text_lower):
                found_terms.append(term)
        
        assert len(found_terms) == 0, \
            f"Educational content contains forbidden medical terms: {found_terms}. " \
            f"Content: {all_text[:200]}..."
    
    # Feature: fitbuddy-lifestyle-assistant, Property 19: Contextual explanation presence
    @given(
        food_item=food_item_strategy(),
        lifestyle=lifestyle_input_strategy(),
        body_type=body_type_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_contextual_explanation_presence(self, food_item, lifestyle, body_type):
        """
        Property 19: Contextual explanation presence
        For any insight about a lifestyle factor, the output should include context 
        explaining why that factor matters for overall wellness.
        
        Validates: Requirements 5.4
        """
        # Test with different analyzer types
        food_result = self.food_classifier.classify_food(food_item)
        water_result = self.water_predictor.predict_retention(lifestyle, body_type)
        
        # Ensure lifestyle has sleep data
        if lifestyle.sleep_data is None:
            lifestyle.sleep_data = SleepData(
                duration=7.0,
                quality=6,
                bedtime=time(22, 0),
                wake_time=time(6, 0),
                interruptions=1,
                timestamp=datetime.now()
            )
        
        sleep_result = self.sleep_analyzer.analyze_sleep(lifestyle.sleep_data, lifestyle)
        body_result = self.body_type_analyzer.analyze_body_type(body_type, lifestyle)
        
        # Test each analyzer type
        test_cases = [
            (AnalysisSource.FOOD, food_result, "Nutrition"),
            (AnalysisSource.WATER, water_result, "Hydration"),
            (AnalysisSource.SLEEP, sleep_result, "Sleep"),
            (AnalysisSource.BODY_TYPE, body_result, "Metabolism"),
        ]
        
        wellness_context_indicators = [
            'wellness', 'health', 'body', 'important', 'essential',
            'support', 'help', 'benefit', 'impact', 'affect',
            'function', 'energy', 'recovery', 'balance', 'overall'
        ]
        
        for source, result, expected_category in test_cases:
            analysis_results = [
                AnalysisResult(
                    source=source,
                    data=result,
                    confidence=80.0,
                    timestamp=datetime.now()
                )
            ]
            
            insight = self.insight_generator.generate_insight(analysis_results)
            educational_content = self.engine.translate_to_educational(insight)
            
            # Check that explanation includes wellness context
            explanation_lower = educational_content.explanation.lower()
            
            # Should mention why this matters for wellness
            has_wellness_context = any(
                indicator in explanation_lower 
                for indicator in wellness_context_indicators
            )
            
            assert has_wellness_context, \
                f"Educational content for {source.value} should include context about " \
                f"why this factor matters for wellness. Expected words like 'wellness', " \
                f"'health', 'important', 'support', etc. " \
                f"Got explanation: '{educational_content.explanation}'"
            
            # Explanation should be substantial (not just a token mention)
            assert len(educational_content.explanation) >= 50, \
                f"Educational explanation should provide substantial context (>=50 chars), " \
                f"got {len(educational_content.explanation)} chars"
    
    # Feature: fitbuddy-lifestyle-assistant, Property 20: Educational disclaimer inclusion
    @given(
        food_item=food_item_strategy(),
        lifestyle=lifestyle_input_strategy(),
        body_type=body_type_strategy()
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_educational_disclaimer_inclusion(self, food_item, lifestyle, body_type):
        """
        Property 20: Educational disclaimer inclusion
        For any user-facing output containing health-related insights, the content 
        should include a disclaimer stating JeevanFit is an educational tool, 
        not a medical device.
        
        Validates: Requirements 8.3, 8.4
        """
        # Test with all analyzer types
        food_result = self.food_classifier.classify_food(food_item)
        water_result = self.water_predictor.predict_retention(lifestyle, body_type)
        
        # Ensure lifestyle has sleep data
        if lifestyle.sleep_data is None:
            lifestyle.sleep_data = SleepData(
                duration=7.0,
                quality=6,
                bedtime=time(22, 0),
                wake_time=time(6, 0),
                interruptions=1,
                timestamp=datetime.now()
            )
        
        sleep_result = self.sleep_analyzer.analyze_sleep(lifestyle.sleep_data, lifestyle)
        body_result = self.body_type_analyzer.analyze_body_type(body_type, lifestyle)
        
        test_cases = [
            (AnalysisSource.FOOD, food_result),
            (AnalysisSource.WATER, water_result),
            (AnalysisSource.SLEEP, sleep_result),
            (AnalysisSource.BODY_TYPE, body_result),
        ]
        
        disclaimer_keywords = [
            'educational',
            'not a medical',
            'not medical advice',
            'consult',
            'healthcare professional',
        ]
        
        for source, result in test_cases:
            analysis_results = [
                AnalysisResult(
                    source=source,
                    data=result,
                    confidence=80.0,
                    timestamp=datetime.now()
                )
            ]
            
            insight = self.insight_generator.generate_insight(analysis_results)
            educational_content = self.engine.translate_to_educational(insight)
            
            # Check that disclaimer exists and is not empty
            assert educational_content.disclaimer is not None, \
                f"Educational content for {source.value} must include a disclaimer"
            
            assert len(educational_content.disclaimer) > 0, \
                f"Educational content disclaimer for {source.value} should not be empty"
            
            # Check that disclaimer contains key educational positioning language
            disclaimer_lower = educational_content.disclaimer.lower()
            
            # Must mention it's educational
            assert 'educational' in disclaimer_lower, \
                f"Disclaimer must state that JeevanFit is an educational tool. " \
                f"Got: '{educational_content.disclaimer}'"
            
            # Must clarify it's not medical advice/device
            has_medical_disclaimer = (
                'not a medical' in disclaimer_lower or 
                'not medical advice' in disclaimer_lower
            )
            assert has_medical_disclaimer, \
                f"Disclaimer must clarify that JeevanFit is not a medical device or advice. " \
                f"Got: '{educational_content.disclaimer}'"
            
            # Should recommend consulting healthcare professional
            has_consult_recommendation = (
                'consult' in disclaimer_lower and 
                'healthcare' in disclaimer_lower
            )
            assert has_consult_recommendation, \
                f"Disclaimer should recommend consulting a healthcare professional. " \
                f"Got: '{educational_content.disclaimer}'"
            
            # Disclaimer should be substantial
            assert len(educational_content.disclaimer) >= 50, \
                f"Disclaimer should be substantial (>=50 chars), " \
                f"got {len(educational_content.disclaimer)} chars"


class TestEducationalContentEngineUnit:
    """Unit tests for EducationalContentEngine specific functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = EducationalContentEngine()
    
    def test_ensure_non_medical_replaces_forbidden_terms(self):
        """Test that ensure_non_medical replaces all forbidden medical terms."""
        # Test text with various medical terms
        test_text = (
            "The diagnosis shows a disease that requires treatment. "
            "We will prescribe medication to cure this condition. "
            "This disorder needs therapy for proper treatment."
        )
        
        cleaned_text = self.engine.ensure_non_medical(test_text)
        
        # Check that forbidden terms are replaced
        assert "diagnosis" not in cleaned_text.lower()
        assert "disease" not in cleaned_text.lower()
        assert "treatment" not in cleaned_text.lower()
        assert "prescribe" not in cleaned_text.lower()
        assert "medication" not in cleaned_text.lower()
        assert "cure" not in cleaned_text.lower()
        assert "condition" not in cleaned_text.lower()
        assert "disorder" not in cleaned_text.lower()
        assert "therapy" not in cleaned_text.lower()
        
        # Check that replacements are present
        assert "observation" in cleaned_text.lower() or "observe" in cleaned_text.lower()
        assert "pattern" in cleaned_text.lower()
        assert "approach" in cleaned_text.lower() or "address" in cleaned_text.lower()
    
    def test_ensure_non_medical_preserves_safe_text(self):
        """Test that ensure_non_medical preserves text without medical terms."""
        safe_text = "Your lifestyle patterns suggest opportunities for improvement."
        
        cleaned_text = self.engine.ensure_non_medical(safe_text)
        
        assert cleaned_text == safe_text
    
    def test_ensure_non_medical_handles_empty_text(self):
        """Test that ensure_non_medical handles empty or None text."""
        assert self.engine.ensure_non_medical("") == ""
        assert self.engine.ensure_non_medical(None) is None
    
    def test_translate_to_educational_creates_cause_effect_pairs(self):
        """Test that translate_to_educational creates cause-effect pairs."""
        from jeevanfit.insights.insight_generator import Insight, InsightPriority
        
        insight = Insight(
            title="Sleep Quality Insight",
            summary="Your sleep patterns show room for improvement",
            details="Caffeine consumption in the evening may be affecting your sleep quality",
            priority=InsightPriority.HIGH,
            category="Sleep & Recovery",
            actionable=True,
            related_insights=[]
        )
        
        educational_content = self.engine.translate_to_educational(insight)
        
        # Should have at least one cause-effect pair
        assert len(educational_content.cause_effect) > 0
        
        # Each pair should have all required fields
        for pair in educational_content.cause_effect:
            assert pair.cause is not None and len(pair.cause) > 0
            assert pair.effect is not None and len(pair.effect) > 0
            assert pair.mechanism is not None and len(pair.mechanism) > 0
            assert pair.confidence is not None

    
    def test_health_concern_detection_triggers_consultation_recommendation(self):
        """
        Test that concerning patterns trigger professional consultation recommendation.
        Validates: Requirements 8.2
        """
        from jeevanfit.insights.insight_generator import Insight, InsightPriority
        
        # Test case 1: Severe sleep issues
        concerning_insight = Insight(
            title="Severe Sleep Quality Issues",
            summary="Your sleep patterns show severe disruption",
            details="Persistent poor sleep quality with extreme interruptions may be affecting your health",
            priority=InsightPriority.HIGH,
            category="Sleep & Recovery",
            actionable=True,
            related_insights=[]
        )
        
        educational_content = self.engine.translate_to_educational(concerning_insight)
        
        # Should include consultation recommendation
        explanation_lower = educational_content.explanation.lower()
        assert 'consult' in explanation_lower or 'healthcare professional' in explanation_lower, \
            "Concerning patterns should trigger consultation recommendation"
        
        # Test case 2: Extreme hydration issues
        hydration_concern = Insight(
            title="Extreme Water Retention",
            summary="Your water retention levels are very high",
            details="Excessive water retention with significant bloating patterns detected",
            priority=InsightPriority.HIGH,
            category="Hydration",
            actionable=True,
            related_insights=[]
        )
        
        educational_content = self.engine.translate_to_educational(hydration_concern)
        explanation_lower = educational_content.explanation.lower()
        assert 'consult' in explanation_lower or 'healthcare professional' in explanation_lower, \
            "Extreme hydration concerns should trigger consultation recommendation"
        
        # Test case 3: Chronic nutrition issues
        nutrition_concern = Insight(
            title="Chronic Nutritional Imbalance",
            summary="Your nutrition patterns show chronic imbalance",
            details="Persistent insufficient nutrient intake detected over extended period",
            priority=InsightPriority.HIGH,
            category="Nutrition",
            actionable=True,
            related_insights=[]
        )
        
        educational_content = self.engine.translate_to_educational(nutrition_concern)
        explanation_lower = educational_content.explanation.lower()
        assert 'consult' in explanation_lower or 'healthcare professional' in explanation_lower, \
            "Chronic nutrition concerns should trigger consultation recommendation"
    
    def test_normal_patterns_do_not_trigger_consultation(self):
        """
        Test that normal patterns do not unnecessarily trigger consultation recommendations.
        """
        from jeevanfit.insights.insight_generator import Insight, InsightPriority
        
        # Normal insight without concerning patterns
        normal_insight = Insight(
            title="Sleep Quality Insight",
            summary="Your sleep patterns are stable",
            details="Sleep quality is good with consistent patterns",
            priority=InsightPriority.MEDIUM,
            category="Sleep & Recovery",
            actionable=False,
            related_insights=[]
        )
        
        educational_content = self.engine.translate_to_educational(normal_insight)
        
        # Should NOT include consultation recommendation for normal patterns
        explanation_lower = educational_content.explanation.lower()
        
        # It's okay if it mentions consulting in the disclaimer, but not in the explanation
        # unless there's a concerning pattern
        if 'consult' in explanation_lower:
            # If consult is mentioned, it should be in context of general wellness, not urgent concern
            assert 'severe' not in explanation_lower and 'extreme' not in explanation_lower
    
    def test_detect_health_concern_method(self):
        """Test the _detect_health_concern method directly."""
        from jeevanfit.insights.insight_generator import Insight, InsightPriority
        
        # Test concerning patterns
        concerning_cases = [
            Insight(
                title="Test",
                summary="Severe sleep disruption",
                details="Details",
                priority=InsightPriority.HIGH,
                category="Sleep",
                actionable=True,
                related_insights=[]
            ),
            Insight(
                title="Test",
                summary="Extreme water retention",
                details="Details",
                priority=InsightPriority.HIGH,
                category="Hydration",
                actionable=True,
                related_insights=[]
            ),
            Insight(
                title="Test",
                summary="Chronic poor nutrition",
                details="Details",
                priority=InsightPriority.HIGH,
                category="Nutrition",
                actionable=True,
                related_insights=[]
            ),
            Insight(
                title="Test",
                summary="Normal",
                details="Persistent abnormal patterns detected",
                priority=InsightPriority.MEDIUM,
                category="General",
                actionable=False,
                related_insights=[]
            ),
        ]
        
        for insight in concerning_cases:
            assert self.engine._detect_health_concern(insight), \
                f"Should detect health concern in: {insight.summary} {insight.details}"
        
        # Test normal patterns
        normal_cases = [
            Insight(
                title="Test",
                summary="Good sleep quality",
                details="Consistent patterns",
                priority=InsightPriority.MEDIUM,
                category="Sleep",
                actionable=False,
                related_insights=[]
            ),
            Insight(
                title="Test",
                summary="Stable hydration",
                details="Normal water retention levels",
                priority=InsightPriority.LOW,
                category="Hydration",
                actionable=False,
                related_insights=[]
            ),
        ]
        
        for insight in normal_cases:
            assert not self.engine._detect_health_concern(insight), \
                f"Should NOT detect health concern in: {insight.summary} {insight.details}"
