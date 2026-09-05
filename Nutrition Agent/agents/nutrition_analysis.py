from typing import Dict, Any, List
from datetime import datetime
from utils.llm_handler import LLMHandler
from utils.qdrant_client import QdrantNutritionDB

class NutritionAnalysisAgent:
    def __init__(self):
        self.llm = LLMHandler()
        self.db = QdrantNutritionDB()
    
    def calculate_bmr(self, age: int, gender: str, weight_kg: float, height_cm: float) -> float:
        if gender.lower() == "male":
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        return bmr
    
    def calculate_tdee(self, bmr: float, activity_level: str) -> float:
        multipliers = {
            "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
            "active": 1.725, "very_active": 1.9
        }
        return bmr * multipliers.get(activity_level.lower(), 1.2)
    
    def analyze_needs(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        age = user_data.get("age", 30)
        gender = user_data.get("gender", "male").lower()
        weight = user_data.get("weight_kg", 70.0)
        height = user_data.get("height_cm", 170.0)
        activity = user_data.get("activity_level", "moderate").lower()
        goals = user_data.get("goals", [])
        
        bmr = self.calculate_bmr(age, gender, weight, height)
        tdee = self.calculate_tdee(bmr, activity)
        
        # Logika penyesuaian kalori
        adj = 0
        g_str = str(goals).lower()
        if "loss" in g_str: adj = -500
        elif "gain" in g_str or "muscle" in g_str: adj = 500
        
        target = max(tdee + adj, 1200)
        
        # Buat profil nutrisi
        profile = {
            "user_id": user_data.get("user_id"),
            "name": user_data.get("name", "User"),
            "bmr": round(bmr, 1),
            "tdee": round(tdee, 1),
            "target_calories": round(target, 1),
            "protein_g": round((target * 0.3) / 4, 1),
            "carbs_g": round((target * 0.45) / 4, 1),
            "fat_g": round((target * 0.25) / 9, 1),
            "age": age,
            "gender": gender,
            "weight_kg": weight,
            "height_cm": height,
            "activity_level": activity,
            "goals": goals,
            "calculated_at": datetime.now().isoformat()
        }
        
        # **SIMPAN KE QDRANT** (Memory jangka panjang)
        try:
            profile_summary = f"""
            User: {user_data.get('name', 'User')}
            Age {age}, {gender}, {weight}kg, {height}cm.
            Activity: {activity}. Goals: {goals}.
            Daily target: {target}kcal, protein: {profile['protein_g']:.1f}g.
            """
            
            embedding = self.llm.generate_embedding(profile_summary)
            self.db.store_nutrition_data(user_data.get("user_id"), profile, embedding)
            print(f"✅ Profile saved to Qdrant for user {user_data.get('user_id')}")
        except Exception as e:
            print(f"⚠️ Failed to save to Qdrant: {e}")
        
        return profile

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Ambil profil user dari Qdrant"""
        try:
            data = self.db.get_user_data(user_id)
            if data and hasattr(data, 'payload'):
                return data.payload.get("nutrition_data", {})
        except Exception as e:
            print(f"Error retrieving profile: {e}")
        return {}
    
    def search_similar_profiles(self, embedding: List[float], limit: int = 3):
        """Cari profil serupa dari Qdrant"""
        return self.db.search_similar_profiles(embedding, limit)
    
    def get_contextual_recommendations(self, user_id: str, question: str) -> str:
        """Beri rekomendasi berdasarkan profil user dan pertanyaan"""
        # Ambil profil user
        profile = self.get_user_profile(user_id)
        
        if not profile:
            return "Saya belum memiliki data profil Anda. Silakan lakukan analisis nutrisi terlebih dahulu."
        
        # Buat embedding dari pertanyaan
        question_embedding = self.llm.generate_embedding(question)
        
        # Cari profil serupa
        similar_profiles = self.search_similar_profiles(question_embedding, limit=2)
        
        # Buat konteks dari profil serupa
        similar_context = ""
        if similar_profiles:
            similar_context = "\n\nBerdasarkan pengguna dengan profil serupa:\n"
            for i, sim in enumerate(similar_profiles[:2], 1):
                sim_data = sim.payload.get("nutrition_data", {})
                similar_context += f"{i}. Usia {sim_data.get('age', '?')}, target {sim_data.get('target_calories', 0)}kcal\n"
        
        # Generate respons dengan konteks
        prompt = f"""
        PROFIL PENGGUNA SAAT INI:
        - Nama: {profile.get('name', 'User')}
        - Usia: {profile.get('age')}
        - Gender: {profile.get('gender')}
        - Berat: {profile.get('weight_kg')}kg
        - Tinggi: {profile.get('height_cm')}cm
        - Aktivitas: {profile.get('activity_level')}
        - Target Kalori: {profile.get('target_calories')}kcal/hari
        - Target Protein: {profile.get('protein_g', 0):.1f}g/hari
        - Tujuan: {', '.join(profile.get('goals', []))}
        
        {similar_context}
        
        PERTANYAAN USER: {question}
        
        Berikan jawaban yang PERSONAL berdasarkan profil di atas.
        Jika relevan, sertakan angka-angka spesifik dari profil.
        """
        
        return self.llm.generate_response(
            system_prompt="Anda adalah ahli gizi personal yang memahami profil pengguna.",
            user_prompt=prompt
        )
    
    def get_recommendations(self, user_data: Dict[str, Any]) -> str:
        """Rekomendasi personal berdasarkan profil user"""
        try:
            profile = self.analyze_needs(user_data)
            
            # Buat prompt personal
            prompt = f"""
            User Profile:
            - Name: {user_data.get('name', 'User')}
            - Age: {profile.get('age')}
            - Gender: {profile.get('gender')}
            - Weight: {profile.get('weight_kg')}kg
            - Height: {profile.get('height_cm')}cm
            - Activity: {profile.get('activity_level')}
            - Goals: {profile.get('goals')}
            - Daily Target: {profile.get('target_calories')}kcal, Protein: {profile.get('protein_g')}g
            
            Berikan rekomendasi nutrisi personal untuk user ini.
            Sertakan:
            1. Rangkuman target harian
            2. Tips untuk mencapai goals
            3. Contoh makanan yang sesuai
            4. Saran pola makan
            """
            
            return self.llm.generate_response(
                system_prompt="Anda adalah ahli gizi personal. Berikan rekomendasi yang personal dan ramah.",
                user_prompt=prompt
            )
        except Exception as e:
            return f"Error analisis: {str(e)}"