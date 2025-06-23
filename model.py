# model.py
import re
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class SimpleTokenizer:
    """Tokeniser sederhana yang menggunakan file konfigurasi JSON"""
    
    def __init__(self, config_path="./"):
        self.config_path = config_path
        self.vocab = {}
        self.special_tokens = {}
        self.load_tokenizer_config()
    
    def load_tokenizer_config(self):
        """Memuat konfigurasi tokeniser dari file JSON"""
        try:
            # Memuat konfigurasi tokeniser
            with open(f"{self.config_path}/tokenizer_config.json", 'r', encoding='utf-8') as f:
                self.tokenizer_config = json.load(f)
            
            # Memuat token khusus
            with open(f"{self.config_path}/special_tokens_map.json", 'r', encoding='utf-8') as f:
                self.special_tokens = json.load(f)
            
            # Memuat kosakata dari tokenizer.json
            with open(f"{self.config_path}/tokenizer.json", 'r', encoding='utf-8') as f:
                tokenizer_data = json.load(f)
                if 'model' in tokenizer_data and 'vocab' in tokenizer_data['model']:
                    self.vocab = tokenizer_data['model']['vocab']
            
            print(f"Tokenizer loaded successfully with {len(self.vocab)} vocab items")
            
        except FileNotFoundError as e:
            print(f"Warning: Could not load tokenizer config: {e}")
            print("Using fallback tokenizer")
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing JSON config: {e}")
            print("Using fallback tokenizer")
    
    def tokenize(self, text):
        """Tokenisasi sederhana - dipisahkan oleh spasi dan tanda baca"""
        tokens = re.findall(r'\w+|[^\w\s]', text.lower())
        return tokens
    
    def encode(self, text):
        """Encode teks menjadi ID token"""
        tokens = self.tokenize(text)
        token_ids = []
        for token in tokens:
            if token in self.vocab:
                token_ids.append(self.vocab[token])
            else:
                # Gunakan ID token tidak dikenal jika tersedia
                unk_token = self.special_tokens.get('unk_token', '<unk>')
                token_ids.append(self.vocab.get(unk_token, 0))
        return token_ids
    
    def decode(self, token_ids):
        """Dekode ID token kembali menjadi teks"""
        reverse_vocab = {v: k for k, v in self.vocab.items()}
        tokens = [reverse_vocab.get(tid, '<unk>') for tid in token_ids]
        return ' '.join(tokens)

def load_model(model_path="./"):
    """Memuat tokeniser sederhana dari file konfigurasi JSON"""
    tokenizer = SimpleTokenizer(model_path)
    # Ringkasan akan mengandalkan pendekatan decision tree
    return tokenizer, None

# ===== Tokenizer Bahasa Indonesia yang Lebih Baik =====
def indonesian_sent_tokenize(text):
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    
    # Pola batas kalimat bahasa Indonesia
    sentence_patterns = [
        r'(?<=[.!?])\s+(?=[A-Z])',  # Setelah tanda baca, sebelum huruf kapital
        r'(?<=[.!?])\s+(?=\d)',     # Setelah tanda baca, sebelum angka
        r'(?<=\w[.!?])\s+(?=[A-Z])', # Setelah kata+tanda baca, sebelum huruf kapital
        r'(?<=\.)\s+(?=[A-Z][a-z])', # Setelah titik, sebelum kata kapital
    ]
    
    sentences = [text]
    for pattern in sentence_patterns:
        new_sentences = []
        for sent in sentences:
            new_sentences.extend(re.split(pattern, sent))
        sentences = new_sentences
    
    # Bersihkan dan saring kalimat
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    return sentences

