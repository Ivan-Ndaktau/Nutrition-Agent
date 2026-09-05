import streamlit as st
import uuid
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AI Nutrition Crew", page_icon="🥗", layout="wide")

# --- SESSION STATE ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'user_data' not in st.session_state: 
    st.session_state.user_data = {}
if 'nutrition_profile' not in st.session_state: 
    st.session_state.nutrition_profile = None
if 'chat_history' not in st.session_state: 
    st.session_state.chat_history = []
if 'page' not in st.session_state: 
    st.session_state.page = "🏠 Dashboard"
if 'user_identified' not in st.session_state:
    st.session_state.user_identified = False

# --- IMPORT AGENTS ---
try:
    from agents.nutrition_analysis import NutritionAnalysisAgent
    from agents.meal_planner import MealPlannerAgent
    from agents.activity_sync import ActivitySyncAgent
    from agents.mindful_eating import MindfulEatingAgent
except ImportError as e:
    st.error(f"⚠️ Error Import Agent: {e}. Pastikan struktur folder benar.")
    st.stop()

# --- INISIALISASI AGENT ---
@st.cache_resource
def init_agents():
    return {
        'nutrition_analyst': NutritionAnalysisAgent(),
        'meal_planner': MealPlannerAgent(),
        'activity_sync': ActivitySyncAgent(),
        'mindful_eating': MindfulEatingAgent()
    }

agents = init_agents()

# --- FUNGSI UTILITAS ---
def get_user_context():
    """Ambil konteks user untuk AI"""
    context = ""
    if st.session_state.nutrition_profile:
        profile = st.session_state.nutrition_profile
        context = f"""
        INI PROFIL USER YANG SEDANG BERBICARA:
        - Nama/Nickname: {st.session_state.user_data.get('name', 'User')}
        - Usia: {profile.get('age')} tahun
        - Gender: {profile.get('gender')}
        - Berat: {profile.get('weight_kg')} kg
        - Tinggi: {profile.get('height_cm')} cm
        - Aktivitas: {profile.get('activity_level')}
        - Target Kalori: {profile.get('target_calories')} kcal/hari
        - Target Protein: {profile.get('protein_g', 0):.1f} g/hari
        - Tujuan: {', '.join(profile.get('goals', []))}
        - BMR: {profile.get('bmr', 0):.0f} kcal
        - TDEE: {profile.get('tdee', 0):.0f} kcal
        """
    return context

def ai_chat_response(prompt: str) -> str:
    """Response AI dengan memory profil user"""
    # 1. Ambil konteks user
    user_context = get_user_context()
    
    # 2. Ambil riwayat chat terbaru (3 pesan terakhir)
    recent_history = ""
    if st.session_state.chat_history:
        recent_history = "RIWAYAT CHAT TERAKHIR:\n"
        for msg in st.session_state.chat_history[-3:]:
            recent_history += f"{msg['role'].upper()}: {msg['content']}\n"
    
    # 3. Buat prompt lengkap untuk AI
    full_prompt = f"""
    {user_context}
    
    {recent_history}
    
    PERTANYAAN USER BARU: {prompt}
    
    PERINTAH UNTUK AI:
    1. Jika user bertanya tentang dirinya sendiri (seperti "siapa saya", "berapa target kalori saya"), JAWAB berdasarkan profil di atas
    2. Jika user belum punya profil, SARANKAN untuk buat profil dulu di Nutrition Analysis
    3. Gunakan nama/nickname user jika tersedia
    4. Jawab dengan ramah dan personal seolah-olah mengenal user
    5. Sertakan data spesifik dari profil jika relevan
    """
    
    # 4. Generate response dari AI
    return agents['nutrition_analyst'].llm.generate_response(
        system_prompt="""Anda adalah AI Nutritionist yang RAMAH dan PERSONAL.
        Anda MENGENAL dan MENGINGAT profil setiap user.
        Jawablah seolah-olah Anda adalah teman/nutritionist pribadi mereka.""",
        user_prompt=full_prompt
    )

