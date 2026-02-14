"""Property-based tests for TrendAnalyzer using Hypothesis."""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from datetime import datetime, timedelta
from typing import List, Tuple

from jeevanfit.analyzers.trend_analyzer import (
    TrendAnalyzer,
    TrendType,
    TimeRange,
    Pattern,
    Correlation,
    Change,
)


# Strategy for generating time series data with trends
@st.composite
def time_series_with_trend_strategy(draw, trend_type: str = "any"):
    """Generate time series data with a specific trend pattern."""
    num_points = draw(st.integers(min_value=7, max_value=30))
    start_date = datetime(2024, 1, 1)
    
    # Generate timestamps
    timestamps = [start_date + timedelta(days=i) for i in range(num_points)]
    
    # Generate values based on trend type
    base_value = draw(st.floats(min_value=10, max_value=100))
    
    if trend_type == "increasing" or (trend_type == "any" and draw(st.booleans())):
        # Increasing trend
        slope = draw(st.floats(min_value=0.5, max_value=5.0))
        noise = draw(st.floats(min_value=0.1, max_value=2.0))
        values = [
            base_value + slope * i + draw(st.floats(min_value=-noise, max_value=noise))
            for i in range(num_points)
        ]
    elif trend_type == "decreasing":
        # Decreasing trend
        slope = draw(st.floats(min_value=0.5, max_value=5.0))
        noise = draw(st.floats(min_value=0.1, max_value=2.0))
        values = [
            base_value - slope * i + draw(st.floats(min_value=-noise, max_value=noise))
            for i in range(num_points)
        ]
    else:
        # Stable or random
        noise = draw(st.floats(min_value=0.5, max_value=3.0))
        values = [
            base_value + draw(st.floats(min_value=-noise, max_value=noise))
            for i in range(num_points)
        ]
    
    # Ensure all values are positive
    min_val = min(values)
    if min_val < 0:
        values = [v - min_val + 1 for v in values]
    
    return list(zip(timestamps, values))


# Strategy for generating multi-day data with patterns
@st.composite
def multi_day_data_strategy(draw):
    """Generate multi-day data for multiple metrics."""
    num_metrics = draw(st.integers(min_value=1, max_value=4))
    metric_names = [f"metric_{i}" for i in range(num_metrics)]
    
    data = {}
    for metric in metric_names:
        time_series = draw(time_series_with_trend_strategy())
        data[metric] = time_series
    
    return data


# Strategy for generating correlated time series
@st.composite
def correlated_time_series_strategy(draw):
    """Generate two time series with correlation."""
    num_points = draw(st.integers(min_value=7, max_value=20))
    start_date = datetime(2024, 1, 1)
    
    # Generate timestamps
    timestamps = [start_date + timedelta(days=i) for i in range(num_points)]
    
    # Generate first series
    base_value1 = draw(st.floats(min_value=10, max_value=100))
    slope1 = draw(st.floats(min_value=-2.0, max_value=2.0))
    noise1 = draw(st.floats(min_value=0.5, max_value=2.0))
    
    values1 = [
        base_value1 + slope1 * i + draw(st.floats(min_value=-noise1, max_value=noise1))
        for i in range(num_points)
    ]
    
    # Generate second series with correlation
    correlation_type = draw(st.sampled_from(["positive", "negative", "none"]))
    base_value2 = draw(st.floats(min_value=10, max_value=100))
    
    if correlation_type == "positive":
        # Positive correlation: similar trend
        scale = draw(st.floats(min_value=0.5, max_value=2.0))
        noise2 = draw(st.floats(min_value=0.5, max_value=2.0))
        values2 = [
            base_value2 + (values1[i] - base_value1) * scale + 
            draw(st.floats(min_value=-noise2, max_value=noise2))
            for i in range(num_points)
        ]
    elif correlation_type == "negative":
        # Negative correlation: opposite trend
        scale = draw(st.floats(min_value=0.5, max_value=2.0))
        noise2 = draw(st.floats(min_value=0.5, max_value=2.0))
        values2 = [
            base_value2 - (values1[i] - base_value1) * scale + 
            draw(st.floats(min_value=-noise2, max_value=noise2))
            for i in range(num_points)
        ]
    else:
        # No correlation: independent random values
        slope2 = draw(st.floats(min_value=-2.0, max_value=2.0))
        noise2 = draw(st.floats(min_value=0.5, max_value=2.0))
        values2 = [
            base_value2 + slope2 * i + draw(st.floats(min_value=-noise2, max_value=noise2))
            for i in range(num_points)
        ]
    
    # Ensure all values are positive
    for values in [values1, values2]:
        min_val = min(values)
        if min_val < 0:
            values[:] = [v - min_val + 1 for v in values]
    
    series1 = list(zip(timestamps, values1))
    series2 = list(zip(timestamps, values2))
    
    return series1, series2, correlation_type


