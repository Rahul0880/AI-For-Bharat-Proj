"""Trend Analyzer for identifying patterns and correlations in user data over time."""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
import statistics


class TrendType(str, Enum):
    """Types of trends that can be detected."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    CYCLICAL = "cyclical"


class CausalityLevel(str, Enum):
    """Likelihood of causal relationship between correlated metrics."""
    LIKELY = "likely"
    POSSIBLE = "possible"
    UNLIKELY = "unlikely"


class TimeRange(BaseModel):
    """Time range for analysis."""
    start: datetime
    end: datetime


class Pattern(BaseModel):
    """Detected pattern in a metric over time."""
    metric: str = Field(description="Name of the metric")
    trend: TrendType = Field(description="Type of trend detected")
    confidence: float = Field(ge=0, le=100, description="Confidence percentage")
    description: str = Field(description="Human-readable description")
    time_range: TimeRange = Field(description="Time range of the pattern")


class Correlation(BaseModel):
    """Correlation between two metrics."""
    metric1: str = Field(description="First metric name")
    metric2: str = Field(description="Second metric name")
    strength: float = Field(ge=-1, le=1, description="Correlation strength from -1 to 1")
    description: str = Field(description="Human-readable description")
    causality: CausalityLevel = Field(description="Likelihood of causal relationship")


class Change(BaseModel):
    """Significant change detected in a metric."""
    metric: str = Field(description="Name of the metric")
    change_point: datetime = Field(description="When the change occurred")
    magnitude: float = Field(description="Size of the change")
    description: str = Field(description="Human-readable description")
    possible_causes: List[str] = Field(default_factory=list, description="Potential causes")


class ChartData(BaseModel):
    """Data for visualization."""
    metric: str = Field(description="Metric name")
    data_points: List[Tuple[datetime, float]] = Field(description="Time series data points")
    chart_type: str = Field(description="Type of chart (line, bar, etc.)")


class TrendAnalysis(BaseModel):
    """Complete trend analysis result."""
    patterns: List[Pattern] = Field(default_factory=list, description="Detected patterns")
    correlations: List[Correlation] = Field(default_factory=list, description="Detected correlations")
    significant_changes: List[Change] = Field(default_factory=list, description="Significant changes")
    visualizations: List[ChartData] = Field(default_factory=list, description="Visualization data")


class TrendAnalyzer:
    """Analyzes trends and patterns in user data over time."""
    
    def __init__(self):
        """Initialize the TrendAnalyzer."""
        self.significant_change_threshold = 0.3  # 30% change threshold
    
    def analyze_trends(
        self, 
        user_id: str, 
        time_range: TimeRange,
        data: Dict[str, List[Tuple[datetime, float]]]
    ) -> TrendAnalysis:
        """
        Analyze trends in user data over time.
        
        Args:
            user_id: User identifier
            time_range: Time range for analysis
            data: Dictionary mapping metric names to time series data [(timestamp, value), ...]
        
        Returns:
            TrendAnalysis with detected patterns, correlations, and changes
        """
        patterns = []
        significant_changes = []
        visualizations = []
        
        # Analyze each metric for patterns
        for metric, time_series in data.items():
            if len(time_series) >= 3:  # Need at least 3 points for pattern detection
                pattern = self._detect_pattern(metric, time_series, time_range)
                if pattern:
                    patterns.append(pattern)
                
                # Check for significant changes
                change = self._detect_significant_change(metric, time_series)
                if change:
                    significant_changes.append(change)
                
                # Create visualization data
                visualizations.append(ChartData(
                    metric=metric,
                    data_points=time_series,
                    chart_type="line"
                ))
        
        # Detect correlations between metrics
        correlations = self._detect_correlations(data)
        
        return TrendAnalysis(
            patterns=patterns,
            correlations=correlations,
            significant_changes=significant_changes,
            visualizations=visualizations
        )
    
    def detect_correlations(
        self,
        user_id: str,
        metric1: str,
        metric2: str,
        data1: List[Tuple[datetime, float]],
        data2: List[Tuple[datetime, float]]
    ) -> Optional[Correlation]:
        """
        Detect correlation between two specific metrics.
        
        Args:
            user_id: User identifier
            metric1: First metric name
            metric2: Second metric name
            data1: Time series data for metric1
            data2: Time series data for metric2
        
        Returns:
            Correlation if detected, None otherwise
        """
        if len(data1) < 3 or len(data2) < 3:
            return None
        
        # Align data by timestamp
        aligned_data = self._align_time_series(data1, data2)
        if len(aligned_data) < 3:
            return None
        
        values1 = [v1 for _, v1, _ in aligned_data]
        values2 = [v2 for _, _, v2 in aligned_data]
        
        # Calculate correlation coefficient
        correlation_strength = self._calculate_correlation(values1, values2)
        
        if abs(correlation_strength) < 0.3:  # Weak correlation threshold
            return None
        
        # Determine causality likelihood
        causality = self._assess_causality(metric1, metric2, correlation_strength)
        
        # Generate description
        direction = "positive" if correlation_strength > 0 else "negative"
        strength_desc = "strong" if abs(correlation_strength) > 0.7 else "moderate"
        description = f"A {strength_desc} {direction} correlation exists between {metric1} and {metric2}"
        
        return Correlation(
            metric1=metric1,
            metric2=metric2,
            strength=correlation_strength,
            description=description,
            causality=causality
        )
    
    def _detect_pattern(
        self,
        metric: str,
        time_series: List[Tuple[datetime, float]],
        time_range: TimeRange
    ) -> Optional[Pattern]:
        """Detect pattern in a time series."""
        if len(time_series) < 3:
            return None
        
        values = [v for _, v in time_series]
        
        # Calculate trend using linear regression slope
        n = len(values)
        x = list(range(n))
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(values)
        
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        if denominator == 0:
            trend = TrendType.STABLE
            confidence = 95.0
        else:
            slope = numerator / denominator
            
            # Determine trend type based on slope
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            threshold = std_dev * 0.1  # 10% of std dev
            
            if abs(slope) < threshold:
                trend = TrendType.STABLE
            elif slope > 0:
                trend = TrendType.INCREASING
            else:
                trend = TrendType.DECREASING
            
            # Calculate confidence based on R-squared
            ss_tot = sum((v - mean_y) ** 2 for v in values)
            predicted = [mean_y + slope * (i - mean_x) for i in range(n)]
            ss_res = sum((values[i] - predicted[i]) ** 2 for i in range(n))
            
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            confidence = max(50.0, min(100.0, r_squared * 100))
        
        description = f"The {metric} shows a {trend.value} trend over the analyzed period"
        
        return Pattern(
            metric=metric,
            trend=trend,
            confidence=confidence,
            description=description,
            time_range=time_range
        )
    
    def _detect_significant_change(
        self,
        metric: str,
        time_series: List[Tuple[datetime, float]]
    ) -> Optional[Change]:
        """Detect significant changes in a metric."""
        if len(time_series) < 7:  # Need at least a week of data
            return None
        
        values = [v for _, v in time_series]
        timestamps = [t for t, _ in time_series]
        
        # Calculate baseline (first half average)
        midpoint = len(values) // 2
        baseline = statistics.mean(values[:midpoint])
        
        if baseline == 0:
            return None
        
        # Check for significant changes in second half
        for i in range(midpoint, len(values)):
            change_pct = abs(values[i] - baseline) / baseline
            
            if change_pct > self.significant_change_threshold:
                magnitude = values[i] - baseline
                direction = "increased" if magnitude > 0 else "decreased"
                pct_change = int(change_pct * 100)
                
                description = f"{metric} {direction} by {pct_change}% from baseline"
                
                return Change(
                    metric=metric,
                    change_point=timestamps[i],
                    magnitude=magnitude,
                    description=description,
                    possible_causes=[]  # Would be populated with domain knowledge
                )
        
        return None
    
    def _detect_correlations(
        self,
        data: Dict[str, List[Tuple[datetime, float]]]
    ) -> List[Correlation]:
        """Detect correlations between all metric pairs."""
        correlations = []
        metrics = list(data.keys())
        
        # Check all pairs of metrics
        for i in range(len(metrics)):
            for j in range(i + 1, len(metrics)):
                metric1, metric2 = metrics[i], metrics[j]
                correlation = self.detect_correlations(
                    user_id="",  # Not used in this context
                    metric1=metric1,
                    metric2=metric2,
                    data1=data[metric1],
                    data2=data[metric2]
                )
                if correlation:
                    correlations.append(correlation)
        
        return correlations
    
    def _align_time_series(
        self,
        data1: List[Tuple[datetime, float]],
        data2: List[Tuple[datetime, float]]
    ) -> List[Tuple[datetime, float, float]]:
        """Align two time series by matching timestamps."""
        # Create dictionaries for fast lookup
        dict1 = {t: v for t, v in data1}
        dict2 = {t: v for t, v in data2}
        
        # Find common timestamps
        common_timestamps = set(dict1.keys()) & set(dict2.keys())
        
        # Return aligned data
        return [(t, dict1[t], dict2[t]) for t in sorted(common_timestamps)]
    
    def _calculate_correlation(
        self,
        values1: List[float],
        values2: List[float]
    ) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(values1) != len(values2) or len(values1) < 2:
            return 0.0
        
        n = len(values1)
        mean1 = statistics.mean(values1)
        mean2 = statistics.mean(values2)
        
        numerator = sum((values1[i] - mean1) * (values2[i] - mean2) for i in range(n))
        
        std1 = statistics.stdev(values1) if len(values1) > 1 else 0
        std2 = statistics.stdev(values2) if len(values2) > 1 else 0
        
        denominator = std1 * std2 * n
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _assess_causality(
        self,
        metric1: str,
        metric2: str,
        correlation_strength: float
    ) -> CausalityLevel:
        """Assess likelihood of causal relationship based on domain knowledge."""
        # Domain-specific causality rules
        causal_pairs = {
            ("caffeine", "sleep_quality"): CausalityLevel.LIKELY,
            ("sodium", "water_retention"): CausalityLevel.LIKELY,
            ("water_intake", "water_retention"): CausalityLevel.LIKELY,
            ("sleep_quality", "stress"): CausalityLevel.POSSIBLE,
            ("food_quality", "energy"): CausalityLevel.LIKELY,
        }
        
        # Check if this pair has known causality
        pair_key = (metric1.lower(), metric2.lower())
        reverse_key = (metric2.lower(), metric1.lower())
        
        if pair_key in causal_pairs:
            return causal_pairs[pair_key]
        elif reverse_key in causal_pairs:
            return causal_pairs[reverse_key]
        
        # Default assessment based on correlation strength
        if abs(correlation_strength) > 0.7:
            return CausalityLevel.POSSIBLE
        else:
            return CausalityLevel.UNLIKELY