def load_user_profile_from_memory():
    """Coba load profil user dari Qdrant berdasarkan user_id"""
    if not st.session_state.nutrition_profile and st.session_state.user_id:
        try:
            # Coba ambil dari Qdrant
            user_data = agents['nutrition_analyst'].db.get_user_data(st.session_state.user_id)
            if user_data and hasattr(user_data, 'payload'):
                profile = user_data.payload.get("nutrition_data", {})
                if profile:
                    st.session_state.nutrition_profile = profile
                    st.session_state.user_data = {
                        "user_id": st.session_state.user_id,
                        "name": profile.get("name", "User"),
                        "age": profile.get("age"),
                        "weight_kg": profile.get("weight_kg"),
                        "height_cm": profile.get("height_cm"),
                        "gender": profile.get("gender"),
                        "activity_level": profile.get("activity_level"),
                        "goals": profile.get("goals", []),
                    }
                    st.session_state.user_identified = True
                    print(f"✅ Loaded profile from memory for user {st.session_state.user_id}")
        except Exception as e:
            print(f"⚠️ Could not load from memory: {e}")

# Panggil fungsi load profile
load_user_profile_from_memory()

# --- SIDEBAR & NAVIGASI ---
st.sidebar.title("🥗 AI Nutrition Crew")
st.sidebar.caption("Powered by Gemini 2.5 Flash")

# Tampilkan status user di sidebar
if st.session_state.nutrition_profile:
    profile = st.session_state.nutrition_profile
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 Profil Anda")
    st.sidebar.write(f"**Nama:** {profile.get('name', 'User')}")
    st.sidebar.write(f"**Usia:** {profile.get('age', '-')}")
    st.sidebar.write(f"**Target:** {profile.get('target_calories', 0):.0f} kcal")
    if profile.get('goals'):
        st.sidebar.write(f"**Tujuan:** {', '.join(profile.get('goals', ['-']))}")

selected_page = st.sidebar.radio("Menu", [
    "🏠 Dashboard", "📊 Nutrition Analysis", "🍽️ Meal Planner", 
    "🏃 Activity Sync", "🧠 Mindful Eating", "💬 Chat with AI"
])

if selected_page != st.session_state.page:
    st.session_state.page = selected_page
    st.rerun()

page = st.session_state.page

# --- HALAMAN UTAMA ---
st.title("AI Nutrition Assistant")

