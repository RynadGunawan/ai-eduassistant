import re
import random
from model import indonesian_sent_tokenize

def generate_flashcards_from_summary(summary, difficulty='medium', max_cards=15):
    # Validasi jika ringkasan terlalu pendek
    if not summary or len(summary.strip()) < 20:
        return [{"question": "Ringkasan terlalu pendek untuk membuat flashcard.", "answer": "", "type": "error"}]
    
    try:
        # Memisahkan ringkasan menjadi kalimat-kalimat
        sentences = indonesian_sent_tokenize(summary)
        
        # Validasi jumlah kalimat
        if len(sentences) < 2:
            return [{"question": "Tidak cukup kalimat untuk membuat flashcard.", "answer": "", "type": "error"}]
        
        # Menentukan jenis flashcard berdasarkan tingkat kesulitan
        if difficulty == 'easy':
            include_types = ['definition', 'fill_blank']
        elif difficulty == 'medium':
            include_types = ['definition', 'fill_blank', 'short_answer']
        else:  # hard
            include_types = ['definition', 'fill_blank', 'short_answer', 'multiple_choice', 'true_false']
        
        # Inisialisasi wadah untuk flashcard
        flashcards = []
        
        # PERBAIKAN: Membuat flashcard definisi dengan pola yang lebih akurat
        if 'definition' in include_types:
            for sentence in sentences:
                # Pola 1: Mencari format "X adalah Y" (konsep + definisi)
                pattern1 = r'^([A-Z][a-zA-Z\s]{2,30}?)\s+(adalah|merupakan)\s+(.{10,}?)(?=\.|$)'
                matches = re.finditer(pattern1, sentence.strip())
                for match in matches:
                    concept = match.group(1).strip()
                    connector = match.group(2)
                    definition = match.group(3).strip()
                    
                    # Penyaringan: Pastikan konsep valid dan definisi sesuai
                    if (len(concept.split()) <= 4 and 
                        not any(word in concept.lower() for word in ['solusi', 'upaya', 'cara', 'metode', 'antara lain', 'seperti']) and
                        len(definition) > 15 and len(definition) < 200):
                        
                        # Tambahkan flashcard definisi
                        flashcards.append({
                            "question": f"Apa yang dimaksud dengan {concept}?",
                            "answer": definition.rstrip('.,!?'),
                            "type": "definition"
                        })
                
                # Pola 2: Mencari format "Y yaitu X" (konsep + definisi alternatif)
                pattern2 = r'([A-Z][a-zA-Z\s]{2,30}?)\s+(yaitu|yakni)\s+(.{10,}?)(?=\.|$)'
                matches = re.finditer(pattern2, sentence.strip())
                for match in matches:
                    concept = match.group(1).strip()
                    definition = match.group(3).strip()
                    
                    # Penyaringan konsep dan definisi
                    if (len(concept.split()) <= 4 and 
                        len(definition) > 15 and len(definition) < 200):
                        
                        # Tambahkan flashcard definisi
                        flashcards.append({
                            "question": f"Apa yang dimaksud dengan {concept}?",
                            "answer": definition.rstrip('.,!?'),
                            "type": "definition"
                        })
        
        # PERBAIKAN: Membuat flashcard isian dengan penyaringan lebih baik
        if 'fill_blank' in include_types:
            for sentence in sentences:
                words = sentence.split()
                # Hanya proses kalimat dengan cukup kata
                if len(words) > 6:
                    # Kumpulkan kandidat kata yang bisa dijadikan blank
                    candidates = []
                    for i, word in enumerate(words):
                        clean_word = re.sub(r'[^\w]', '', word)
                        # Kriteria kata yang cocok untuk blank:
                        # 1. Panjang > 4 karakter
                        # 2. Bukan kata penghubung umum
                        # 3. Bukan di posisi ujung kalimat
                        if (len(clean_word) > 4 and 
                            clean_word.lower() not in ['adalah', 'merupakan', 'yaitu', 'yakni', 'seperti', 'antara', 'dengan', 'kepada', 'terhadap', 'sehingga', 'karena', 'namun', 'tetapi', 'akan', 'dapat', 'bisa'] and
                            i > 0 and i < len(words) - 1):
                            candidates.append((i, word, clean_word))
                    
                    # Pilih satu kata acak jika ada kandidat
                    if candidates:
                        idx, original_word, blank_word = random.choice(candidates)
                        question = sentence.replace(original_word, "_____", 1)
                        flashcards.append({
                            "question": question,
                            "answer": blank_word,
                            "type": "fill_blank"
                        })
        
        # PERBAIKAN UTAMA: Flashcard jawaban pendek dengan pola lebih spesifik
        if 'short_answer' in include_types:
            # Pola pertanyaan-jawaban yang didukung:
            qa_patterns = [
                # Pola fungsi/kegunaan: [X] berfungsi untuk [Y]
                (r'(.+?)\s+(berfungsi|berguna|digunakan)\s+untuk\s+(.+?)(?=[.!?]|$)', 
                 "Apa fungsi dari {}?", 3),
                
                # Pola penyebab: [X] disebabkan oleh [Y]
                (r'(.+?)\s+(disebabkan|diakibatkan)\s+oleh\s+(.+?)(?=[.!?]|$)', 
                 "Apa yang menyebabkan {}?", 3),
                
                # Pola lokasi: [X] terletak di [Y]
                (r'(.+?)\s+(terletak|berada|terdapat)\s+di\s+(.+?)(?=[.!?]|$)', 
                 "Di mana {}?", 3),
                
                # Pola dampak: [X] menyebabkan [Y]
                (r'(.+?)\s+(menyebabkan|mengakibatkan|menimbulkan)\s+(.+?)(?=[.!?]|$)', 
                 "Apa dampak dari {}?", 3),
                
                # Pola contoh: [X] seperti [Y]
                (r'(.+?)\s+(seperti|contohnya|misalnya|antara lain)\s+([^.!?]+?)(?=[.!?]|$)', 
                 "Sebutkan contoh dari {}!", 3),
            ]
            
            # Cocokkan pola dengan setiap kalimat
            for pattern, template, answer_group in qa_patterns:
                for sentence in sentences:
                    match = re.search(pattern, sentence, re.IGNORECASE)
                    if match:
                        subject = match.group(1).strip()
                        answer = match.group(answer_group).strip()
                        
                        # Penyaringan hasil yang valid
                        if (len(subject.split()) <= 6 and 
                            len(answer) > 5 and len(answer) < 150 and
                            not subject.lower().startswith(('solusi', 'upaya', 'cara')) and
                            not any(word in answer.lower() for word in ['seperti', 'contohnya', 'misalnya', 'antara lain'])):
                            
                            # Format pertanyaan khusus untuk pola contoh
                            if "contoh" in template:
                                question = template.format(subject)
                            else:
                                question = template.format(subject)
                            
                            # Tambahkan flashcard
                            flashcards.append({
                                "question": question,
                                "answer": answer.rstrip('.,!?'),
                                "type": "short_answer"
                            })
        
        # PERBAIKAN: Flashcard pilihan ganda dengan distraktor lebih relevan
        if 'multiple_choice' in include_types:
            for sentence in sentences:
                # Cari kalimat yang mengandung angka atau indikator daftar
                if re.search(r'\b\d+\b', sentence) or any(word in sentence.lower() for word in ['pertama', 'kedua', 'ketiga']):
                    words = sentence.split()
                    # Hanya proses kalimat panjang
                    if len(words) > 8:
                        # Ekstrak konsep dan jawaban benar
                        key_info = re.search(r'(.+?)\s+(adalah|merupakan|yaitu)\s+(.+)', sentence)
                        if key_info:
                            concept = key_info.group(1)
                            correct_answer = key_info.group(3).rstrip('.,!?')
                            
                            # Pastikan jawaban tidak terlalu panjang
                            if len(correct_answer) < 100:
                                # Buat opsi jawaban salah (distraktor)
                                distractors = [
                                    correct_answer.split()[0] + " yang berbeda",
                                    "konsep yang berlawanan",
                                    "fenomena terkait"
                                ]
                                
                                # Gabungkan jawaban benar dan salah
                                options = [correct_answer] + distractors[:2]
                                random.shuffle(options)
                                # Tentukan indeks jawaban benar
                                correct_index = options.index(correct_answer)
                                
                                # Tambahkan flashcard
                                flashcards.append({
                                    "question": f"Apa yang dimaksud dengan {concept}?",
                                    "answer": f"Pilihan: A) {options[0]} B) {options[1]} C) {options[2]} | Jawaban: {chr(65 + correct_index)}",
                                    "type": "multiple_choice"
                                })
        
        # Hapus duplikat dan batasi jumlah flashcard
        seen_questions = set()
        unique_flashcards = []
        for card in flashcards:
            if card["question"] not in seen_questions:
                seen_questions.add(card["question"])
                unique_flashcards.append(card)
        
        # Potong sesuai batas maksimal
        unique_flashcards = unique_flashcards[:max_cards]
        
        # Cadangan jika tidak ada flashcard yang berhasil dibuat
        if not unique_flashcards:
            for i, sent in enumerate(sentences[:5]):
                words = sent.split()
                if len(words) > 6:
                    # Pilih kata acak di tengah kalimat
                    start_idx = max(1, len(words) // 4)
                    end_idx = min(len(words) - 1, 3 * len(words) // 4)
                    idx = random.randint(start_idx, end_idx)
                    
                    original_word = words[idx]
                    clean_word = re.sub(r'[^\w]', '', original_word)
                    
                    # Buat flashcard isian sederhana
                    if len(clean_word) > 3:
                        question = sent.replace(original_word, "_____", 1)
                        unique_flashcards.append({
                            "question": question,
                            "answer": clean_word,
                            "type": "simple"
                        })
        
        return unique_flashcards
    
    except Exception as e:
        return [{"question": f"Error: {str(e)}", "answer": "", "type": "error"}]


def validate_flashcard_quality(flashcards):
    """Memeriksa kualitas flashcard yang dihasilkan"""
    quality_issues = []
    
    for i, card in enumerate(flashcards):
        # Cek pertanyaan mengandung kata tidak diinginkan
        if any(phrase in card["question"].lower() for phrase in 
               ["antara lain", "seperti", "misalnya", "yaitu", "yakni"]):
            quality_issues.append(f"Card {i+1}: Pertanyaan mengandung kata penghubung yang tidak tepat")
        
        # Cek panjang jawaban
        if len(card["answer"]) > 200:
            quality_issues.append(f"Card {i+1}: Jawaban terlalu panjang")
        elif len(card["answer"]) < 3:
            quality_issues.append(f"Card {i+1}: Jawaban terlalu pendek")
        
        # Cek jawaban berupa kata penghubung
        if card["answer"].lower() in ['seperti', 'contohnya', 'misalnya', 'antara lain']:
            quality_issues.append(f"Card {i+1}: Jawaban berupa kata penghubung yang tidak tepat")
    
    return quality_issues