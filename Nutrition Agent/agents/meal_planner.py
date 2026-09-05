from typing import List, Dict, Any
from utils.llm_handler import LLMHandler
from utils.qdrant_client import QdrantNutritionDB

class MealPlannerAgent:
    def __init__(self):
        self.llm = LLMHandler()
        self.db = QdrantNutritionDB()
    
    def generate_meal_plan(self, nutrition_profile: Dict[str, Any], days: int = 7, cuisine_preferences: List[str] = None) -> Dict[str, Any]:
        # --- PERBAIKAN UTAMA DI SINI ---
        # Kita ubah prompt agar meminta TABEL MARKDOWN.
        # Kita HAPUS permintaan resep/bahan agar muat dan tidak kepotong.
        
        pref_str = ", ".join(cuisine_preferences) if cuisine_preferences else "Bebas"
        
        prompt = f"""
        Buatkan Tabel Rencana Makan {days} Hari yang RAPI & RINGKAS.
        
        Data User:
        - Kalori Harian: {nutrition_profile.get('target_calories')} kcal
        - Tujuan: {nutrition_profile.get('goals', [])}
        - Preferensi: {pref_str}
        
        INSTRUKSI FORMAT (WAJIB):
        1. Sajikan dalam FORMAT TABEL MARKDOWN.
        2. Kolom: | Hari | Sarapan | Makan Siang | Makan Malam | Snack |
        3. Isi sel HANYA dengan Nama Menu & Kalori (contoh: "Nasi Goreng (400kcal)").
        4. JANGAN tulis bahan, resep, atau cara masak.
        5. JANGAN ada intro atau penutup. Langsung tabel.
        """
        
        meal_plan_text = self.llm.generate_response(
            system_prompt="Anda adalah perencana menu profesional. Sajikan data dalam tabel.",
            user_prompt=prompt
        )
        
        return {"meal_plan": meal_plan_text}

    def generate_quick_meal(self, calories: int, restrictions: List[str] = None) -> str:
        prompt = f"Saran 1 menu cepat {calories} kalori. Nama menu & bahan utama saja."
        return self.llm.generate_response("Chef praktis.", prompt)