# 1. DASHBOARD
if page == "🏠 Dashboard":
    # Header personal
    if st.session_state.user_data.get('name'):
        st.header(f"Selamat Datang, {st.session_state.user_data['name']}! 👋")
    else:
        st.header("Selamat Datang di AI Nutrition Crew! 👋")
    
    col1, col2, col3 = st.columns(3)
    
    if st.session_state.nutrition_profile:
        profile = st.session_state.nutrition_profile
        cal = profile.get('target_calories', 0)
        prot = profile.get('protein_g', 0)
        
        col1.metric("Target Kalori", f"{cal:.0f} kcal")
        col2.metric("Target Protein", f"{prot:.0f} g")
        col3.metric("Status", "✅ Profil Aktif")
        
        # Quick actions
        st.markdown("---")
        st.subheader("🚀 Aksi Cepat")
        
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        
        with quick_col1:
            if st.button("💬 Chat dengan AI", use_container_width=True, type="primary"):
                st.session_state.page = "💬 Chat with AI"
                st.rerun()
        
        with quick_col2:
            if st.button("🍽️ Rencana Makan", use_container_width=True):
                st.session_state.page = "🍽️ Meal Planner"
                st.rerun()
        
        with quick_col3:
            if st.button("📊 Edit Profil", use_container_width=True):
                st.session_state.page = "📊 Nutrition Analysis"
                st.rerun()
        
        # Ringkasan profil
        with st.expander("📋 Ringkasan Profil Saya", expanded=True):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Usia:** {profile.get('age')} tahun")
                st.write(f"**Gender:** {profile.get('gender')}")
                st.write(f"**Berat/Tinggi:** {profile.get('weight_kg')} kg / {profile.get('height_cm')} cm")
                # Hitung BMI
                height_m = profile.get('height_cm', 1) / 100
                bmi = profile.get('weight_kg', 0) / (height_m ** 2) if height_m > 0 else 0
                st.write(f"**BMI:** {bmi:.1f}")
            with col_b:
                st.write(f"**Aktivitas:** {profile.get('activity_level')}")
                st.write(f"**Tujuan:** {', '.join(profile.get('goals', []))}")
                st.write(f"**BMR:** {profile.get('bmr', 0):.0f} kcal")
                st.write(f"**TDEE:** {profile.get('tdee', 0):.0f} kcal")
        
        # Pesan personal dari AI
        st.markdown("---")
        st.subheader("💬 Pesan Personal dari AI Nutritionist")
        with st.container():
            if st.session_state.user_data.get('name'):
                message = f"""
                Halo **{st.session_state.user_data['name']}**! 👋
                
                Saya sudah mengenal profil nutrisi Anda. Berdasarkan data yang Anda berikan:
                - Target harian Anda adalah **{cal:.0f} kalori** dengan **{prot:.0f}g protein**
                - Aktivitas Anda termasuk **{profile.get('activity_level')}**
                - Tujuan Anda: **{', '.join(profile.get('goals', []))}**
                
                Siap membantu Anda mencapai tujuan kesehatan! 🥗
                """
            else:
                message = """
                Halo! 👋
                
                Saya sudah mengenal profil nutrisi Anda. 
                Silakan tanya apa saja tentang nutrisi, target kalori, atau rekomendasi makanan!
                """
            st.info(message)
    else:
        col1.metric("Target Kalori", "-")
        col2.metric("Target Protein", "-")
        col3.metric("Status", "⏳ Belum Ada Profil")
        
        st.info("""
        👋 **Halo! Selamat datang di AI Nutrition Crew!**
        
        Untuk pengalaman personal, silakan:
        1. **Buat profil** dulu di menu **📊 Nutrition Analysis**
        2. Atau langsung **chat** dengan saya di menu **💬 Chat with AI**
        
        Setelah punya profil, saya akan mengenal Anda dan bisa memberikan rekomendasi yang personal!
        """)

# 2. NUTRITION ANALYSIS
elif page == "📊 Nutrition Analysis":
    st.header("Analisis Kebutuhan Nutrisi")
    
    # Buat form untuk input data
    with st.form("analysis_form"):
        # Tambahkan input nama
        name = st.text_input("Nama/Nickname (opsional)", placeholder="Milds, Andi, dll.")
        
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("Usia", 18, 90, 25)
            weight = st.number_input("Berat (kg)", 30.0, 150.0, 60.0)
        with c2:
            height = st.number_input("Tinggi (cm)", 100.0, 220.0, 170.0)
            gender = st.selectbox("Gender", ["Male", "Female"])
        
        activity = st.selectbox("Level Aktivitas", 
                               ["Sedentary (jarang olahraga)", 
                                "Light (olahraga ringan 1-3x/minggu)",
                                "Moderate (olahraga 3-5x/minggu)",
                                "Active (olahraga berat 6-7x/minggu)"])
        
        # Simplify activity untuk kalkulasi
        activity_map = {
            "Sedentary (jarang olahraga)": "sedentary",
            "Light (olahraga ringan 1-3x/minggu)": "light",
            "Moderate (olahraga 3-5x/minggu)": "moderate",
            "Active (olahraga berat 6-7x/minggu)": "active"
        }
        
        goals = st.multiselect("Tujuan Anda", 
                              ["Weight Loss", "Maintain Weight", "Muscle Gain", "Improve Health"])
        
        submit = st.form_submit_button("🚀 Analisis Kebutuhan Saya")
    
    # Proses hasil form di luar form
    if submit:
        with st.spinner("Menganalisis profil Anda..."):
            # Data user
            user_data = {
                "user_id": st.session_state.user_id,
                "name": name if name else "User",
                "age": age,
                "weight_kg": weight,
                "height_cm": height,
                "gender": gender,
                "activity_level": activity_map[activity],
                "goals": goals,
                "created_at": datetime.now().isoformat()
            }
            
            # Simpan ke session
            st.session_state.user_data = user_data
            
            # Analisis dengan agent
            profile = agents['nutrition_analyst'].analyze_needs(user_data)
            st.session_state.nutrition_profile = profile
            st.session_state.user_identified = True
            
            # Tampilkan hasil
            st.success("✅ Profil berhasil dibuat! Sekarang AI mengenal Anda.")
            
            st.balloons()
            
            # Tampilkan hasil dalam container terpisah
            with st.container():
                st.markdown("---")
                st.subheader("📊 Hasil Analisis Anda")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("BMR (Basal)", f"{profile['bmr']:.0f} kcal")
                col2.metric("TDEE (Total)", f"{profile['tdee']:.0f} kcal")
                col3.metric("Target Harian", f"{profile['target_calories']:.0f} kcal")
                col4.metric("Protein", f"{profile['protein_g']:.1f} g")
                
                # Pesan personal
                st.markdown("---")
                gender_id = "Pria" if gender == "Male" else "Wanita"
                st.write(f"""
                **Profil:** {age} tahun, {gender_id}, {weight} kg, {height} cm  
                **Aktivitas:** {activity}  
                **Tujuan:** {', '.join(goals) if goals else 'Tidak spesifik'}
                """)
                
                # Rekomendasi AI
                with st.spinner("Membuat rekomendasi personal..."):
                    recs = agents['nutrition_analyst'].get_recommendations(user_data)
                    st.info(recs)
    
    # Tombol Chat Sekarang (DI LUAR FORM, tapi hanya muncul jika sudah submit)
    if submit or st.session_state.nutrition_profile:
        st.markdown("---")
        st.write("### 🗣️ Ingin berbicara dengan AI Nutritionist?")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("💬 Chat Sekarang", type="primary", use_container_width=True):
                st.session_state.page = "💬 Chat with AI"
                st.rerun()
    
    # Jika belum ada profil, tampilkan pesan default
    elif not st.session_state.nutrition_profile:
        st.info("""
        👋 **Selamat datang di analisis nutrisi!**
        
        Silakan isi form di atas untuk membuat profil nutrisi personal Anda.
        Setelah selesai, AI akan mengenal Anda dan bisa memberikan rekomendasi yang sesuai.
        """)

