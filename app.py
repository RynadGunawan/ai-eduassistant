import streamlit as st
import random
import model
import utils
import flashcard_generator
from answer_checker import check_flashcard_answers, create_answer_checker

# Muat file CSS
def load_css(file_name="styles.css"):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Panggil fungsi untuk memuat CSS
load_css()

# ===== Inisialisasi Session State =====
def init_session_state():
    # Nilai default untuk session state
    defaults = {
        'summary': "",
        'input_text': "",
        'flashcards': [],
        'show_answers': False,
        'processing': False,
        'flashcard_answers': {},
        'score': 0,
        'difficulty': 'medium',
        'learning_progress': 0,
        'detailed_results': [],
        'answer_checker': None,
        'learning_tips': [
            "Baca materi secara menyeluruh sebelum membuat ringkasan",
            "Fokus pada konsep utama saat membuat flashcard",
            "Ulangi materi 24 jam setelah belajar untuk meningkatkan retensi",
            "Gunakan teknik pomodoro (25 menit belajar, 5 menit istirahat)",
            "Ajarkan konsep yang baru dipelajari kepada orang lain"
        ]
    }
    
    # Inisialisasi session state jika belum ada
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ===== Sidebar Navigasi =====
st.sidebar.markdown("""
<div class="sidebar-header">
    <h2>📚 EduAI Assistant</h2>
    <p>Asisten Belajar Pintar</p>
</div>
""", unsafe_allow_html=True)

# Pilihan halaman
page = st.sidebar.radio(
    "🧭 Navigasi",
    ["📝 Input Teks", "📄 Hasil Ringkasan", "🧠 Kartu Belajar", "📊 Progress Belajar"],
    help="Pilih halaman yang ingin Anda kunjungi"
)

# Pengaturan tingkat kesulitan
st.sidebar.markdown("### ⚙️ Pengaturan Pembelajaran")
difficulty = st.sidebar.selectbox(
    "Tingkat Kesulitan",
    ["Mudah", "Sedang", "Sulit"],
    index=1,
    help="Pilih tingkat kesulitan materi"
)
# Simpan tingkat kesulitan dalam session state
st.session_state.difficulty = ['easy', 'medium', 'hard'][["Mudah", "Sedang", "Sulit"].index(difficulty)]

# Tips pembelajaran acak
st.sidebar.markdown("### 💡 Tips Pembelajaran")
st.sidebar.markdown(f"""
<div class="learning-tip">
    {random.choice(st.session_state.learning_tips)}
</div>
""", unsafe_allow_html=True)

# Informasi aplikasi
st.sidebar.markdown("---")
st.sidebar.info("""
**Fitur Utama:**
- Perangkuman otomatis dengan AI
- Generator flashcard interaktif
- Penilaian otomatis dengan fuzzy matching
- Pelacakan progress belajar
- Feedback pembelajaran detail
""")

# ===== Header Utama =====
st.markdown("""
<div class="main-header">
    <h1>🧠 AI EduAssistant - Pembelajaran Interaktif</h1>
    <p>Perangkat AI untuk meningkatkan efektivitas belajar</p>
</div>
""", unsafe_allow_html=True)

