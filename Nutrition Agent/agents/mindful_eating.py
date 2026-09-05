from typing import List, Dict, Any  # Tambahkan ini
from utils.llm_handler import LLMHandler

class MindfulEatingAgent:
    def __init__(self):
        self.llm = LLMHandler()
    
    def provide_mindful_eating_guidance(self,
                                       user_state: Dict[str, Any]) -> str:
        """Provide mindful eating guidance based on user's current state"""
        
        prompt = f"""
        User is currently feeling: {user_state.get('mood', 'neutral')}
        Hunger level: {user_state.get('hunger_level', 5)}/10
        Stress level: {user_state.get('stress_level', 5)}/10
        Time since last meal: {user_state.get('hours_since_meal', 3)} hours
        
        Provide mindful eating guidance including:
        1. Breathing exercise before eating
        2. Eating pace recommendations
        3. Portion awareness tips
        4. Hunger/fullness scale guidance
        5. Emotional eating alternatives if stressed
        """
        
        return self.llm.generate_response(
            system_prompt="You are a mindfulness coach specializing in eating behaviors.",
            user_prompt=prompt
        )
    
    def generate_motivation(self,
                           user_progress: Dict[str, Any],
                           challenges: List[str] = None) -> str:
        """Generate personalized motivational messages"""
        
        prompt = f"""
        User has been working on: {user_progress.get('goals', [])}
        Progress made: {user_progress.get('progress', 'starting out')}
        Current challenges: {challenges or ['staying consistent']}
        
        Create motivational content including:
        1. Encouragement based on their journey
        2. Reminder of their "why"
        3. Small win celebrations
        4. Strategy for overcoming current challenges
        5. Inspirational quote related to their goals
        """
        
        return self.llm.generate_response(
            system_prompt="You are an inspirational coach who helps people stay motivated on their health journey.",
            user_prompt=prompt
        )
    
    def eating_habit_analysis(self,
                             eating_logs: List[Dict[str, Any]]) -> str:
        """Analyze eating habits and provide insights"""
        
        prompt = f"""
        Analyze these eating patterns:
        {eating_logs}
        
        Provide insights on:
        1. Eating timing patterns
        2. Emotional eating triggers if present
        3. Macronutrient balance
        4. Hydration habits
        5. Suggestions for improvement
        6. Positive habits to reinforce
        """
        
        return self.llm.generate_response(
            system_prompt="You are a behavioral nutritionist analyzing eating patterns.",
            user_prompt=prompt
        )
    
    def stress_eating_intervention(self,
                                  trigger: str,
                                  intensity: int) -> str:
        """Provide alternatives to stress eating"""
        
        prompt = f"""
        User is experiencing stress eating triggered by: {trigger}
        Intensity level: {intensity}/10
        
        Provide:
        1. Immediate distraction techniques
        2. Alternative coping mechanisms
        3. Healthy snack options if they must eat
        4. Long-term strategies
        5. Self-compassion messages
        """
        
        return self.llm.generate_response(
            system_prompt="You are a therapist specializing in stress management and eating behaviors.",
            user_prompt=prompt
        )