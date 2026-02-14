"""Unit tests for SleepAnalyzer."""

import pytest
from datetime import datetime, time

from jeevanfit.analyzers import (
    SleepAnalyzer,
    SleepQuality,
    ImpactType,
    SleepDisruptorType,
    RecommendationPriority
)
from jeevanfit.models import (
    LifestyleInput,
    FoodItem,
    NutritionalInfo,
    SleepData,
    Habit,
    HabitType
)


class TestSleepAnalyzer:
    """Test suite for SleepAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a SleepAnalyzer instance."""
        return SleepAnalyzer()
    
    @pytest.fixture
    def good_sleep_data(self):
        """Create good quality sleep data."""
        return SleepData(
            duration=8.0,
            quality=9,
            bedtime=time(22, 0),
            wake_time=time(6, 0),
            interruptions=0,
            timestamp=datetime.now()
        )
    
    @pytest.fixture
    def poor_sleep_data(self):
        """Create poor quality sleep data."""
        return SleepData(
            duration=5.5,
            quality=4,
            bedtime=time(23, 30),
            wake_time=time(5, 0),
            interruptions=3,
            timestamp=datetime.now()
        )
    
    @pytest.fixture
    def optimal_lifestyle(self):
        """Create lifestyle input with optimal conditions."""
        return LifestyleInput(
            food_items=[],
            water_intake=2500,
            sleep_data=None,  # Will be set in tests
            daily_habits=[],
            user_id="test-user",
            timestamp=datetime(2024, 1, 15, 18, 0)  # 6 PM
        )
    
    def test_analyze_sleep_with_good_conditions(self, analyzer, good_sleep_data, optimal_lifestyle):
        """Test sleep analysis with good sleep and optimal conditions."""
        optimal_lifestyle.sleep_data = good_sleep_data
        
        analysis = analyzer.analyze_sleep(good_sleep_data, optimal_lifestyle)
        
        assert analysis.overall_quality in [SleepQuality.GOOD, SleepQuality.EXCELLENT]
        assert isinstance(analysis.correlations, list)
        assert isinstance(analysis.recommendations, list)
        assert analysis.explanation
        assert len(analysis.explanation) > 0
    
    def test_analyze_sleep_with_poor_conditions(self, analyzer, poor_sleep_data, optimal_lifestyle):
        """Test sleep analysis with poor sleep quality."""
        optimal_lifestyle.sleep_data = poor_sleep_data
        
        analysis = analyzer.analyze_sleep(poor_sleep_data, optimal_lifestyle)
        
        assert analysis.overall_quality in [SleepQuality.POOR, SleepQuality.FAIR]
        assert len(analysis.recommendations) > 0
    
    def test_analyze_sleep_with_late_caffeine(self, analyzer, good_sleep_data, optimal_lifestyle):
        """Test sleep analysis detects late caffeine consumption."""
        # Add caffeine 4 hours before bedtime (22:00 - 4h = 18:00)
        caffeine_habit = Habit(
            type=HabitType.CAFFEINE,
            intensity=7,
            duration=0.25,
            timing=time(18, 0),
            notes="Evening coffee"
        )
        optimal_lifestyle.daily_habits.append(caffeine_habit)
        optimal_lifestyle.sleep_data = good_sleep_data
        
        analysis = analyzer.analyze_sleep(good_sleep_data, optimal_lifestyle)
        
        # Should identify caffeine as a negative correlation
        caffeine_correlations = [
            c for c in analysis.correlations
            if "caffeine" in c.habit.lower()
        ]
        assert len(caffeine_correlations) > 0
        assert caffeine_correlations[0].impact == ImpactType.NEGATIVE
    
    def test_analyze_sleep_with_high_stress(self, analyzer, poor_sleep_data, optimal_lifestyle):
        """Test sleep analysis detects high stress impact."""
        stress_habit = Habit(
            type=HabitType.STRESS,
            intensity=9,
            duration=6.0,
            timing=time(14, 0),
            notes="Work stress"
        )
        optimal_lifestyle.daily_habits.append(stress_habit)
        optimal_lifestyle.sleep_data = poor_sleep_data
        
        analysis = analyzer.analyze_sleep(poor_sleep_data, optimal_lifestyle)
        
        # Should identify stress as a negative correlation
        stress_correlations = [
            c for c in analysis.correlations
            if "stress" in c.habit.lower()
        ]
        assert len(stress_correlations) > 0
        assert stress_correlations[0].impact == ImpactType.NEGATIVE
    
    def test_analyze_sleep_with_dehydration(self, analyzer, poor_sleep_data, optimal_lifestyle):
        """Test sleep analysis detects dehydration impact."""
        optimal_lifestyle.water_intake = 1000  # Low water intake
        optimal_lifestyle.sleep_data = poor_sleep_data
        
        analysis = analyzer.analyze_sleep(poor_sleep_data, optimal_lifestyle)
        
        # Should identify hydration as a factor
        hydration_correlations = [
            c for c in analysis.correlations
            if "water" in c.habit.lower() or "hydration" in c.habit.lower()
        ]
        assert len(hydration_correlations) > 0
    
    def test_identify_sleep_disruptors_caffeine(self, analyzer, optimal_lifestyle):
        """Test identification of caffeine as a sleep disruptor."""
        optimal_lifestyle.sleep_data = SleepData(
            duration=7.0,
            quality=6,
            bedtime=time(22, 0),
            wake_time=time(5, 0),
            interruptions=1,
            timestamp=datetime.now()
        )
        
        # Add late caffeine
        caffeine_habit = Habit(
            type=HabitType.CAFFEINE,
            intensity=8,
            duration=0.5,
            timing=time(19, 0),  # 3 hours before bed
            notes="Late coffee"
        )
        optimal_lifestyle.daily_habits.append(caffeine_habit)
        
        disruptors = analyzer.identify_sleep_disruptors(optimal_lifestyle)
        
        # Should identify caffeine disruptor
        caffeine_disruptors = [d for d in disruptors if d.type == SleepDisruptorType.CAFFEINE]
        assert len(caffeine_disruptors) > 0
        assert caffeine_disruptors[0].severity > 0
        assert caffeine_disruptors[0].recommendation
    
    def test_identify_sleep_disruptors_late_eating(self, analyzer, optimal_lifestyle):
        """Test identification of late eating as a sleep disruptor."""
        optimal_lifestyle.sleep_data = SleepData(
            duration=7.0,
            quality=6,
            bedtime=time(22, 0),
            wake_time=time(5, 0),
            interruptions=1,
            timestamp=datetime.now()
        )
        
        # Set timestamp to indicate eating close to bedtime
        optimal_lifestyle.timestamp = datetime(2024, 1, 15, 20, 30)  # 1.5 hours before bed
        
        # Add food items
        food = FoodItem(
            name="Late dinner",
            serving_size=300,
            unit="g",
            nutritional_info=NutritionalInfo(
                calories=500,
                protein=25,
                carbohydrates=50,
                fat=20,
                sodium=600,
                sugar=5,
                fiber=4,
                preservatives=[],
                processing_level=2
            )
        )
        optimal_lifestyle.food_items.append(food)
        
        disruptors = analyzer.identify_sleep_disruptors(optimal_lifestyle)
        
        # Should identify late eating disruptor
        eating_disruptors = [d for d in disruptors if d.type == SleepDisruptorType.LATE_EATING]
        assert len(eating_disruptors) > 0
    
    def test_identify_sleep_disruptors_stress(self, analyzer, optimal_lifestyle):
        """Test identification of stress as a sleep disruptor."""
        optimal_lifestyle.sleep_data = SleepData(
            duration=6.5,
            quality=5,
            bedtime=time(23, 0),
            wake_time=time(5, 30),
            interruptions=2,
            timestamp=datetime.now()
        )
        
        # Add high stress
        stress_habit = Habit(
            type=HabitType.STRESS,
            intensity=8,
            duration=5.0,
            notes="High stress day"
        )
        optimal_lifestyle.daily_habits.append(stress_habit)
        
        disruptors = analyzer.identify_sleep_disruptors(optimal_lifestyle)
        
        # Should identify stress disruptor
        stress_disruptors = [d for d in disruptors if d.type == SleepDisruptorType.STRESS]
        assert len(stress_disruptors) > 0
        assert stress_disruptors[0].severity >= 6
    
    def test_identify_sleep_disruptors_screen_time(self, analyzer, optimal_lifestyle):
        """Test identification of screen time as a sleep disruptor."""
        optimal_lifestyle.sleep_data = SleepData(
            duration=7.0,
            quality=6,
            bedtime=time(22, 0),
            wake_time=time(5, 0),
            interruptions=1,
            timestamp=datetime.now()
        )
        
        # Add late screen time
        screen_habit = Habit(
            type=HabitType.SCREEN_TIME,
            intensity=6,
            duration=2.0,
            timing=time(21, 0),  # 1 hour before bed
            notes="Phone before bed"
        )
        optimal_lifestyle.daily_habits.append(screen_habit)
        
        disruptors = analyzer.identify_sleep_disruptors(optimal_lifestyle)
        
        # Should identify screen time disruptor
        screen_disruptors = [d for d in disruptors if d.type == SleepDisruptorType.SCREEN_TIME]
        assert len(screen_disruptors) > 0
    
    def test_identify_sleep_disruptors_dehydration(self, analyzer, optimal_lifestyle):
        """Test identification of dehydration as a sleep disruptor."""
        optimal_lifestyle.sleep_data = SleepData(
            duration=7.0,
            quality=6,
            bedtime=time(22, 0),
            wake_time=time(5, 0),
            interruptions=1,
            timestamp=datetime.now()
        )
        
        optimal_lifestyle.water_intake = 1200  # Low water
        
        disruptors = analyzer.identify_sleep_disruptors(optimal_lifestyle)
        
        # Should identify dehydration disruptor
        dehydration_disruptors = [d for d in disruptors if d.type == SleepDisruptorType.DEHYDRATION]
        assert len(dehydration_disruptors) > 0
    
    def test_disruptors_sorted_by_severity(self, analyzer, optimal_lifestyle):
        """Test that disruptors are sorted by severity."""
        optimal_lifestyle.sleep_data = SleepData(
            duration=6.0,
            quality=5,
            bedtime=time(22, 0),
            wake_time=time(4, 0),
            interruptions=2,
            timestamp=datetime.now()
        )
        
        # Add multiple disruptors with different severities
        optimal_lifestyle.daily_habits.extend([
            Habit(type=HabitType.CAFFEINE, intensity=7, timing=time(19, 0)),
            Habit(type=HabitType.STRESS, intensity=9, duration=4.0),
            Habit(type=HabitType.SCREEN_TIME, intensity=5, timing=time(21, 30))
        ])
        optimal_lifestyle.water_intake = 1300
        
        disruptors = analyzer.identify_sleep_disruptors(optimal_lifestyle)
        
        # Should be sorted by severity (highest first)
        if len(disruptors) > 1:
            for i in range(len(disruptors) - 1):
                assert disruptors[i].severity >= disruptors[i + 1].severity
    
    def test_recommendations_generated(self, analyzer, poor_sleep_data, optimal_lifestyle):
        """Test that recommendations are generated for poor sleep."""
        optimal_lifestyle.sleep_data = poor_sleep_data
        
        # Add some disruptors
        optimal_lifestyle.daily_habits.append(
            Habit(type=HabitType.CAFFEINE, intensity=7, timing=time(18, 0))
        )
        optimal_lifestyle.water_intake = 1200
        
        analysis = analyzer.analyze_sleep(poor_sleep_data, optimal_lifestyle)
        
        # Should have recommendations
        assert len(analysis.recommendations) > 0
        
        # All recommendations should have required fields
        for rec in analysis.recommendations:
            assert rec.priority in [
                RecommendationPriority.HIGH,
                RecommendationPriority.MEDIUM,
                RecommendationPriority.LOW
            ]
            assert rec.action
            assert rec.rationale
            assert rec.expected_impact
    
    def test_recommendations_prioritized(self, analyzer, poor_sleep_data, optimal_lifestyle):
        """Test that recommendations are prioritized correctly."""
        optimal_lifestyle.sleep_data = poor_sleep_data
        
        # Add multiple disruptors
        optimal_lifestyle.daily_habits.extend([
            Habit(type=HabitType.CAFFEINE, intensity=8, timing=time(19, 0)),
            Habit(type=HabitType.STRESS, intensity=9, duration=5.0)
        ])
        
        analysis = analyzer.analyze_sleep(poor_sleep_data, optimal_lifestyle)
        
        # High priority recommendations should come first
        if len(analysis.recommendations) > 1:
            priority_order = {
                RecommendationPriority.HIGH: 0,
                RecommendationPriority.MEDIUM: 1,
                RecommendationPriority.LOW: 2
            }
            for i in range(len(analysis.recommendations) - 1):
                current_priority = priority_order[analysis.recommendations[i].priority]
                next_priority = priority_order[analysis.recommendations[i + 1].priority]
                assert current_priority <= next_priority
    
    def test_overall_quality_assessment_excellent(self, analyzer):
        """Test overall quality assessment for excellent sleep."""
        excellent_sleep = SleepData(
            duration=8.0,
            quality=9,
            bedtime=time(22, 0),
            wake_time=time(6, 0),
            interruptions=0,
            timestamp=datetime.now()
        )
        
        quality = analyzer._assess_overall_quality(excellent_sleep)
        assert quality == SleepQuality.EXCELLENT
    
    def test_overall_quality_assessment_poor(self, analyzer):
        """Test overall quality assessment for poor sleep."""
        poor_sleep = SleepData(
            duration=5.0,
            quality=3,
            bedtime=time(1, 0),
            wake_time=time(6, 0),
            interruptions=4,
            timestamp=datetime.now()
        )
        
        quality = analyzer._assess_overall_quality(poor_sleep)
        assert quality == SleepQuality.POOR
    
    def test_overall_quality_downgrade_for_short_duration(self, analyzer):
        """Test that short sleep duration downgrades quality."""
        short_sleep = SleepData(
            duration=5.5,  # Short duration
            quality=9,  # High quality rating
            bedtime=time(1, 0),
            wake_time=time(6, 30),
            interruptions=0,
            timestamp=datetime.now()
        )
        
        quality = analyzer._assess_overall_quality(short_sleep)
        # Should be downgraded from EXCELLENT
        assert quality in [SleepQuality.GOOD, SleepQuality.FAIR]
    
    def test_overall_quality_downgrade_for_interruptions(self, analyzer):
        """Test that frequent interruptions downgrade quality."""
        interrupted_sleep = SleepData(
            duration=8.0,
            quality=9,
            bedtime=time(22, 0),
            wake_time=time(6, 0),
            interruptions=4,  # Many interruptions
            timestamp=datetime.now()
        )
        
        quality = analyzer._assess_overall_quality(interrupted_sleep)
        # Should be downgraded from EXCELLENT
        assert quality in [SleepQuality.GOOD, SleepQuality.FAIR]
    
    def test_explanation_includes_sleep_metrics(self, analyzer, good_sleep_data, optimal_lifestyle):
        """Test that explanation includes key sleep metrics."""
        optimal_lifestyle.sleep_data = good_sleep_data
        
        analysis = analyzer.analyze_sleep(good_sleep_data, optimal_lifestyle)
        
        # Explanation should mention duration and quality
        assert str(good_sleep_data.duration) in analysis.explanation or "hour" in analysis.explanation.lower()
        assert str(good_sleep_data.quality) in analysis.explanation
    
    def test_explanation_mentions_interruptions(self, analyzer, optimal_lifestyle):
        """Test that explanation mentions sleep interruptions."""
        interrupted_sleep = SleepData(
            duration=7.5,
            quality=6,
            bedtime=time(22, 0),
            wake_time=time(5, 30),
            interruptions=3,
            timestamp=datetime.now()
        )
        optimal_lifestyle.sleep_data = interrupted_sleep
        
        analysis = analyzer.analyze_sleep(interrupted_sleep, optimal_lifestyle)
        
        # Should mention interruptions
        assert "interruption" in analysis.explanation.lower()
    
    def test_calculate_hours_between_same_day(self, analyzer):
        """Test hour calculation for times on the same day."""
        earlier = time(14, 0)  # 2 PM
        later = time(22, 0)    # 10 PM
        
        hours = analyzer._calculate_hours_between(earlier, later)
        
        assert hours == 8.0
    
    def test_calculate_hours_between_crossing_midnight(self, analyzer):
        """Test hour calculation for times crossing midnight."""
        earlier = time(20, 0)  # 8 PM
        later = time(2, 0)     # 2 AM next day
        
        hours = analyzer._calculate_hours_between(earlier, later)
        
        assert hours == 6.0
    
    def test_no_disruptors_with_optimal_conditions(self, analyzer, optimal_lifestyle):
        """Test that no disruptors are identified with optimal conditions."""
        optimal_lifestyle.sleep_data = SleepData(
            duration=8.0,
            quality=9,
            bedtime=time(22, 0),
            wake_time=time(6, 0),
            interruptions=0,
            timestamp=datetime.now()
        )
        optimal_lifestyle.water_intake = 2500
        
        disruptors = analyzer.identify_sleep_disruptors(optimal_lifestyle)
        
        # Should have no or minimal disruptors
        assert len(disruptors) == 0
    
    def test_early_caffeine_not_flagged(self, analyzer, optimal_lifestyle):
        """Test that early caffeine consumption is not flagged as disruptor."""
        optimal_lifestyle.sleep_data = SleepData(
            duration=8.0,
            quality=8,
            bedtime=time(22, 0),
            wake_time=time(6, 0),
            interruptions=0,
            timestamp=datetime.now()
        )
        
        # Add early caffeine (more than 6 hours before bed)
        early_caffeine = Habit(
            type=HabitType.CAFFEINE,
            intensity=7,
            duration=0.25,
            timing=time(10, 0),  # 12 hours before bed
            notes="Morning coffee"
        )
        optimal_lifestyle.daily_habits.append(early_caffeine)
        
        disruptors = analyzer.identify_sleep_disruptors(optimal_lifestyle)
        
        # Should not have caffeine disruptor
        caffeine_disruptors = [d for d in disruptors if d.type == SleepDisruptorType.CAFFEINE]
        assert len(caffeine_disruptors) == 0
