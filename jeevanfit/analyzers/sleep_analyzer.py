"""Sleep analysis analyzer for JeevanFit."""

from datetime import time, datetime, timedelta
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from jeevanfit.models.core import LifestyleInput, SleepData, HabitType


class SleepQuality(str, Enum):
    """Overall sleep quality classifications."""
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class ImpactType(str, Enum):
    """Type of impact a habit has on sleep."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SleepDisruptorType(str, Enum):
    """Types of sleep disruptors."""
    CAFFEINE = "caffeine"
    LATE_EATING = "late_eating"
    DEHYDRATION = "dehydration"
    STRESS = "stress"
    SCREEN_TIME = "screen_time"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SleepCorrelation(BaseModel):
    """Correlation between a habit and sleep quality."""
    habit: str = Field(description="Description of the habit")
    impact: ImpactType = Field(description="Type of impact on sleep")
    strength: int = Field(ge=1, le=10, description="Strength of correlation")
    description: str = Field(description="Explanation of the correlation")


class SleepDisruptor(BaseModel):
    """Specific habit or factor disrupting sleep."""
    type: SleepDisruptorType = Field(description="Type of sleep disruptor")
    severity: int = Field(ge=1, le=10, description="Severity of disruption")
    timing: str = Field(description="When the disruptor occurred")
    recommendation: str = Field(description="Recommendation to address disruptor")


class Recommendation(BaseModel):
    """Actionable recommendation for sleep improvement."""
    priority: RecommendationPriority = Field(description="Priority level")
    action: str = Field(description="Specific action to take")
    rationale: str = Field(description="Why this action helps")
    expected_impact: str = Field(description="Expected improvement from action")


class SleepAnalysis(BaseModel):
    """Complete sleep analysis result."""
    overall_quality: SleepQuality = Field(description="Overall sleep quality assessment")
    correlations: List[SleepCorrelation] = Field(description="Habit-sleep correlations")
    recommendations: List[Recommendation] = Field(description="Actionable recommendations")
    explanation: str = Field(description="Comprehensive explanation")


class SleepAnalyzer:
    """Analyzes sleep quality and identifies correlations with lifestyle habits."""
    
    # Analysis thresholds
    CAFFEINE_CUTOFF_HOURS = 6  # Hours before bedtime
    LATE_EATING_CUTOFF_HOURS = 3  # Hours before bedtime
    LOW_WATER_THRESHOLD = 1500  # ml per day
    OPTIMAL_WATER_MIN = 2000  # ml per day
    HIGH_STRESS_THRESHOLD = 7  # intensity score
    MODERATE_STRESS_THRESHOLD = 5  # intensity score
    POOR_SLEEP_QUALITY = 5  # quality score
    FAIR_SLEEP_QUALITY = 7  # quality score
    GOOD_SLEEP_QUALITY = 8  # quality score
    OPTIMAL_SLEEP_DURATION_MIN = 7  # hours
    OPTIMAL_SLEEP_DURATION_MAX = 9  # hours
    
    def analyze_sleep(
        self, sleep_data: SleepData, lifestyle: LifestyleInput
    ) -> SleepAnalysis:
        """
        Analyze sleep quality and correlations with lifestyle habits.
        
        Args:
            sleep_data: Sleep information for the night
            lifestyle: Lifestyle input including habits and food
            
        Returns:
            SleepAnalysis with quality assessment, correlations, and recommendations
        """
        # Determine overall sleep quality
        overall_quality = self._assess_overall_quality(sleep_data)
        
        # Identify correlations between habits and sleep
        correlations = self._identify_correlations(sleep_data, lifestyle)
        
        # Generate actionable recommendations
        recommendations = self._generate_recommendations(
            sleep_data, lifestyle, correlations
        )
        
        # Create comprehensive explanation
        explanation = self._generate_explanation(
            overall_quality, sleep_data, correlations
        )
        
        return SleepAnalysis(
            overall_quality=overall_quality,
            correlations=correlations,
            recommendations=recommendations,
            explanation=explanation
        )
    
    def identify_sleep_disruptors(
        self, lifestyle: LifestyleInput
    ) -> List[SleepDisruptor]:
        """
        Identify specific habits affecting sleep quality.
        
        Args:
            lifestyle: Lifestyle input including habits and food
            
        Returns:
            List of SleepDisruptor objects ranked by severity
        """
        if not lifestyle.sleep_data:
            return []
        
        disruptors = []
        bedtime = lifestyle.sleep_data.bedtime
        
        # Check for caffeine consumption
        caffeine_disruptor = self._check_caffeine_timing(lifestyle, bedtime)
        if caffeine_disruptor:
            disruptors.append(caffeine_disruptor)
        
        # Check for late eating
        late_eating_disruptor = self._check_late_eating(lifestyle, bedtime)
        if late_eating_disruptor:
            disruptors.append(late_eating_disruptor)
        
        # Check for dehydration
        dehydration_disruptor = self._check_hydration(lifestyle)
        if dehydration_disruptor:
            disruptors.append(dehydration_disruptor)
        
        # Check for stress
        stress_disruptor = self._check_stress(lifestyle)
        if stress_disruptor:
            disruptors.append(stress_disruptor)
        
        # Check for screen time
        screen_disruptor = self._check_screen_time(lifestyle, bedtime)
        if screen_disruptor:
            disruptors.append(screen_disruptor)
        
        # Sort by severity (highest first)
        disruptors.sort(key=lambda d: d.severity, reverse=True)
        
        return disruptors
    
    def _assess_overall_quality(self, sleep_data: SleepData) -> SleepQuality:
        """Assess overall sleep quality based on multiple factors."""
        quality_score = sleep_data.quality
        duration = sleep_data.duration
        interruptions = sleep_data.interruptions
        
        # Start with quality rating
        if quality_score >= self.GOOD_SLEEP_QUALITY:
            base_quality = SleepQuality.EXCELLENT
        elif quality_score >= self.FAIR_SLEEP_QUALITY:
            base_quality = SleepQuality.GOOD
        elif quality_score >= self.POOR_SLEEP_QUALITY:
            base_quality = SleepQuality.FAIR
        else:
            base_quality = SleepQuality.POOR
        
        # Adjust for duration
        if duration < 6:
            # Insufficient sleep - downgrade
            if base_quality == SleepQuality.EXCELLENT:
                base_quality = SleepQuality.GOOD
            elif base_quality == SleepQuality.GOOD:
                base_quality = SleepQuality.FAIR
        elif duration > 10:
            # Excessive sleep - may indicate issues
            if base_quality == SleepQuality.EXCELLENT:
                base_quality = SleepQuality.GOOD
        
        # Adjust for interruptions
        if interruptions >= 3:
            # Frequent interruptions - downgrade
            if base_quality == SleepQuality.EXCELLENT:
                base_quality = SleepQuality.GOOD
            elif base_quality == SleepQuality.GOOD:
                base_quality = SleepQuality.FAIR
        
        return base_quality
    
    def _identify_correlations(
        self, sleep_data: SleepData, lifestyle: LifestyleInput
    ) -> List[SleepCorrelation]:
        """Identify correlations between habits and sleep quality."""
        correlations = []
        bedtime = sleep_data.bedtime
        
        # Analyze caffeine impact
        caffeine_correlation = self._analyze_caffeine_impact(lifestyle, bedtime, sleep_data)
        if caffeine_correlation:
            correlations.append(caffeine_correlation)
        
        # Analyze eating timing impact
        eating_correlation = self._analyze_eating_timing(lifestyle, bedtime, sleep_data)
        if eating_correlation:
            correlations.append(eating_correlation)
        
        # Analyze hydration impact
        hydration_correlation = self._analyze_hydration_impact(lifestyle, sleep_data)
        if hydration_correlation:
            correlations.append(hydration_correlation)
        
        # Analyze stress impact
        stress_correlation = self._analyze_stress_impact(lifestyle, sleep_data)
        if stress_correlation:
            correlations.append(stress_correlation)
        
        # Analyze screen time impact
        screen_correlation = self._analyze_screen_time_impact(lifestyle, bedtime, sleep_data)
        if screen_correlation:
            correlations.append(screen_correlation)
        
        return correlations
    
    def _analyze_caffeine_impact(
        self, lifestyle: LifestyleInput, bedtime: time, sleep_data: SleepData
    ) -> Optional[SleepCorrelation]:
        """Analyze caffeine's impact on sleep."""
        caffeine_habits = [h for h in lifestyle.daily_habits if h.type == HabitType.CAFFEINE]
        
        if not caffeine_habits:
            return None
        
        # Find caffeine closest to bedtime
        late_caffeine = []
        for habit in caffeine_habits:
            if habit.timing:
                hours_before_bed = self._calculate_hours_between(habit.timing, bedtime)
                if hours_before_bed <= self.CAFFEINE_CUTOFF_HOURS:
                    late_caffeine.append((habit, hours_before_bed))
        
        if late_caffeine:
            # Late caffeine - negative impact
            closest_habit, hours_gap = min(late_caffeine, key=lambda x: x[1])
            strength = min(10, int(10 - hours_gap))  # Closer = stronger impact
            
            return SleepCorrelation(
                habit=f"Caffeine consumption {hours_gap:.1f} hours before bed",
                impact=ImpactType.NEGATIVE,
                strength=strength,
                description=(
                    f"Caffeine consumed at {closest_habit.timing.strftime('%H:%M')} "
                    f"(intensity {closest_habit.intensity}/10) likely disrupted your sleep. "
                    "Caffeine has a half-life of 5-6 hours and can interfere with sleep onset."
                )
            )
        else:
            # Caffeine consumed early enough - neutral or positive
            return SleepCorrelation(
                habit="Caffeine consumption timing",
                impact=ImpactType.NEUTRAL,
                strength=2,
                description=(
                    "Caffeine was consumed more than 6 hours before bedtime, "
                    "minimizing its impact on sleep quality."
                )
            )
    
    def _analyze_eating_timing(
        self, lifestyle: LifestyleInput, bedtime: time, sleep_data: SleepData
    ) -> Optional[SleepCorrelation]:
        """Analyze eating timing's impact on sleep."""
        # Check if there are food items with timing information
        # For now, we'll use a simplified approach based on timestamp
        if not lifestyle.food_items:
            return None
        
        # Estimate last meal time from lifestyle timestamp
        # This is a simplification - in a real system, each food item would have a timestamp
        last_meal_time = lifestyle.timestamp.time()
        hours_before_bed = self._calculate_hours_between(last_meal_time, bedtime)
        
        if hours_before_bed < self.LATE_EATING_CUTOFF_HOURS:
            # Late eating - negative impact
            strength = min(10, int(8 - hours_before_bed * 2))
            
            return SleepCorrelation(
                habit=f"Eating {hours_before_bed:.1f} hours before bed",
                impact=ImpactType.NEGATIVE,
                strength=max(1, strength),
                description=(
                    f"Eating within {hours_before_bed:.1f} hours of bedtime can disrupt sleep. "
                    "Digestion requires energy and can interfere with the body's natural "
                    "wind-down process, potentially causing discomfort and restlessness."
                )
            )
        
        return None
    
    def _analyze_hydration_impact(
        self, lifestyle: LifestyleInput, sleep_data: SleepData
    ) -> Optional[SleepCorrelation]:
        """Analyze hydration's impact on sleep."""
        water_intake = lifestyle.water_intake
        
        if water_intake < self.LOW_WATER_THRESHOLD:
            # Dehydration - negative impact
            strength = 6
            return SleepCorrelation(
                habit=f"Low water intake ({water_intake:.0f}ml)",
                impact=ImpactType.NEGATIVE,
                strength=strength,
                description=(
                    "Dehydration can cause discomfort, dry mouth, and restlessness during sleep. "
                    "Adequate hydration supports better sleep quality and recovery."
                )
            )
        elif water_intake < self.OPTIMAL_WATER_MIN:
            # Slightly low hydration
            strength = 3
            return SleepCorrelation(
                habit=f"Suboptimal water intake ({water_intake:.0f}ml)",
                impact=ImpactType.NEUTRAL,
                strength=strength,
                description=(
                    "Water intake is slightly below optimal levels. "
                    "Increasing hydration may improve sleep quality."
                )
            )
        
        return None
    
    def _analyze_stress_impact(
        self, lifestyle: LifestyleInput, sleep_data: SleepData
    ) -> Optional[SleepCorrelation]:
        """Analyze stress's impact on sleep."""
        stress_habits = [h for h in lifestyle.daily_habits if h.type == HabitType.STRESS]
        
        if not stress_habits:
            return None
        
        max_stress = max(h.intensity for h in stress_habits)
        
        if max_stress >= self.HIGH_STRESS_THRESHOLD:
            # High stress - strong negative impact
            strength = 9
            return SleepCorrelation(
                habit=f"High stress levels (intensity {max_stress}/10)",
                impact=ImpactType.NEGATIVE,
                strength=strength,
                description=(
                    "High stress levels significantly impact sleep quality by increasing "
                    "cortisol, causing racing thoughts, and preventing the body from "
                    "entering deep, restorative sleep stages."
                )
            )
        elif max_stress >= self.MODERATE_STRESS_THRESHOLD:
            # Moderate stress
            strength = 6
            return SleepCorrelation(
                habit=f"Moderate stress levels (intensity {max_stress}/10)",
                impact=ImpactType.NEGATIVE,
                strength=strength,
                description=(
                    "Moderate stress can interfere with sleep onset and reduce sleep quality. "
                    "Managing stress through relaxation techniques may improve rest."
                )
            )
        
        return None
    
    def _analyze_screen_time_impact(
        self, lifestyle: LifestyleInput, bedtime: time, sleep_data: SleepData
    ) -> Optional[SleepCorrelation]:
        """Analyze screen time's impact on sleep."""
        screen_habits = [h for h in lifestyle.daily_habits if h.type == HabitType.SCREEN_TIME]
        
        if not screen_habits:
            return None
        
        # Find screen time close to bedtime
        late_screen_time = []
        for habit in screen_habits:
            if habit.timing:
                hours_before_bed = self._calculate_hours_between(habit.timing, bedtime)
                if hours_before_bed <= 2:  # Within 2 hours of bedtime
                    late_screen_time.append((habit, hours_before_bed))
        
        if late_screen_time:
            closest_habit, hours_gap = min(late_screen_time, key=lambda x: x[1])
            strength = min(10, int(8 - hours_gap * 2))
            
            return SleepCorrelation(
                habit=f"Screen time {hours_gap:.1f} hours before bed",
                impact=ImpactType.NEGATIVE,
                strength=max(1, strength),
                description=(
                    f"Screen time at {closest_habit.timing.strftime('%H:%M')} "
                    "exposed you to blue light, which suppresses melatonin production "
                    "and can delay sleep onset and reduce sleep quality."
                )
            )
        
        return None
    
    def _generate_recommendations(
        self,
        sleep_data: SleepData,
        lifestyle: LifestyleInput,
        correlations: List[SleepCorrelation]
    ) -> List[Recommendation]:
        """Generate actionable recommendations for sleep improvement."""
        recommendations = []
        
        # Identify disruptors to base recommendations on
        disruptors = self.identify_sleep_disruptors(lifestyle)
        
        # Generate recommendations based on disruptors
        for disruptor in disruptors:
            if disruptor.type == SleepDisruptorType.CAFFEINE:
                recommendations.append(Recommendation(
                    priority=RecommendationPriority.HIGH,
                    action="Avoid caffeine after 2 PM",
                    rationale=(
                        "Caffeine has a half-life of 5-6 hours and can remain in your system "
                        "for up to 10 hours, interfering with sleep onset and quality."
                    ),
                    expected_impact="Faster sleep onset and deeper, more restful sleep"
                ))
            
            elif disruptor.type == SleepDisruptorType.LATE_EATING:
                recommendations.append(Recommendation(
                    priority=RecommendationPriority.HIGH,
                    action="Finish eating at least 3 hours before bedtime",
                    rationale=(
                        "Late eating keeps your digestive system active when your body "
                        "should be winding down, potentially causing discomfort and disrupting sleep."
                    ),
                    expected_impact="Reduced nighttime discomfort and improved sleep quality"
                ))
            
            elif disruptor.type == SleepDisruptorType.DEHYDRATION:
                recommendations.append(Recommendation(
                    priority=RecommendationPriority.MEDIUM,
                    action="Increase daily water intake to 2000-3000ml",
                    rationale=(
                        "Dehydration can cause discomfort and restlessness during sleep. "
                        "However, avoid drinking large amounts right before bed."
                    ),
                    expected_impact="Better sleep comfort and reduced nighttime awakenings"
                ))
            
            elif disruptor.type == SleepDisruptorType.STRESS:
                recommendations.append(Recommendation(
                    priority=RecommendationPriority.HIGH,
                    action="Practice relaxation techniques before bed (meditation, deep breathing, gentle stretching)",
                    rationale=(
                        "Stress activates the sympathetic nervous system, making it difficult "
                        "to fall asleep. Relaxation techniques help activate the parasympathetic "
                        "nervous system, promoting rest."
                    ),
                    expected_impact="Easier sleep onset and more restorative sleep"
                ))
            
            elif disruptor.type == SleepDisruptorType.SCREEN_TIME:
                recommendations.append(Recommendation(
                    priority=RecommendationPriority.MEDIUM,
                    action="Avoid screens 1-2 hours before bedtime",
                    rationale=(
                        "Blue light from screens suppresses melatonin production, the hormone "
                        "that regulates sleep-wake cycles."
                    ),
                    expected_impact="Improved melatonin production and easier sleep onset"
                ))
        
        # Add general recommendations if sleep quality is poor
        if sleep_data.quality <= self.POOR_SLEEP_QUALITY:
            # Check if we don't already have a sleep schedule recommendation
            if not any("consistent" in r.action.lower() for r in recommendations):
                recommendations.append(Recommendation(
                    priority=RecommendationPriority.MEDIUM,
                    action="Establish a consistent sleep schedule",
                    rationale=(
                        "Going to bed and waking up at the same time daily helps regulate "
                        "your circadian rhythm, improving sleep quality over time."
                    ),
                    expected_impact="More consistent sleep patterns and better overall sleep quality"
                ))
        
        # Sort by priority
        priority_order = {
            RecommendationPriority.HIGH: 0,
            RecommendationPriority.MEDIUM: 1,
            RecommendationPriority.LOW: 2
        }
        recommendations.sort(key=lambda r: priority_order[r.priority])
        
        return recommendations
    
    def _generate_explanation(
        self,
        overall_quality: SleepQuality,
        sleep_data: SleepData,
        correlations: List[SleepCorrelation]
    ) -> str:
        """Generate comprehensive explanation of sleep analysis."""
        quality_descriptions = {
            SleepQuality.POOR: "poor quality",
            SleepQuality.FAIR: "fair quality",
            SleepQuality.GOOD: "good quality",
            SleepQuality.EXCELLENT: "excellent quality"
        }
        
        explanation_parts = [
            f"Your sleep was of {quality_descriptions[overall_quality]} "
            f"with {sleep_data.duration:.1f} hours of rest and a quality rating of "
            f"{sleep_data.quality}/10."
        ]
        
        # Add information about interruptions
        if sleep_data.interruptions > 0:
            explanation_parts.append(
                f"You experienced {sleep_data.interruptions} interruption(s) during the night."
            )
        
        # Summarize negative correlations
        negative_correlations = [c for c in correlations if c.impact == ImpactType.NEGATIVE]
        if negative_correlations:
            # Find strongest negative correlation
            strongest = max(negative_correlations, key=lambda c: c.strength)
            explanation_parts.append(
                f"The primary factor affecting your sleep was: {strongest.habit}. "
                f"{strongest.description}"
            )
            
            # Mention other significant factors
            other_significant = [
                c for c in negative_correlations 
                if c != strongest and c.strength >= 6
            ]
            if other_significant:
                factor_names = ", ".join(c.habit for c in other_significant)
                explanation_parts.append(
                    f"Additional factors that may have impacted your sleep include: {factor_names}."
                )
        else:
            explanation_parts.append(
                "No significant lifestyle factors were identified as negatively impacting your sleep."
            )
        
        return " ".join(explanation_parts)
    
    def _check_caffeine_timing(
        self, lifestyle: LifestyleInput, bedtime: time
    ) -> Optional[SleepDisruptor]:
        """Check for caffeine consumption too close to bedtime."""
        caffeine_habits = [h for h in lifestyle.daily_habits if h.type == HabitType.CAFFEINE]
        
        if not caffeine_habits:
            return None
        
        late_caffeine = []
        for habit in caffeine_habits:
            if habit.timing:
                hours_before_bed = self._calculate_hours_between(habit.timing, bedtime)
                if hours_before_bed <= self.CAFFEINE_CUTOFF_HOURS:
                    late_caffeine.append((habit, hours_before_bed))
        
        if late_caffeine:
            closest_habit, hours_gap = min(late_caffeine, key=lambda x: x[1])
            severity = min(10, int(10 - hours_gap))
            
            return SleepDisruptor(
                type=SleepDisruptorType.CAFFEINE,
                severity=severity,
                timing=f"{closest_habit.timing.strftime('%H:%M')} ({hours_gap:.1f}h before bed)",
                recommendation=(
                    "Avoid caffeine consumption after 2 PM. Consider switching to "
                    "decaffeinated beverages or herbal tea in the afternoon and evening."
                )
            )
        
        return None
    
    def _check_late_eating(
        self, lifestyle: LifestyleInput, bedtime: time
    ) -> Optional[SleepDisruptor]:
        """Check for eating too close to bedtime."""
        if not lifestyle.food_items:
            return None
        
        # Estimate last meal time from lifestyle timestamp
        last_meal_time = lifestyle.timestamp.time()
        hours_before_bed = self._calculate_hours_between(last_meal_time, bedtime)
        
        if hours_before_bed < self.LATE_EATING_CUTOFF_HOURS:
            severity = min(10, int(8 - hours_before_bed * 2))
            
            return SleepDisruptor(
                type=SleepDisruptorType.LATE_EATING,
                severity=max(1, severity),
                timing=f"{last_meal_time.strftime('%H:%M')} ({hours_before_bed:.1f}h before bed)",
                recommendation=(
                    "Try to finish your last meal at least 3 hours before bedtime. "
                    "If you need a snack, choose something light and easy to digest."
                )
            )
        
        return None
    
    def _check_hydration(self, lifestyle: LifestyleInput) -> Optional[SleepDisruptor]:
        """Check for dehydration affecting sleep."""
        water_intake = lifestyle.water_intake
        
        if water_intake < self.LOW_WATER_THRESHOLD:
            severity = 6
            return SleepDisruptor(
                type=SleepDisruptorType.DEHYDRATION,
                severity=severity,
                timing=f"Daily intake: {water_intake:.0f}ml",
                recommendation=(
                    "Increase water intake throughout the day to 2000-3000ml. "
                    "Drink most of your water earlier in the day to avoid nighttime bathroom trips."
                )
            )
        
        return None
    
    def _check_stress(self, lifestyle: LifestyleInput) -> Optional[SleepDisruptor]:
        """Check for stress affecting sleep."""
        stress_habits = [h for h in lifestyle.daily_habits if h.type == HabitType.STRESS]
        
        if not stress_habits:
            return None
        
        max_stress = max(h.intensity for h in stress_habits)
        
        if max_stress >= self.HIGH_STRESS_THRESHOLD:
            severity = 9
            return SleepDisruptor(
                type=SleepDisruptorType.STRESS,
                severity=severity,
                timing=f"Stress intensity: {max_stress}/10",
                recommendation=(
                    "Practice stress management techniques: meditation, deep breathing exercises, "
                    "journaling, or talking to a counselor. Consider a relaxing bedtime routine."
                )
            )
        elif max_stress >= self.MODERATE_STRESS_THRESHOLD:
            severity = 6
            return SleepDisruptor(
                type=SleepDisruptorType.STRESS,
                severity=severity,
                timing=f"Stress intensity: {max_stress}/10",
                recommendation=(
                    "Incorporate stress-reduction activities into your routine: light exercise, "
                    "mindfulness, or relaxing hobbies before bed."
                )
            )
        
        return None
    
    def _check_screen_time(
        self, lifestyle: LifestyleInput, bedtime: time
    ) -> Optional[SleepDisruptor]:
        """Check for screen time too close to bedtime."""
        screen_habits = [h for h in lifestyle.daily_habits if h.type == HabitType.SCREEN_TIME]
        
        if not screen_habits:
            return None
        
        late_screen_time = []
        for habit in screen_habits:
            if habit.timing:
                hours_before_bed = self._calculate_hours_between(habit.timing, bedtime)
                if hours_before_bed <= 2:
                    late_screen_time.append((habit, hours_before_bed))
        
        if late_screen_time:
            closest_habit, hours_gap = min(late_screen_time, key=lambda x: x[1])
            severity = min(10, int(7 - hours_gap * 2))
            
            return SleepDisruptor(
                type=SleepDisruptorType.SCREEN_TIME,
                severity=max(1, severity),
                timing=f"{closest_habit.timing.strftime('%H:%M')} ({hours_gap:.1f}h before bed)",
                recommendation=(
                    "Avoid screens 1-2 hours before bedtime. If you must use devices, "
                    "enable blue light filters or use blue light blocking glasses."
                )
            )
        
        return None
    
    def _calculate_hours_between(self, earlier_time: time, later_time: time) -> float:
        """Calculate hours between two times, handling day boundary."""
        # Convert times to datetime for calculation
        today = datetime.now().date()
        earlier_dt = datetime.combine(today, earlier_time)
        later_dt = datetime.combine(today, later_time)
        
        # If later time is before earlier time, it's the next day
        if later_dt < earlier_dt:
            later_dt += timedelta(days=1)
        
        # Calculate difference in hours
        diff = later_dt - earlier_dt
        return diff.total_seconds() / 3600
