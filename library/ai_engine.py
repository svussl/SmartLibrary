import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Book

class SmartLibraryAI:
    """
    محرك الذكاء الاصطناعي (نسخة الأداء العالي - High Performance).
    يستخدم نموذج Transformer مقطر (Distilled) لضمان السرعة والدقة.
    النموذج: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    """

    def __init__(self):
        print("Loading Optimized AI Model (MiniLM)...")
        try:
            # تحميل النموذج الخفيف باستخدام المسار الكامل الصحيح على Hugging Face
            # هذا يمنع أي خطأ في التعرف على النموذج
            self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None

    def _prepare_data(self):
        """تجهيز بيانات الكتب للنظام"""
        books = Book.objects.all()
        if not books.exists():
            return None, None
        
        data = []
        for b in books:
            # دمج النصوص لبناء السياق
            content = f"{b.title} {b.description} {b.tags}"
            data.append({
                'id': b.id,
                'title': b.title,
                'content': content
            })
        
        df = pd.DataFrame(data)
        return df, df['content'].tolist()

    def get_recommendations(self, book_title):
        """نظام التوصية الذكي"""
        if self.model is None:
            return []

        df, sentences = self._prepare_data()
        if df is None or df.empty:
            return []

        try:
            # 1. تحويل النصوص لمتجهات
            embeddings = self.model.encode(sentences)
            
            # 2. البحث عن الكتاب الحالي
            if book_title not in df['title'].values:
                return []
            
            idx = df[df['title'] == book_title].index[0]
            target_embedding = embeddings[idx].reshape(1, -1)
            
            # 3. حساب التشابه
            sim_scores = cosine_similarity(target_embedding, embeddings)[0]
            
            # 4. الترتيب واختيار الأفضل
            indexed_scores = list(enumerate(sim_scores))
            sorted_scores = sorted(indexed_scores, key=lambda x: x[1], reverse=True)
            
            # أفضل 4 كتب (باستثناء الكتاب نفسه)
            top_indices = [i[0] for i in sorted_scores[1:5]]
            
            return df['title'].iloc[top_indices].tolist()
            
        except Exception as e:
            print(f"AI Error: {e}")
            return []

    def semantic_search(self, query):
        """البحث الدلالي (Semantic Search)"""
        if self.model is None:
            return []

        df, sentences = self._prepare_data()
        if df is None or df.empty:
            return []

        try:
            # 1. تحويل نصوص الكتب
            book_embeddings = self.model.encode(sentences)
            
            # 2. تحويل نص البحث
            query_embedding = self.model.encode([query])
            
            # 3. حساب التشابه
            scores = cosine_similarity(query_embedding, book_embeddings)[0]
            
            # 4. تصفية النتائج
            df['score'] = scores
            
            # عرض النتائج التي لها صلة مقبولة (أكبر من 0.1)
            results = df[df['score'] > 0.1].sort_values(by='score', ascending=False)
            
            return results[['id', 'title', 'score']].to_dict('records')

        except Exception as e:
            print(f"Search Error: {e}")
            return []