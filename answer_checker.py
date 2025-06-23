import re
import difflib
from typing import Dict, List, Tuple

class AnswerChecker:
    def __init__(self):
        # Kamus sinonim bahasa Indonesia
        self.synonyms = {
            'adalah': ['merupakan', 'ialah', 'yaitu', 'yakni'],
            # ... (sinonim lainnya tetap sama) ...
        }
        
        # Kata-kata yang bisa diabaikan saat pengecekan jawaban
        self.stop_words = {
            'yang', 'dan', 'atau', 'dengan', 'pada', 'di', 'ke', 'dari', 'untuk',
            # ... (stop words lainnya tetap sama) ...
        }
        
        # Pola untuk normalisasi singkatan bahasa Indonesia
        self.normalization_patterns = [
            (r'\bdrpd\b', 'daripada'),
            (r'\bdg\b', 'dengan'),
            # ... (pola lainnya tetap sama) ...
        ]
    
    def normalize_text(self, text: str) -> str:
        """Normalisasi teks untuk mempermudah perbandingan"""
        if not text:
            return ""
        
        # Ubah ke huruf kecil dan hilangkan spasi di awal/akhir
        text = text.lower().strip()
        
        # Hapus tanda baca berlebihan
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Ganti singkatan dengan kata lengkap
        for pattern, replacement in self.normalization_patterns:
            text = re.sub(pattern, replacement, text)
        
        # Normalisasi spasi ganda
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_keywords(self, text: str) -> List[str]:
        """Ambil kata kunci penting dari teks"""
        normalized = self.normalize_text(text)
        words = normalized.split()
        
        # Filter stop words dan kata terlalu pendek
        keywords = [word for word in words 
                   if word not in self.stop_words and len(word) > 2]
        
        return keywords
    
    def get_synonyms(self, word: str) -> List[str]:
        """Dapatkan semua sinonim untuk sebuah kata"""
        word_lower = word.lower()
        
        # Cari di kamus sinonim
        for main_word, synonym_list in self.synonyms.items():
            if word_lower == main_word or word_lower in synonym_list:
                return [main_word] + synonym_list
        
        return [word_lower]
    
    def fuzzy_match_score(self, text1: str, text2: str) -> float:
        """Hitung tingkat kemiripan dua teks"""
        normalized1 = self.normalize_text(text1)
        normalized2 = self.normalize_text(text2)
        
        # Jika salah satu kosong
        if not normalized1 or not normalized2:
            return 0.0
        
        # Jika sama persis setelah normalisasi
        if normalized1 == normalized2:
            return 1.0
        
        # Hitung kemiripan urutan karakter
        sequence_ratio = difflib.SequenceMatcher(None, normalized1, normalized2).ratio()
        
        return sequence_ratio
    
    def keyword_match_score(self, user_answer: str, correct_answer: str) -> float:
        """Hitung skor berdasarkan kecocokan kata kunci penting"""
        user_keywords = self.extract_keywords(user_answer)
        correct_keywords = self.extract_keywords(correct_answer)
        
        if not correct_keywords:
            return 0.0
        
        matched_keywords = 0
        total_keywords = len(correct_keywords)
        
        # Cek setiap kata kunci jawaban benar
        for correct_keyword in correct_keywords:
            correct_synonyms = self.get_synonyms(correct_keyword)
            
            # Cek apakah ada sinonim yang cocok di jawaban user
            for user_keyword in user_keywords:
                user_synonyms = self.get_synonyms(user_keyword)
                
                # Cek apakah ada sinonim yang sama
                if set(correct_synonyms) & set(user_synonyms):
                    matched_keywords += 1
                    break
                
                # Cek kemiripan untuk typo/kesalahan ketik
                for c_syn in correct_synonyms:
                    for u_syn in user_synonyms:
                        if difflib.SequenceMatcher(None, c_syn, u_syn).ratio() > 0.8:
                            matched_keywords += 1
                            break
                    if matched_keywords > len(correct_keywords):
                        break
                
                if matched_keywords > len(set(correct_keywords)):
                    break
        
        return min(matched_keywords / total_keywords, 1.0)
    
    def number_match_score(self, user_answer: str, correct_answer: str) -> float:
        """Khusus untuk jawaban yang mengandung angka"""
        user_numbers = re.findall(r'\d+(?:\.\d+)?', user_answer)
        correct_numbers = re.findall(r'\d+(?:\.\d+)?', correct_answer)
        
        if not correct_numbers:
            return 0.0
        
        if not user_numbers:
            return 0.0
        
        # Bandingkan angka
        matched = 0
        for correct_num in correct_numbers:
            if correct_num in user_numbers:
                matched += 1
        
        return matched / len(correct_numbers)
    
    def check_answer(self, user_answer: str, correct_answer: str, 
                    threshold: float = 0.7) -> Dict:
        """
        Fungsi utama untuk mengecek jawaban
        
        Args:
            user_answer: Jawaban dari pengguna
            correct_answer: Jawaban yang benar
            threshold: Batas minimal untuk dianggap benar (0.0-1.0)
        
        Returns:
            Dict berisi hasil pemeriksaan
        """
        if not user_answer or not user_answer.strip():
            return {
                'is_correct': False,
                'score': 0.0,
                'feedback': 'Jawaban kosong',
                'method': 'empty'
            }
        
        # Hitung berbagai jenis skor
        fuzzy_score = self.fuzzy_match_score(user_answer, correct_answer)
        keyword_score = self.keyword_match_score(user_answer, correct_answer)
        number_score = self.number_match_score(user_answer, correct_answer)
        
        # Bobot untuk setiap metode pengecekan
        weights = {
            'fuzzy': 0.4,    # Kemiripan teks
            'keyword': 0.5,  # Kata kunci
            'number': 0.1    # Angka
        }
        
        # Hitung skor gabungan
        combined_score = (
            fuzzy_score * weights['fuzzy'] +
            keyword_score * weights['keyword'] +
            number_score * weights['number']
        )
        
        # Tentukan metode terbaik yang digunakan
        best_method = 'fuzzy'
        best_score = fuzzy_score
        
        if keyword_score > best_score:
            best_method = 'keyword'
            best_score = keyword_score
        
        if number_score > best_score and number_score > 0:
            best_method = 'number'
            best_score = number_score
        
        # Gunakan skor tertinggi sebagai final score
        final_score = max(fuzzy_score, keyword_score, combined_score)
        
        # Tentukan apakah jawaban benar
        is_correct = final_score >= threshold
        
        # Buat feedback untuk pengguna
        feedback = self._generate_feedback(
            user_answer, correct_answer, final_score, best_method
        )
        
        return {
            'is_correct': is_correct,
            'score': final_score,
            'fuzzy_score': fuzzy_score,
            'keyword_score': keyword_score,
            'number_score': number_score,
            'combined_score': combined_score,
            'feedback': feedback,
            'method': best_method,
            'threshold': threshold
        }
    
    def _generate_feedback(self, user_answer: str, correct_answer: str, 
                          score: float, method: str) -> str:
        """Buat feedback berdasarkan hasil pengecekan"""
        if score >= 0.9:
            return "Sempurna! Jawaban Anda benar."
        elif score >= 0.8:
            return "Sangat baik! Jawaban Anda hampir tepat."
        elif score >= 0.7:
            return "Baik! Jawaban Anda cukup tepat."
        elif score >= 0.5:
            return "Cukup baik, tapi masih bisa diperbaiki."
        elif score >= 0.3:
            return "Jawaban kurang tepat, coba lagi."
        else:
            return "Jawaban belum benar, silakan pelajari lagi."
    
    def batch_check_answers(self, answers: List[Tuple[str, str]], 
                           threshold: float = 0.7) -> List[Dict]:
        """Cek banyak jawaban sekaligus"""
        results = []
        for user_ans, correct_ans in answers:
            result = self.check_answer(user_ans, correct_ans, threshold)
            results.append(result)
        return results

# Fungsi untuk integrasi dengan Streamlit
def create_answer_checker():
    """Buat instance AnswerChecker"""
    return AnswerChecker()

# Fungsi untuk mengganti logic pemeriksaan di app.py
def check_flashcard_answers(flashcards: List[Dict], user_answers: Dict, 
                          threshold: float = 0.7) -> Tuple[int, List[Dict]]:
    """
    Fungsi untuk memeriksa jawaban flashcard
    
    Args:
        flashcards: Daftar flashcard format {'question': str, 'answer': str}
        user_answers: Jawaban user format {'user_answer_i': str}
        threshold: Batas minimal untuk dianggap benar
    
    Returns:
        Tuple (jumlah_benar, detail_hasil)
    """
    checker = AnswerChecker()
    correct_count = 0
    detailed_results = []
    
    for i, fc in enumerate(flashcards):
        user_answer = user_answers.get(f"user_answer_{i}", "")
        correct_answer = str(fc.get('answer', ''))
        
        result = checker.check_answer(user_answer, correct_answer, threshold)
        
        if result['is_correct']:
            correct_count += 1
        
        detailed_results.append({
            'question_index': i,
            'question': fc.get('question', ''),
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'result': result
        })
    
    return correct_count, detailed_results