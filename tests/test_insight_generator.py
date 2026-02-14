"""Unit tests for InsightGenerator."""

import pytest
from datetime import datetime
from jeevanfit.insights import (
    InsightGenerator,
    AnalysisResult,
    AnalysisSource,
    Insight,
    InsightPriority
)


class TestInsightGenerator:
    """Test suite for InsightGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = InsightGenerator()
    
    def test_generate_insight_single_source(self):
        """Test generating insight from a single analysis result."""
        result = AnalysisResult(
            source=AnalysisSource.FOOD,
            data={"category": "healthy"},
            confidence=85.0,
            timestamp=datetime.now()
        )
        
        insight = self.generator.generate_insight([result])
        
        assert insight.title == "Food Classification Insight"
        assert insight.category == "Nutrition"
        assert insight.priority == InsightPriority.MEDIUM
        assert isinstance(insight.summary, str)
        assert len(insight.summary) > 0
        assert isinstance(insight.details, str)
        assert len(insight.details) > 0
    
    def test_generate_insight_multiple_sources(self):
        """Test generating insight from multiple analysis results."""
        results = [
            AnalysisResult(
                source=AnalysisSource.FOOD,
                data={"category": "junk"},
                confidence=90.0,
                timestamp=datetime.now()
            ),
            AnalysisResult(
                source=AnalysisSource.WATER,
                data={"level": "high"},
                confidence=85.0,
                timestamp=datetime.now()
            ),
            AnalysisResult(
                source=AnalysisSource.SLEEP,
                data={"quality": "poor"},
                confidence=80.0,
                timestamp=datetime.now()
            )
        ]
        
        insight = self.generator.generate_insight(results)
        
        assert insight.priority == InsightPriority.HIGH  # High confidence + 3 sources
        assert "3 sources" in insight.summary
        assert len(insight.details) > 0
    
    def test_generate_insight_empty_results_raises_error(self):
        """Test that empty results raise ValueError."""
        with pytest.raises(ValueError, match="Cannot generate insight from empty"):
            self.generator.generate_insight([])
    
    def test_generate_insight_determines_primary_source(self):
        """Test that primary source is determined by highest confidence."""
        results = [
            AnalysisResult(
                source=AnalysisSource.FOOD,
                data={},
                confidence=70.0,
                timestamp=datetime.now()
            ),
            AnalysisResult(
                source=AnalysisSource.SLEEP,
                data={},
                confidence=95.0,
                timestamp=datetime.now()
            )
        ]
        
        insight = self.generator.generate_insight(results)
        
        # Primary source should be SLEEP (highest confidence)
        assert insight.title == "Sleep Quality Insight"
        assert insight.category == "Sleep & Recovery"
    
    def test_prioritize_insights_empty_list(self):
        """Test prioritizing empty list returns empty list."""
        result = self.generator.prioritize_insights([])
        assert result == []
    
    def test_prioritize_insights_sorts_by_priority(self):
        """Test that insights are sorted by priority."""
        insights = [
            Insight(
                title="Low Priority",
                summary="Summary",
                details="Details",
                priority=InsightPriority.LOW,
                category="Test",
                actionable=False,
                related_insights=[]
            ),
            Insight(
                title="High Priority",
                summary="Summary",
                details="Details",
                priority=InsightPriority.HIGH,
                category="Test",
                actionable=True,
                related_insights=[]
            ),
            Insight(
                title="Medium Priority",
                summary="Summary",
                details="Details",
                priority=InsightPriority.MEDIUM,
                category="Test",
                actionable=False,
                related_insights=[]
            )
        ]
        
        sorted_insights = self.generator.prioritize_insights(insights)
        
        assert sorted_insights[0].priority == InsightPriority.HIGH
        assert sorted_insights[1].priority == InsightPriority.MEDIUM
        assert sorted_insights[2].priority == InsightPriority.LOW
    
    def test_prioritize_insights_considers_actionability(self):
        """Test that actionable insights are prioritized within same priority level."""
        insights = [
            Insight(
                title="Not Actionable",
                summary="Summary",
                details="Details",
                priority=InsightPriority.HIGH,
                category="Test",
                actionable=False,
                related_insights=[]
            ),
            Insight(
                title="Actionable",
                summary="Summary",
                details="Details",
                priority=InsightPriority.HIGH,
                category="Test",
                actionable=True,
                related_insights=[]
            )
        ]
        
        sorted_insights = self.generator.prioritize_insights(insights)
        
        # Actionable should come first
        assert sorted_insights[0].actionable is True
        assert sorted_insights[1].actionable is False
    
    def test_prioritize_insights_filters_redundant(self):
        """Test that redundant insights are filtered out."""
        insights = [
            Insight(
                title="Food Classification Insight",
                summary="Summary 1",
                details="Details 1",
                priority=InsightPriority.HIGH,
                category="Nutrition",
                actionable=True,
                related_insights=[]
            ),
            Insight(
                title="Food Classification Insight",
                summary="Summary 2",
                details="Details 2",
                priority=InsightPriority.MEDIUM,
                category="Nutrition",
                actionable=False,
                related_insights=[]
            )
        ]
        
        filtered_insights = self.generator.prioritize_insights(insights)
        
        # Should only keep one insight with same category and similar title
        assert len(filtered_insights) == 1
    
    def test_is_actionable_with_recommendations_dict(self):
        """Test actionability detection with recommendations in dict."""
        results = [
            AnalysisResult(
                source=AnalysisSource.SLEEP,
                data={"recommendations": ["Get more sleep"]},
                confidence=80.0,
                timestamp=datetime.now()
            )
        ]
        
        insight = self.generator.generate_insight(results)
        assert insight.actionable is True
    
    def test_is_actionable_with_recommendations_attribute(self):
        """Test actionability detection with recommendations attribute."""
        class MockData:
            def __init__(self):
                self.recommendations = ["Drink more water"]
        
        results = [
            AnalysisResult(
                source=AnalysisSource.WATER,
                data=MockData(),
                confidence=80.0,
                timestamp=datetime.now()
            )
        ]
        
        insight = self.generator.generate_insight(results)
        assert insight.actionable is True
    
    def test_is_actionable_without_recommendations(self):
        """Test actionability detection without recommendations."""
        results = [
            AnalysisResult(
                source=AnalysisSource.TREND,
                data={"pattern": "increasing"},
                confidence=80.0,
                timestamp=datetime.now()
            )
        ]
        
        insight = self.generator.generate_insight(results)
        assert insight.actionable is False
    
    def test_priority_high_with_high_confidence_and_multiple_sources(self):
        """Test HIGH priority assignment with high confidence and 3+ sources."""
        results = [
            AnalysisResult(source=AnalysisSource.FOOD, data={}, confidence=85.0, timestamp=datetime.now()),
            AnalysisResult(source=AnalysisSource.WATER, data={}, confidence=80.0, timestamp=datetime.now()),
            AnalysisResult(source=AnalysisSource.SLEEP, data={}, confidence=75.0, timestamp=datetime.now())
        ]
        
        insight = self.generator.generate_insight(results)
        assert insight.priority == InsightPriority.HIGH
    
    def test_priority_medium_with_moderate_confidence(self):
        """Test MEDIUM priority assignment with moderate confidence."""
        results = [
            AnalysisResult(source=AnalysisSource.FOOD, data={}, confidence=65.0, timestamp=datetime.now())
        ]
        
        insight = self.generator.generate_insight(results)
        assert insight.priority == InsightPriority.MEDIUM
    
    def test_priority_low_with_low_confidence_single_source(self):
        """Test LOW priority assignment with low confidence and single source."""
        results = [
            AnalysisResult(source=AnalysisSource.TREND, data={}, confidence=50.0, timestamp=datetime.now())
        ]
        
        insight = self.generator.generate_insight(results)
        assert insight.priority == InsightPriority.LOW
    
    def test_category_mapping_for_all_sources(self):
        """Test that all source types map to correct categories."""
        source_category_map = {
            AnalysisSource.FOOD: "Nutrition",
            AnalysisSource.WATER: "Hydration",
            AnalysisSource.SLEEP: "Sleep & Recovery",
            AnalysisSource.BODY_TYPE: "Metabolism",
            AnalysisSource.TREND: "Lifestyle Patterns"
        }
        
        for source, expected_category in source_category_map.items():
            result = AnalysisResult(
                source=source,
                data={},
                confidence=80.0,
                timestamp=datetime.now()
            )
            insight = self.generator.generate_insight([result])
            assert insight.category == expected_category