# ===== Halaman Input Teks =====
if page == "📝 Input Teks":
    st.markdown("### 📝 Masukkan Materi Belajar")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Pilihan mode input
        input_mode = st.radio(
            "Sumber Teks",
            ["✍️ Ketik Manual", "📁 Unggah PDF"],
            help="Pilih cara input materi"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Mode ketik manual
        if input_mode == "✍️ Ketik Manual":
            input_text = st.text_area(
                "Ketik atau tempel teks materi:",
                value=st.session_state.input_text,
                height=300,
                placeholder="Tempel materi belajar Anda di sini...",
                help="Minimal 100 kata untuk hasil optimal"
            )
            st.session_state.input_text = input_text
            
            # Tampilkan statistik teks
            if input_text:
                word_count = len(input_text.split())
                char_count = len(input_text)
                st.info(f"📊 Statistik: {word_count} kata | {char_count} karakter")
        
        # Mode unggah PDF
        else:
            uploaded_file = st.file_uploader(
                "Unggah file PDF:",
                type=["pdf"],
                help="Format yang didukung: PDF"
            )
            
            if uploaded_file is not None:
                # Ekstrak teks dari PDF
                with st.spinner("🔄 Mengekstrak teks dari PDF..."):
                    extracted_text = utils.extract_text_from_pdf(uploaded_file)
                
                if extracted_text and not extracted_text.startswith("Gagal membaca PDF"):
                    st.session_state.input_text = extracted_text
                    st.success("✅ Teks berhasil diekstrak!")
                    
                    word_count = len(extracted_text.split())
                    char_count = len(extracted_text)
                    st.info(f"📊 Statistik PDF: {word_count} kata | {char_count} karakter")
                else:
                    st.error(extracted_text)
            
            # Tampilkan preview teks
            if st.session_state.input_text:
                with st.expander("👁️ Lihat Preview Teks"):
                    preview_text = st.session_state.input_text[:1000] + "..." if len(st.session_state.input_text) > 1000 else st.session_state.input_text
                    st.text_area("", preview_text, height=200, disabled=True)

    with col2:
        # Panduan penggunaan
        st.markdown("### 🎯 Panduan Pembelajaran")
        st.markdown("""
        1. 📝 Input teks atau upload PDF
        2. 🔄 Buat ringkasan otomatis
        3. 🧠 Generate kartu belajar
        4. 📊 Latihan dan evaluasi
        5. 🔁 Ulangi materi sulit
        """)
        
        # Strategi belajar
        st.markdown("### 📈 Strategi Belajar Efektif")
        st.markdown("""
        - **Spaced Repetition**: Ulangi materi secara berkala
        - **Active Recall**: Uji diri dengan flashcard
        - **Interleaving**: Campur berbagai topik
        - **Elaboration**: Hubungkan dengan pengetahuan lain
        """)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tombol proses utama
    st.markdown("---")
    if st.button(
        "🚀 Buat Ringkasan & Kartu Belajar",
        type="primary",
        disabled=not st.session_state.input_text.strip()
    ):
        # Validasi panjang teks
        if len(st.session_state.input_text.strip()) < 100:
            st.warning("⚠️ Teks terlalu pendek. Minimal 100 karakter.")
        else:
            with st.spinner("🔄 Memproses dengan AI..."):
                # Reset state sebelum memproses
                st.session_state.flashcards = []
                st.session_state.show_answers = False
                st.session_state.flashcard_answers = {}
                st.session_state.score = 0
                st.session_state.detailed_results = []
                
                # Buat ringkasan
                st.session_state.summary = model.summarize_with_decision_tree(st.session_state.input_text)
                
                # Generate flashcards
                if st.session_state.summary:
                    st.session_state.flashcards = flashcard_generator.generate_flashcards_from_summary(
                        st.session_state.summary,
                        difficulty=st.session_state.difficulty
                    )
                
                # Update progress
                st.session_state.learning_progress += 10
                st.success("✅ Ringkasan dan kartu belajar berhasil dibuat!")
                st.balloons()

# ===== Halaman Hasil Ringkasan =====
elif page == "📄 Hasil Ringkasan":
    st.markdown("### 📄 Hasil Ringkasan AI")
    
    if st.session_state.summary:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Tampilkan ringkasan
            st.markdown("#### 📝 Ringkasan:")
            st.write(st.session_state.summary)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Tombol aksi
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📋 Salin Ringkasan", use_container_width=True):
                    st.code(st.session_state.summary)
                    st.success("Ringkasan siap disalin!")
            
            with col_b:
                if st.button("🔄 Buat Ulang Ringkasan", use_container_width=True):
                    if st.session_state.input_text:
                        with st.spinner("Membuat ringkasan baru..."):
                            st.session_state.summary = model.summarize_with_decision_tree(st.session_state.input_text)
                        st.rerun()
        
        with col2:
            # Statistik ringkasan
            st.markdown("#### 📊 Statistik Ringkasan")
            
            original_words = len(st.session_state.input_text.split()) if st.session_state.input_text else 0
            summary_words = len(st.session_state.summary.split())
            compression_ratio = (1 - summary_words/original_words) * 100 if original_words > 0 else 0
            
            st.metric("Kata Asli", f"{original_words:,}")
            st.metric("Kata Ringkasan", f"{summary_words:,}")
            st.metric("Tingkat Kompresi", f"{compression_ratio:.1f}%")
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("ℹ️ Belum ada ringkasan. Silakan input teks terlebih dahulu")
        st.markdown('</div>', unsafe_allow_html=True)

# ===== Halaman Kartu Belajar =====
elif page == "🧠 Kartu Belajar":
    st.markdown("### 🧠 Kartu Belajar Interaktif")
    
    # Validasi ringkasan
    if not st.session_state.summary:
        st.warning("⚠️ Silakan buat ringkasan terlebih dahulu")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    
    # Generate flashcards jika belum ada
    if not st.session_state.flashcards:
        with st.spinner("🔄 Membuat kartu belajar dari ringkasan..."):
            st.session_state.flashcards = flashcard_generator.generate_flashcards_from_summary(
                st.session_state.summary,
                difficulty=st.session_state.difficulty
            )
    
    if st.session_state.flashcards:
        st.markdown(f"**📊 Total Kartu: {len(st.session_state.flashcards)}**")
        st.markdown("---")
        
        # Tampilkan form pertanyaan
        for i, fc in enumerate(st.session_state.flashcards):
            st.markdown(f"#### 🎯 Soal {i+1}")
            st.markdown(f"**{fc['question']}**")
            
            # Input jawaban user
            answer_key = f"user_answer_{i}"
            user_answer = st.text_input(
                f"Jawaban Anda:",
                value=st.session_state.flashcard_answers.get(answer_key, ""),
                key=answer_key,
                placeholder="Ketik jawaban Anda..."
            )
            st.session_state.flashcard_answers[answer_key] = user_answer
            st.markdown('</div>', unsafe_allow_html=True)
        
        # ===== SISTEM PENGECEK JAWABAN BARU =====
        if st.button("🔍 Periksa Jawaban", type="primary"):
            # Inisialisasi pemeriksa jawaban
            if 'answer_checker' not in st.session_state:
                st.session_state.answer_checker = create_answer_checker()
            
            # Atur ambang batas berdasarkan kesulitan
            difficulty_thresholds = {
                'easy': 0.6,    # Lebih toleran untuk pemula
                'medium': 0.7,  # Standar
                'hard': 0.8     # Lebih ketat untuk tingkat sulit
            }
            
            threshold = difficulty_thresholds.get(st.session_state.difficulty, 0.7)
            
            # Periksa jawaban dengan sistem baru
            correct_count, detailed_results = check_flashcard_answers(
                st.session_state.flashcards,
                st.session_state.flashcard_answers,
                threshold
            )
            
            # Update session state
            st.session_state.show_answers = True
            st.session_state.score = (correct_count / len(st.session_state.flashcards)) * 100
            st.session_state.learning_progress = min(100, st.session_state.learning_progress + 20)
            st.session_state.detailed_results = detailed_results
            
            # Tampilkan hasil cepat
            st.success(f"✅ Selesai! {correct_count}/{len(st.session_state.flashcards)} jawaban benar")
        
        # Tampilkan hasil detail jika sudah diperiksa
        if st.session_state.show_answers:
            st.markdown("---")
            st.markdown("### 🎯 Hasil Pembelajaran Detail")
            
            # Tampilkan skor keseluruhan
            score = st.session_state.score
            if score >= 80:
                st.success(f"🎉 Excellent! Skor Anda: {score:.1f}% - Pemahaman sangat baik!")
            elif score >= 60:
                st.info(f"👍 Good Job! Skor Anda: {score:.1f}% - Terus tingkatkan!")
            else:
                st.warning(f"💪 Keep Learning! Skor Anda: {score:.1f}% - Butuh lebih banyak latihan!")
            
            # Tampilkan detail setiap jawaban
            for detail in st.session_state.get('detailed_results', []):
                question_num = detail['question_index'] + 1
                result = detail['result']
                
                st.markdown(f"#### 📝 Soal {question_num}: {detail['question']}")
                
                # Layout jawaban
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div class="correct-answer">', unsafe_allow_html=True)
                    st.markdown(f"✅ **Jawaban Benar:** {detail['correct_answer']}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    user_ans = detail['user_answer'] or '(Kosong)'
                    if result['is_correct']:
                        st.markdown('<div class="correct-answer">', unsafe_allow_html=True)
                        st.markdown(f"✅ **Jawaban Anda:** {user_ans}")
                    else:
                        st.markdown('<div class="user-answer">', unsafe_allow_html=True)
                        st.markdown(f"❌ **Jawaban Anda:** {user_ans}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Tampilkan skor detail
                col3, col4 = st.columns(2)
                
                with col3:
                    st.metric(
                        "Skor Kecocokan", 
                        f"{result['score']:.1%}",
                        help=f"Fuzzy: {result.get('fuzzy_score', 0):.1%} | Keyword: {result.get('keyword_score', 0):.1%}"
                    )
                
                with col4:
                    # Tampilkan feedback dengan warna sesuai skor
                    if result['score'] >= 0.8:
                        st.success(result['feedback'])
                    elif result['score'] >= 0.6:
                        st.info(result['feedback'])
                    else:
                        st.warning(result['feedback'])
                
                # Progress bar visual
                progress_html = f"""
                <div style="background-color: #f0f0f0; border-radius: 10px; padding: 3px; margin: 10px 0;">
                    <div style="background: linear-gradient(90deg, #4CAF50, #8BC34A); 
                                width: {result['score']*100}%; height: 20px; border-radius: 7px;
                                display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                        {result['score']:.1%}
                    </div>
                </div>
                """
                st.markdown(progress_html, unsafe_allow_html=True)
                
                st.markdown("---")
            
            # Ringkasan pembelajaran
            st.markdown("### 📊 Ringkasan Pembelajaran")
            
            # Hitung statistik
            total_questions = len(st.session_state.get('detailed_results', []))
            correct_answers = sum(1 for detail in st.session_state.get('detailed_results', []) 
                                if detail['result']['is_correct'])
            avg_score = sum(detail['result']['score'] for detail in st.session_state.get('detailed_results', [])) / total_questions if total_questions > 0 else 0
            
            # Tampilkan metrik
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Total Soal", total_questions)
            with col2: st.metric("Jawaban Benar", correct_answers)
            with col3: st.metric("Akurasi", f"{(correct_answers/total_questions)*100:.1f}%" if total_questions > 0 else "0%")
            with col4: st.metric("Rata-rata Skor", f"{avg_score:.1%}")
            
            # Saran pembelajaran berdasarkan skor
            st.markdown("### 💡 Saran Pembelajaran")
            if avg_score >= 0.8:
                st.success("""
                **Excellent Work!** 🎉
                - Pemahaman Anda sangat baik
                - Coba tingkatkan ke level kesulitan lebih tinggi
                - Lanjutkan ke materi berikutnya
                """)
            elif avg_score >= 0.6:
                st.info("""
                **Good Progress!** 👍
                - Pemahaman cukup baik, terus berlatih
                - Fokus pada soal yang skornya rendah
                - Ulangi materi yang masih kurang dipahami
                """)
            else:
                st.warning("""
                **Keep Learning!** 💪
                - Pelajari kembali materi dasar
                - Buat catatan untuk konsep yang sulit
                - Minta bantuan atau cari sumber tambahan
                - Jangan menyerah, terus berlatih!
                """)
            
            # Tombol aksi lanjutan
            col_a, col_b, col_c = st.columns(3)
            with col_a: st.button("🔄 Coba Lagi", use_container_width=True)
            with col_b: st.button("📚 Pelajari Ulang", use_container_width=True)
            with col_c: st.button("📝 Materi Baru", use_container_width=True)
    
    else:
        st.error("❌ Tidak dapat membuat kartu belajar dari ringkasan ini.")

# ===== Halaman Progress Belajar =====
elif page == "📊 Progress Belajar":
    st.markdown("### 📊 Progress Pembelajaran")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Tampilkan progress utama
        st.markdown("#### 📈 Ringkasan Pembelajaran")
        progress = st.session_state.learning_progress
        st.metric("Progress Pembelajaran", f"{progress}%")
        
        # Progress bar visual
        st.markdown("""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {0}%"></div>
        </div>
        """.format(progress), unsafe_allow_html=True)
        
        # Statistik tambahan
        st.metric("Teks Input", "✅ Ada" if st.session_state.input_text else "❌ Belum")
        st.metric("Ringkasan", "✅ Dibuat" if st.session_state.summary else "❌ Belum")
        st.metric("Kartu Belajar", f"✅ {len(st.session_state.flashcards)}" if st.session_state.flashcards else "❌ Belum")
        
        # Tampilkan skor terakhir jika ada
        if st.session_state.score > 0:
            st.metric("Skor Terakhir", f"{st.session_state.score:.1f}%")
        
        # Statistik detail jika sudah mengerjakan
        if st.session_state.get('detailed_results'):
            total_questions = len(st.session_state.detailed_results)
            correct_answers = sum(1 for detail in st.session_state.detailed_results 
                                if detail['result']['is_correct'])
            avg_score = sum(detail['result']['score'] for detail in st.session_state.detailed_results) / total_questions
            
            st.markdown("#### 📊 Detail Performa")
            st.metric("Akurasi Jawaban", f"{(correct_answers/total_questions)*100:.1f}%")
            st.metric("Rata-rata Skor", f"{avg_score:.1%}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Rencana belajar
        st.markdown("#### 🎯 Rencana Belajar")
        steps = [
            ("📝 Input materi", bool(st.session_state.input_text)),
            ("📄 Buat ringkasan", bool(st.session_state.summary)),
            ("🧠 Kerjakan flashcard", bool(st.session_state.flashcards)),
            ("🎯 Selesaikan evaluasi", st.session_state.score > 0)
        ]
        
        completed = sum(1 for _, done in steps if done)
        total_steps = len(steps)
        st.markdown(f"**Progress: {completed}/{total_steps} langkah**")
        
        # Tampilkan checklist langkah
        for step, done in steps:
            icon = "✅" if done else "⏳"
            st.markdown(f"{icon} {step}")
        
        st.markdown("---")
        # Saran berdasarkan progress
        st.markdown("### 🔁 Saran Pembelajaran")
        if st.session_state.score < 60 and st.session_state.score > 0:
            st.info("""
            **Saran:**
            - Ulangi materi yang sulit
            - Buat ringkasan ulang
            - Fokus pada konsep yang salah di flashcard
            """)
        elif st.session_state.learning_progress < 50:
            st.info("""
            **Saran:**
            - Lanjutkan ke tahap berikutnya
            - Coba kerjakan flashcard
            - Tambahkan materi baru
            """)
        else:
            st.info("""
            **Saran:**
            - Coba materi dengan tingkat kesulitan lebih tinggi
            - Tinjau kembali progress belajar
            - Beri istirahat untuk otak
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)

# ===== Footer =====
st.markdown("---")
# Tombol reset
if st.button("🔄 Reset Semua Data", type="secondary"):
    # Reset semua state
    st.session_state.summary = ""
    st.session_state.input_text = ""
    st.session_state.flashcards = []
    st.session_state.show_answers = False
    st.session_state.flashcard_answers = {}
    st.session_state.score = 0
    st.session_state.learning_progress = 0
    st.session_state.detailed_results = []
    st.session_state.answer_checker = None
    st.success("✅ Semua data telah direset!")
    st.rerun()

# Footer aplikasi
st.markdown("""
<div class="footer">
    <p>🧠 <strong>AI EduAssistant</strong> - Powered by Learning Science</p>
    <p>Menerapkan prinsip pembelajaran berbasis bukti untuk hasil optimal</p>
</div>
""", unsafe_allow_html=True)