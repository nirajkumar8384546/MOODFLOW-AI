# train_text_model.py
import pandas as pd
import pickle
import os
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

print("🚀 Training Text Emotion Model...")

# ===========================
# 🔥 Ensure NLTK stopwords
# ===========================
nltk.download('stopwords')

# English stopwords
english_stopwords = set(stopwords.words('english'))

# Hindi stopwords (manually added basic list)
hindi_stopwords = {
    'में', 'का', 'की', 'के', 'है', 'हैं', 'और', 'से', 'को', 'पर', 'यह', 'कि', 'मैं', 'तुम', 'हो',
    'वह', 'हम', 'यहाँ', 'थे', 'था', 'थे', 'हूँ', 'रही', 'हुआ', 'कर', 'करना', 'करते', 'हुए',
    'भी', 'तक', 'जब', 'तो', 'लेकिन', 'या', 'क्या', 'क्यों', 'का', 'की', 'के', 'में', 'है', 'हैं'
}

all_stopwords = english_stopwords.union(hindi_stopwords)

# ===========================
# 🔥 Load datasets
# ===========================
# English dataset
df_en = pd.read_csv("dataset/text/tweet_emotions.csv")
df_en = df_en[['content', 'sentiment']]

# Hindi dataset
df_hi = pd.read_csv("dataset/text/hindi_emotions.csv")  # Make sure this exists
df_hi = df_hi[['content', 'sentiment']]

# Combine datasets
df = pd.concat([df_en, df_hi], ignore_index=True)

# ===========================
# Features & Labels
# ===========================
X = df['content']
y = df['sentiment']

# ===========================
# Text vectorization
# ===========================
vectorizer = TfidfVectorizer(max_features=5000, stop_words=list(all_stopwords))  # ✅ FIXED
X_vec = vectorizer.fit_transform(X)

# ===========================
# Train model
# ===========================
model = LogisticRegression(max_iter=200)
model.fit(X_vec, y)

# ===========================
# Save model & vectorizer
# ===========================
os.makedirs("backend/models", exist_ok=True)

pickle.dump(model, open("backend/models/text_model.pkl", "wb"))
pickle.dump(vectorizer, open("backend/models/vectorizer.pkl", "wb"))

print("✅ Model trained & saved successfully!")