# ===== Preprocessing untuk Bahasa Indonesia =====
def preprocess_indonesian_text(text):
    """Praproses teks bahasa Indonesia"""
    text = re.sub(r'[^\w\s.,!?;:\-àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

# ===== Ekstraksi Fitur untuk Bahasa Indonesia =====
def extract_indonesian_features(sentences):
    # Kata kunci penting bahasa Indonesia
    important_keywords = [
        'adalah', 'merupakan', 'yaitu', 'yakni', 'berupa', 'terdiri',
        'pertama', 'kedua', 'ketiga', 'keempat', 'kelima',
        'utama', 'penting', 'hasil', 'kesimpulan', 'ringkasan',
        'menunjukkan', 'membuktikan', 'menghasilkan', 'menyebabkan',
        'sebab', 'karena', 'oleh karena itu', 'dengan demikian',
        'definisi', 'pengertian', 'maksud', 'arti', 'makna',
        'fungsi', 'tujuan', 'manfaat', 'kegunaan'
    ]
    
    # Kata penghubung bahasa Indonesia
    connective_words = [
        'namun', 'tetapi', 'akan tetapi', 'meskipun', 'walaupun',
        'selain itu', 'di samping itu', 'lebih lanjut', 'kemudian',
        'setelah itu', 'selanjutnya', 'pada akhirnya', 'akhirnya',
        'dengan kata lain', 'artinya', 'maksudnya'
    ]
    
    features = []
    
    for i, sent in enumerate(sentences):
        sent_lower = sent.lower()
        words = sent.split()
        
        # Fitur dasar
        word_count = len(words)
        char_count = len(sent)
        position_ratio = i / len(sentences) if len(sentences) > 1 else 0
        
        # Fitur kata kunci
        keyword_score = sum(1 for keyword in important_keywords if keyword in sent_lower)
        keyword_ratio = keyword_score / len(words) if len(words) > 0 else 0
        
        # Kata penghubung
        connective_score = sum(1 for conn in connective_words if conn in sent_lower)
        
        # Fitur numerik dan struktural
        number_count = len(re.findall(r'\d+', sent))
        capital_words = len(re.findall(r'\b[A-Z][a-z]*\b', sent))
        punctuation_score = sent.count(',') + sent.count(';') + sent.count(':')
        
        # Fitur posisi
        is_first_sentence = 1 if i == 0 else 0
        is_last_sentence = 1 if i == len(sentences) - 1 else 0
        
        features.append([
            word_count,
            char_count,
            position_ratio,
            keyword_ratio,
            connective_score,
            number_count,
            capital_words,
            punctuation_score,
            is_first_sentence,
            is_last_sentence
        ])
    
    return features

# ===== Model Classification untuk Bahasa Indonesia =====
class IndonesianSentenceClassifier:
    """Klasifikasi kalimat bahasa Indonesia menggunakan pendekatan berbasis aturan"""
    
    def __init__(self):
        self.important_keywords = [
            'adalah', 'merupakan', 'yaitu', 'yakni', 'berupa', 'terdiri',
            'pertama', 'kedua', 'ketiga', 'utama', 'penting', 'hasil',
            'kesimpulan', 'menunjukkan', 'membuktikan', 'menghasilkan',
            'sebab', 'karena', 'oleh karena itu', 'dengan demikian',
            'definisi', 'pengertian', 'maksud', 'arti', 'fungsi', 'tujuan'
        ]
        
        self.connective_words = [
            'namun', 'tetapi', 'akan tetapi', 'meskipun', 'walaupun',
            'selain itu', 'di samping itu', 'lebih lanjut', 'kemudian',
            'dengan kata lain', 'artinya', 'maksudnya'
        ]
    
    def predict(self, features):
        predictions = []
        
        for feature in features:
            (word_count, char_count, position_ratio, keyword_ratio, 
             connective_score, number_count, capital_words, punctuation_score,
             is_first_sentence, is_last_sentence) = feature
            
            score = 0
            
            # Pentingnya posisi
            if is_first_sentence or is_last_sentence:
                score += 0.3
            
            # Pentingnya kata kunci
            if keyword_ratio > 0:
                score += keyword_ratio * 2
            
            # Pertimbangan panjang
            if 8 <= word_count <= 25:
                score += 0.2
            
            # Kata penghubung
            if connective_score > 0:
                score += 0.15
            
            # Angka sering menunjukkan fakta penting
            if number_count > 0:
                score += 0.1
            
            # Kata benda yang tepat
            if capital_words > 0:
                score += 0.1
            
            # Kalimat kompleks
            if punctuation_score > 0:
                score += 0.05
            
            # Klasifikasikan sebagai penting jika skor melebihi ambang
            predictions.append(1 if score >= 0.4 else 0)
        
        return predictions

# Inisialisasi klasifikasi
clf_indonesian = IndonesianSentenceClassifier()

# ===== TF-IDF untuk Ranking Tambahan =====
def calculate_tfidf_scores(sentences):
    if len(sentences) < 2:
        return [1.0] * len(sentences)
    
    try:
        processed_sentences = []
        for sent in sentences:
            processed = re.sub(r'[^\w\s]', '', sent.lower())
            processed_sentences.append(processed)
        
        # Stop words bahasa Indonesia
        indonesian_stop_words = [
            'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 'pada',
            'dalam', 'oleh', 'akan', 'telah', 'sudah', 'ini', 'itu',
            'atau', 'juga', 'dapat', 'bisa', 'ada', 'tidak', 'belum'
        ]
        
        vectorizer = TfidfVectorizer(
            stop_words=indonesian_stop_words,
            max_features=1000,
            ngram_range=(1, 2)
        )
        
        tfidf_matrix = vectorizer.fit_transform(processed_sentences)
        scores = np.mean(tfidf_matrix.toarray(), axis=1)
        
        # Normalisasi skor
        if np.max(scores) > np.min(scores):
            scores = (scores - np.min(scores)) / (np.max(scores) - np.min(scores))
        
        return scores.tolist()
    
    except Exception as e:
        print(f"TF-IDF calculation error: {e}")
        return [1.0] * len(sentences)

# ===== Fungsi Utama Summarizer =====
def summarize_with_decision_tree(text, max_sentences=None, min_sentences=2):
    try:
        # Praproses teks
        text = preprocess_indonesian_text(text)
        
        if len(text.strip()) < 50:
            return "Teks terlalu pendek untuk dirangkum. Minimal 50 karakter diperlukan."
        
        # Tokenisasi menjadi kalimat
        sentences = indonesian_sent_tokenize(text)
        
        if len(sentences) < 2:
            return "Teks harus memiliki minimal 2 kalimat untuk dapat dirangkum."
        
        # Atur max_sentences default
        if max_sentences is None:
            max_sentences = max(min_sentences, len(sentences) // 3)
        
        # Ekstrak fitur dan buat prediksi
        features = extract_indonesian_features(sentences)
        predictions = clf_indonesian.predict(features)
        tfidf_scores = calculate_tfidf_scores(sentences)
        
        # Pilih kalimat penting
        selected_sentences = []
        sentence_scores = []
        
        for i, (sent, pred, tfidf_score) in enumerate(zip(sentences, predictions, tfidf_scores)):
            if pred == 1:  # Kalimat penting
                position_bonus = 0.3 if i == 0 or i == len(sentences) - 1 else 0
                combined_score = tfidf_score + position_bonus
                sentence_scores.append((sent, combined_score, i))
        
        # Cadangan jika tidak ada kalimat yang terpilih
        if not sentence_scores:
            for i, (sent, tfidf_score) in enumerate(zip(sentences, tfidf_scores)):
                position_bonus = 0.3 if i == 0 or i == len(sentences) - 1 else 0
                combined_score = tfidf_score + position_bonus
                sentence_scores.append((sent, combined_score, i))
        
        # Urutkan berdasarkan skor dan pilih kalimat teratas
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        selected_count = min(max_sentences, max(min_sentences, len(sentence_scores)))
        selected_with_index = sentence_scores[:selected_count]
        
        # Urutkan berdasarkan urutan asli
        selected_with_index.sort(key=lambda x: x[2])
        selected_sentences = [item[0] for item in selected_with_index]
        
        # Buat ringkasan
        summary = ' '.join(selected_sentences)
        summary = re.sub(r'\s+', ' ', summary).strip()
        
        if len(summary) < 20:
            return "Tidak dapat membuat ringkasan yang bermakna."
        
        return summary
    
    except Exception as e:
        return f"Terjadi kesalahan dalam pembuatan ringkasan: {str(e)}"

# ===== Fungsi utilitas tambahan =====
def get_text_statistics(text):
    """Dapatkan statistik dasar tentang teks"""
    sentences = indonesian_sent_tokenize(text)
    words = text.split()
    
    return {
        'character_count': len(text),
        'word_count': len(words),
        'sentence_count': len(sentences),
        'avg_words_per_sentence': len(words) / len(sentences) if sentences else 0
    }