# 3. MEAL PLANNER
elif page == "🍽️ Meal Planner":
    st.header("Rencana Makan")
    if not st.session_state.nutrition_profile:
        st.warning("Harap lakukan Analisis Nutrisi dulu di menu 📊 Nutrition Analysis.")
        if st.button("📊 Buat Profil Saya", type="primary"):
            st.session_state.page = "📊 Nutrition Analysis"
            st.rerun()
    else:
        days = st.slider("Jumlah Hari", 1, 7, 3)
        pref = st.text_input("Preferensi Makanan", "Masakan Indonesia, Sehat")
        if st.button("🍴 Buat Menu Saya", type="primary"):
            with st.spinner("Menyusun menu personal..."):
                plan = agents['meal_planner'].generate_meal_plan(
                    st.session_state.nutrition_profile, days, [pref]
                )
                st.write(plan.get('meal_plan'))

# 4. ACTIVITY SYNC
elif page == "🏃 Activity Sync":
    st.header("Sinkronisasi Aktivitas")
    if not st.session_state.nutrition_profile:
        st.warning("Harap buat profil dulu untuk rekomendasi personal.")
        if st.button("📊 Buat Profil Saya", type="primary"):
            st.session_state.page = "📊 Nutrition Analysis"
            st.rerun()
    else:
        st.write(f"**Profil Aktif:** {st.session_state.user_data.get('name', 'User')}")
        act = st.selectbox("Jenis Olahraga", ["Lari", "Gym", "Renang", "Yoga", "Bersepeda", "Jalan Cepat"])
        dur = st.number_input("Durasi (menit)", 10, 180, 30)
        if st.button("💪 Hitung Kebutuhan Nutrisi", type="primary"):
            with st.spinner("Menghitung..."):
                res = agents['activity_sync'].calculate_post_workout_nutrition(act, dur)
                st.write(res)

