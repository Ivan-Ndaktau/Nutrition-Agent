from typing import List, Dict, Any  # Tambahkan ini di bagian atas
from utils.llm_handler import LLMHandler

class ActivitySyncAgent:
    def __init__(self):
        self.llm = LLMHandler()
        
        # Activity multipliers for different exercises
        self.activity_calories = {
            "running": 10,  # calories per minute
            "cycling": 8,
            "swimming": 9,
            "weight_training": 5,
            "yoga": 3,
            "walking": 4,
            "hiit": 12
        }
    
    def adjust_nutrition_for_activity(self,
                                     nutrition_profile: Dict[str, Any],
                                     activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Adjust nutrition based on physical activities"""
        
        total_activity_calories = 0
        
        for activity in activities:
            activity_type = activity.get("type", "walking")
            duration_min = activity.get("duration_min", 30)
            intensity = activity.get("intensity", "moderate")
            
            # Calculate calories burned
            base_rate = self.activity_calories.get(activity_type, 5)
            
            # Adjust for intensity
            intensity_multiplier = {
                "light": 0.8,
                "moderate": 1.0,
                "vigorous": 1.3
            }.get(intensity, 1.0)
            
            calories_burned = base_rate * duration_min * intensity_multiplier
            total_activity_calories += calories_burned
        
        # Adjust nutrition targets
        adjusted_profile = nutrition_profile.copy()
        adjusted_calories = nutrition_profile.get("target_calories", 2000) + total_activity_calories
        
        # Increase protein for muscle recovery if intense exercise
        intense_activities = any(a.get("intensity") == "vigorous" for a in activities)
        if intense_activities:
            protein_multiplier = 1.2
        else:
            protein_multiplier = 1.0
        
        adjusted_profile["target_calories"] = adjusted_calories
        adjusted_profile["protein_g"] = adjusted_profile.get("protein_g", 100) * protein_multiplier
        adjusted_profile["total_activity_calories"] = total_activity_calories
        adjusted_profile["activities_today"] = activities
        
        return adjusted_profile
    
    def get_activity_recommendations(self,
                                    nutrition_profile: Dict[str, Any],
                                    fitness_level: str = "intermediate") -> str:
        """Get personalized activity recommendations"""
        
        prompt = f"""
        Based on this user profile:
        {nutrition_profile}
        
        Fitness Level: {fitness_level}
        
        Create a weekly activity plan that complements their nutrition goals:
        {nutrition_profile.get('goals', [])}
        
        Include:
        1. Recommended types of exercise
        2. Duration and frequency
        3. Intensity levels
        4. Best times to exercise relative to meals
        5. Recovery recommendations
        6. Hydration guidelines
        7. Signs of overtraining to watch for
        """
        
        return self.llm.generate_response(
            system_prompt="You are a certified personal trainer and sports nutritionist.",
            user_prompt=prompt
        )
    
    def calculate_post_workout_nutrition(self,
                                        activity_type: str,
                                        duration_min: int) -> str:
        """Calculate optimal post-workout nutrition"""
        
        prompt = f"""
        For {activity_type} lasting {duration_min} minutes, recommend:
        
        1. Ideal post-workout meal/snack timing
        2. Macronutrient ratios (protein:carbs)
        3. Specific food suggestions
        4. Hydration requirements
        5. Supplement recommendations if applicable
        """
        
        return self.llm.generate_response(
            system_prompt="You are an expert in exercise physiology and post-workout nutrition.",
            user_prompt=prompt
        )