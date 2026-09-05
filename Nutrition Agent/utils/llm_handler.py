import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class LLMHandler:
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = model
        self.client = None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)
                print(f"✓ Terkoneksi ke Gemini: {self.model_name}")
            except Exception as e:
                print(f"⚠️ Error inisialisasi Gemini: {e}")
        else:
            print("⚠️ GEMINI_API_KEY tidak ditemukan di .env")

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        if not self.client:
            return "⚠️ Error: API Key tidak valid."
        
        try:
            # TEKNIK BARU: "Strict Instruction"
            # Kita paksa AI hemat bicara lewat instruksi, bukan lewat pemotongan paksa.
            strict_instruction = (
                "Jawab dengan SINGKAT, PADAT, dan JELAS. "
                "Gunakan format poin-poin atau tabel jika memungkinkan. "
                "HINDARI intro atau penutup yang bertele-tele. "
                "Langsung ke inti jawaban."
            )
            
            full_prompt = f"{system_prompt}\n{strict_instruction}\n\nPermintaan User: {user_prompt}"
            
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.7,
                    # Kita naikkan ke 2000 agar kalimat penutup tidak kepotong
                    # Tapi karena ada instruksi "SINGKAT" di atas, AI jarang akan pakai sampai habis.
                    "max_output_tokens": 2000, 
                }
            )
            return response.text
        except Exception as e:
            return f"Maaf, terjadi error pada AI: {str(e)}"

    def generate_embedding(self, text: str):
        if not self.api_key: return [0.0] * 768
        try:
            # Tetap potong input agar hemat kuota embedding
            safe_text = text[:1000]
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=safe_text
            )
            return result['embedding']
        except:
            return [0.0] * 768