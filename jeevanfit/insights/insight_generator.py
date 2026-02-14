"""Insight generator for aggregating multi-analyzer outputs."""

from datetime import datetime
from enum import Enum
from typing import Any, List
from pydantic import BaseModel, Field


class AnalysisSource(str, Enum):
    """Source of analysis results."""
    FOOD = "food"
    WATER = "water"
    SLEEP = "sleep"
    BODY_TYPE = "body_type"
    TREND = "trend"


class InsightPriority(str, Enum):
    """Priority level for insights."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisResult(BaseModel):
    """Result from an individual analyzer."""
    source: AnalysisSource = Field(description="Source analyzer")
    data: Any = Field(description="Analysis data from the source")
    confidence: float = Field(ge=0, le=100, description="Confidence percentage")
    timestamp: datetime = Field(description="When the analysis was performed")


class Insight(BaseModel):
    """Cohesive insight generated from multiple analysis results."""
    title: str = Field(description="Brief title of the insight")
    summary: str = Field(description="Short summary of the insight")
    details: str = Field(description="Detailed explanation")
    priority: InsightPriority = Field(description="Importance level")
    category: str = Field(description="Category of the insight")
    actionable: bool = Field(description="Whether the insight suggests actions")
    related_insights: List[str] = Field(default_factory=list, description="IDs of related insights")


class InsightGenerator:
    """Generates cohesive insights from multiple analyzer outputs."""
    
    def generate_insight(self, analysis_results: List[AnalysisResult]) -> Insight:
        """
        Aggregate multi-analyzer outputs into a cohesive insight.
        
        Args:
            analysis_results: List of results from different analyzers
            
        Returns:
            Insight: Cohesive insight combining multiple analysis results
        """
        if not analysis_results:
            raise ValueError("Cannot generate insight from empty analysis results")
        
        # Determine the primary source (highest confidence)
        primary_result = max(analysis_results, key=lambda r: r.confidence)
        
        # Extract key information from all sources
        sources = [result.source.value for result in analysis_results]
        avg_confidence = sum(r.confidence for r in analysis_results) / len(analysis_results)
        
        # Generate title based on primary source
        title = self._generate_title(primary_result)
        
        # Generate summary combining all sources
        summary = self._generate_summary(analysis_results)
        
        # Generate detailed explanation
        details = self._generate_details(analysis_results)
        
        # Determine priority based on confidence and source
        priority = self._determine_priority(analysis_results, avg_confidence)
        
        # Determine category
        category = self._determine_category(primary_result.source)
        
        # Check if actionable
        actionable = self._is_actionable(analysis_results)
        
        return Insight(
            title=title,
            summary=summary,
            details=details,
            priority=priority,
            category=category,
            actionable=actionable,
            related_insights=[]
        )
    
    def prioritize_insights(self, insights: List[Insight]) -> List[Insight]:
        """
        Rank insights by importance and filter redundant information.
        
        Args:
            insights: List of insights to prioritize
            
        Returns:
            List[Insight]: Sorted and filtered insights
        """
        if not insights:
            return []
        
        # Filter redundant insights
        filtered_insights = self._filter_redundant(insights)
        
        # Sort by priority (HIGH > MEDIUM > LOW) and actionability
        priority_order = {
            InsightPriority.HIGH: 3,
            InsightPriority.MEDIUM: 2,
            InsightPriority.LOW: 1
        }
        
        sorted_insights = sorted(
            filtered_insights,
            key=lambda i: (priority_order[i.priority], i.actionable),
            reverse=True
        )
        
        return sorted_insights
    
    def _generate_title(self, primary_result: AnalysisResult) -> str:
        """Generate a title based on the primary analysis result."""
        source_titles = {
            AnalysisSource.FOOD: "Food Classification Insight",
            AnalysisSource.WATER: "Water Retention Insight",
            AnalysisSource.SLEEP: "Sleep Quality Insight",
            AnalysisSource.BODY_TYPE: "Body Type Insight",
            AnalysisSource.TREND: "Lifestyle Trend Insight"
        }
        return source_titles.get(primary_result.source, "Lifestyle Insight")
    
    def _generate_summary(self, analysis_results: List[AnalysisResult]) -> str:
        """Generate a summary combining information from all sources."""
        sources = [r.source.value for r in analysis_results]
        source_count = len(set(sources))
        
        if source_count == 1:
            return f"Analysis from {sources[0]} indicates patterns in your lifestyle."
        else:
            return f"Combined analysis from {source_count} sources reveals insights about your habits."
    
    def _generate_details(self, analysis_results: List[AnalysisResult]) -> str:
        """Generate detailed explanation from all analysis results."""
        details_parts = []
        
        for result in analysis_results:
            source_name = result.source.value.replace("_", " ").title()
            details_parts.append(
                f"{source_name} analysis (confidence: {result.confidence:.1f}%) "
                f"provides insights about your lifestyle patterns."
            )
        
        return " ".join(details_parts)
    
    def _determine_priority(
        self, 
        analysis_results: List[AnalysisResult], 
        avg_confidence: float
    ) -> InsightPriority:
        """Determine priority based on confidence and number of sources."""
        source_count = len(set(r.source for r in analysis_results))
        
        # High priority: high confidence and multiple sources
        if avg_confidence >= 80 and source_count >= 3:
            return InsightPriority.HIGH
        
        # Medium priority: moderate confidence or multiple sources
        if avg_confidence >= 60 or source_count >= 2:
            return InsightPriority.MEDIUM
        
        # Low priority: everything else
        return InsightPriority.LOW
    
    def _determine_category(self, primary_source: AnalysisSource) -> str:
        """Determine category based on primary source."""
        category_map = {
            AnalysisSource.FOOD: "Nutrition",
            AnalysisSource.WATER: "Hydration",
            AnalysisSource.SLEEP: "Sleep & Recovery",
            AnalysisSource.BODY_TYPE: "Metabolism",
            AnalysisSource.TREND: "Lifestyle Patterns"
        }
        return category_map.get(primary_source, "General Wellness")
    
    def _is_actionable(self, analysis_results: List[AnalysisResult]) -> bool:
        """Determine if the insight suggests actionable recommendations."""
        # Check if any result contains recommendation-like data
        for result in analysis_results:
            if isinstance(result.data, dict):
                # Check for common recommendation fields
                if any(key in result.data for key in ['recommendations', 'actions', 'suggestions']):
                    return True
            # Check if data has recommendations attribute
            if hasattr(result.data, 'recommendations'):
                recommendations = getattr(result.data, 'recommendations', [])
                if recommendations:
                    return True
        
        return False
    
    def _filter_redundant(self, insights: List[Insight]) -> List[Insight]:
        """Filter out redundant insights based on similarity."""
        if len(insights) <= 1:
            return insights
        
        filtered = []
        seen_categories = set()
        
        for insight in insights:
            # Create a key based on category and title similarity
            key = (insight.category, insight.title[:20])  # First 20 chars of title
            
            if key not in seen_categories:
                filtered.append(insight)
                seen_categories.add(key)
        
        return filtered