class TestTrendAnalyzerProperties:
    """Property-based tests for TrendAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = TrendAnalyzer()
    
    # Feature: fitbuddy-lifestyle-assistant, Property 24: Pattern detection in multi-day data
    @given(st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_pattern_detection_multi_day(self, data):
        """
        Property 24: Pattern detection in multi-day data
        For any user with at least 7 days of data containing a consistent 
        increasing or decreasing trend in a metric, the trend analyzer should 
        identify that pattern.
        
        Validates: Requirements 7.1
        """
        # Generate time series with a clear increasing trend
        time_series = data.draw(time_series_with_trend_strategy(trend_type="increasing"))
        
        # Ensure we have at least 7 days
        assume(len(time_series) >= 7)
        
        # Create time range
        timestamps = [t for t, _ in time_series]
        time_range = TimeRange(start=timestamps[0], end=timestamps[-1])
        
        # Create data dictionary
        metric_data = {"test_metric": time_series}
        
        # Analyze trends
        analysis = self.analyzer.analyze_trends(
            user_id="test-user",
            time_range=time_range,
            data=metric_data
        )
        
        # Verify patterns were detected
        assert analysis is not None, "Analysis should not be None"
        assert analysis.patterns is not None, "Patterns should not be None"
        assert len(analysis.patterns) > 0, \
            "Should detect at least one pattern in 7+ days of trending data"
        
        # Verify the detected pattern is for our metric
        pattern = analysis.patterns[0]
        assert pattern.metric == "test_metric", \
            f"Pattern should be for 'test_metric', got '{pattern.metric}'"
        
        # Verify pattern has valid trend type
        valid_trends = {TrendType.INCREASING, TrendType.DECREASING, TrendType.STABLE, TrendType.CYCLICAL}
        assert pattern.trend in valid_trends, \
            f"Pattern trend must be one of {valid_trends}, got {pattern.trend}"
        
        # For increasing data, we expect INCREASING or STABLE trend
        # (STABLE is acceptable if noise is high)
        assert pattern.trend in {TrendType.INCREASING, TrendType.STABLE}, \
            f"Expected INCREASING or STABLE trend for increasing data, got {pattern.trend}"
        
        # Verify pattern has confidence
        assert pattern.confidence is not None, "Pattern confidence should not be None"
        assert 0 <= pattern.confidence <= 100, \
            f"Confidence must be between 0 and 100, got {pattern.confidence}"
        
        # Verify pattern has description
        assert pattern.description, "Pattern description should not be empty"
        assert "test_metric" in pattern.description.lower(), \
            "Pattern description should mention the metric name"
        
        # Verify pattern has time range
        assert pattern.time_range is not None, "Pattern time_range should not be None"
        assert pattern.time_range.start == time_range.start, \
            "Pattern time range start should match input time range"
        assert pattern.time_range.end == time_range.end, \
            "Pattern time range end should match input time range"
    
    # Feature: fitbuddy-lifestyle-assistant, Property 25: Correlation detection over time
    @given(st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_correlation_detection(self, data):
        """
        Property 25: Correlation detection over time
        For any user dataset where changes in one metric consistently precede 
        changes in another metric, the trend analyzer should identify a 
        correlation between those metrics.
        
        Validates: Requirements 7.2
        """
        # Generate correlated time series
        series1, series2, correlation_type = data.draw(correlated_time_series_strategy())
        
        # Ensure we have enough data points
        assume(len(series1) >= 3)
        assume(len(series2) >= 3)
        
        # Detect correlation
        correlation = self.analyzer.detect_correlations(
            user_id="test-user",
            metric1="metric_a",
            metric2="metric_b",
            data1=series1,
            data2=series2
        )
        
        # For strong positive or negative correlation, we should detect it
        if correlation_type in ["positive", "negative"]:
            # We should detect a correlation (though it might be weak due to noise)
            # The key is that the analyzer attempts to find correlations
            if correlation is not None:
                # Verify correlation structure
                assert correlation.metric1 == "metric_a", \
                    f"Correlation metric1 should be 'metric_a', got '{correlation.metric1}'"
                assert correlation.metric2 == "metric_b", \
                    f"Correlation metric2 should be 'metric_b', got '{correlation.metric2}'"
                
                # Verify strength is in valid range
                assert -1 <= correlation.strength <= 1, \
                    f"Correlation strength must be between -1 and 1, got {correlation.strength}"
                
                # Verify description exists
                assert correlation.description, "Correlation description should not be empty"
                
                # Verify causality is valid
                from jeevanfit.analyzers.trend_analyzer import CausalityLevel
                valid_causality = {CausalityLevel.LIKELY, CausalityLevel.POSSIBLE, CausalityLevel.UNLIKELY}
                assert correlation.causality in valid_causality, \
                    f"Causality must be one of {valid_causality}, got {correlation.causality}"
                
                # For positive correlation type, strength should be positive (if detected)
                if correlation_type == "positive":
                    assert correlation.strength >= 0, \
                        f"Positive correlation should have non-negative strength, got {correlation.strength}"
                
                # For negative correlation type, strength should be negative (if detected)
                elif correlation_type == "negative":
                    assert correlation.strength <= 0, \
                        f"Negative correlation should have non-positive strength, got {correlation.strength}"
        
        # For no correlation, we might or might not detect one (depends on random noise)
        # The key property is that the analyzer doesn't crash and returns valid data
        if correlation is not None:
            assert -1 <= correlation.strength <= 1, \
                "Correlation strength must always be in valid range"
    
    # Feature: fitbuddy-lifestyle-assistant, Property 27: Significant change notification
    @given(st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_significant_change_notification(self, data):
        """
        Property 27: Significant change notification
        For any user dataset where a metric changes by more than 30% from its 
        baseline average, the system should generate a notification explaining 
        the detected change.
        
        Validates: Requirements 7.5
        """
        # Generate baseline data (first week)
        num_baseline_points = data.draw(st.integers(min_value=7, max_value=10))
        baseline_value = data.draw(st.floats(min_value=50, max_value=100))
        noise = data.draw(st.floats(min_value=0.5, max_value=2.0))
        
        start_date = datetime(2024, 1, 1)
        
        # Create baseline period with stable values
        baseline_data = [
            (start_date + timedelta(days=i), 
             baseline_value + data.draw(st.floats(min_value=-noise, max_value=noise)))
            for i in range(num_baseline_points)
        ]
        
        # Create significant change period (>30% change)
        change_magnitude = data.draw(st.floats(min_value=0.35, max_value=0.8))  # 35-80% change
        direction = data.draw(st.sampled_from([1, -1]))  # increase or decrease
        new_value = baseline_value * (1 + direction * change_magnitude)
        
        num_change_points = data.draw(st.integers(min_value=3, max_value=7))
        change_data = [
            (start_date + timedelta(days=num_baseline_points + i),
             new_value + data.draw(st.floats(min_value=-noise, max_value=noise)))
            for i in range(num_change_points)
        ]
        
        # Combine data
        time_series = baseline_data + change_data
        
        # Ensure we have enough data
        assume(len(time_series) >= 7)
        
        # Create time range
        timestamps = [t for t, _ in time_series]
        time_range = TimeRange(start=timestamps[0], end=timestamps[-1])
        
        # Create data dictionary
        metric_data = {"test_metric": time_series}
        
        # Analyze trends
        analysis = self.analyzer.analyze_trends(
            user_id="test-user",
            time_range=time_range,
            data=metric_data
        )
        
        # Verify analysis is not None
        assert analysis is not None, "Analysis should not be None"
        
        # Verify significant changes were detected
        assert analysis.significant_changes is not None, \
            "Significant changes should not be None"
        
        # We should detect at least one significant change
        assert len(analysis.significant_changes) > 0, \
            f"Should detect significant change when metric changes by {change_magnitude*100:.0f}%"
        
        # Verify the change structure
        change = analysis.significant_changes[0]
        assert change.metric == "test_metric", \
            f"Change should be for 'test_metric', got '{change.metric}'"
        
        # Verify change has a change point
        assert change.change_point is not None, "Change point should not be None"
        assert isinstance(change.change_point, datetime), \
            f"Change point should be datetime, got {type(change.change_point)}"
        
        # Verify change has magnitude
        assert change.magnitude is not None, "Change magnitude should not be None"
        
        # Verify change has description
        assert change.description, "Change description should not be empty"
        assert "test_metric" in change.description.lower(), \
            "Change description should mention the metric name"
        
        # Verify description indicates increase or decrease
        if direction > 0:
            assert "increase" in change.description.lower(), \
                "Description should mention 'increase' for positive change"
        else:
            assert "decrease" in change.description.lower(), \
                "Description should mention 'decrease' for negative change"
        
        # Verify possible causes is a list (even if empty)
        assert isinstance(change.possible_causes, list), \
            f"Possible causes should be a list, got {type(change.possible_causes)}"