# 5. MINDFUL EATING
elif page == "🧠 Mindful Eating":
    st.header("Mindful Eating")
    if not st.session_state.nutrition_profile:
        st.warning("Buat profil dulu untuk panduan personal.")
        if st.button("📊 Buat Profil Saya", type="primary"):
            st.session_state.page = "📊 Nutrition Analysis"
            st.rerun()
    else:
        st.write(f"Halo {st.session_state.user_data.get('name', 'User')}, bagaimana perasaan Anda hari ini?")
        mood = st.select_slider("Mood Anda", ["Stres", "Sedih", "Biasa", "Senang", "Sangat Senang"])
        if st.button("🎯 Dapatkan Panduan", type="primary"):
            with st.spinner("Menyiapkan panduan personal..."):
                res = agents['mindful_eating'].provide_mindful_eating_guidance({"mood": mood})
                st.write(res)

# 6. CHAT WITH AI
elif page == "💬 Chat with AI":
    st.header(f"💬 Chat dengan AI Nutritionist")
    
    # Tampilkan status user di bagian atas
    status_col1, status_col2 = st.columns([3, 1])
    
    with status_col1:
        if st.session_state.nutrition_profile:
            profile = st.session_state.nutrition_profile
            st.success(f"✅ **Status:** AI mengenal Anda ({st.session_state.user_data.get('name', 'User')})")
        else:
            st.warning("⚠️ **Status:** AI belum mengenal Anda")
    
    with status_col2:
        if st.button("📊 Buat/Edit Profil", type="secondary"):
            st.session_state.page = "📊 Nutrition Analysis"
            st.rerun()
    
    # Jika belum ada profil, beri pilihan
    if not st.session_state.nutrition_profile:
        st.info("""
        🤖 **AI Nutritionist:** Halo! Saya belum mengenal Anda.
        
        Untuk pengalaman chat yang personal, silakan:
        1. **Buat profil** dulu di menu **📊 Nutrition Analysis**
        2. Atau **tanyakan pertanyaan umum** tentang nutrisi
        
        Setelah punga profil, saya bisa memberikan saran yang spesifik untuk Anda!
        """)
    
    # Tampilkan ringkasan profil jika ada
    if st.session_state.nutrition_profile:
        with st.expander("👤 Profil Saya (AI menggunakan data ini)", expanded=False):
            profile = st.session_state.nutrition_profile
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Nama:** {st.session_state.user_data.get('name', 'User')}")
                st.write(f"**Usia:** {profile.get('age')} tahun")
                st.write(f"**Gender:** {profile.get('gender')}")
                st.write(f"**Berat/Tinggi:** {profile.get('weight_kg')} kg / {profile.get('height_cm')} cm")
            with col2:
                st.write(f"**Target Kalori:** {profile.get('target_calories', 0):.0f} kcal")
                st.write(f"**Target Protein:** {profile.get('protein_g', 0):.1f} g")
                st.write(f"**Aktivitas:** {profile.get('activity_level')}")
                st.write(f"**Tujuan:** {', '.join(profile.get('goals', []))}")
    
    # Tampilkan chat history
    st.markdown("---")
    st.subheader("Percakapan")
    
    # Jika belum ada chat history, beri contoh
    if not st.session_state.chat_history and st.session_state.nutrition_profile:
        st.info("💡 **Contoh pertanyaan yang bisa ditanyakan:**\n"
                "- 'Berapa target kalori harian saya?'\n"
                f"- 'Halo, perkenalkan diri saya ({st.session_state.user_data.get('name', 'User')})'\n"
                "- 'Apa yang harus saya makan untuk mencapai tujuan saya?'\n"
                "- 'Berdasarkan profil saya, apa saran Anda?'")
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Input chat
    prompt = st.chat_input("Tanya apa saja tentang nutrisi Anda...")
    
    if prompt:
        # Tambahkan ke history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Tampilkan pesan user
        with st.chat_message("user"):
            st.write(prompt)
        
        # Response AI
        with st.chat_message("assistant"):
            with st.spinner("AI sedang berpikir..."):
                try:
                    # Gunakan fungsi yang sudah diperbaiki
                    response = ai_chat_response(prompt)
                    st.write(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Maaf, terjadi error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
    
    # Tombol clear chat (jika ada history)
    if st.session_state.chat_history:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🗑️ Hapus Riwayat Chat", type="secondary", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()