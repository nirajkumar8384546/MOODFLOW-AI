# train_audio_model.py
import os
import numpy as np
import librosa
import pickle
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from tensorflow.keras import layers, models
from tensorflow.keras.utils import to_categorical

DATASET_PATH = "dataset/audio"

emotion_map = {
    "01": "neutral",
    "02": "calm",
    "03": "happy",
    "04": "sad",
    "05": "angry",
    "06": "fear",
    "07": "disgust",
    "08": "surprised"
}

def preprocess_audio(audio, sr):
    # normalize
    audio = librosa.util.normalize(audio)
    # trim silence
    audio, _ = librosa.effects.trim(audio, top_db=25)
    return audio

def extract_features(file_path):
    try:
        audio, sr = librosa.load(file_path, sr=None, mono=True)  # safer
        audio = preprocess_audio(audio, sr)
        # fixed length 3 sec
        max_len = 3 * sr
        if len(audio) > max_len:
            audio = audio[:max_len]
        else:
            audio = np.pad(audio, (0, max_len - len(audio)), mode='constant')
        # MFCC
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        return np.mean(mfcc.T, axis=0)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

# LOAD DATA
X, y = [], []
for actor in os.listdir(DATASET_PATH):
    actor_path = os.path.join(DATASET_PATH, actor)
    if os.path.isdir(actor_path):
        for file in os.listdir(actor_path):
            if file.endswith(".wav"):
                parts = file.split("-")
                if len(parts) < 3:
                    continue
                emotion_code = parts[2]
                if emotion_code in emotion_map:
                    emotion = emotion_map[emotion_code]
                    file_path = os.path.join(actor_path, file)
                    features = extract_features(file_path)
                    if features is not None:
                        X.append(features)
                        y.append(emotion)

X = np.array(X)
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)
y = to_categorical(y_encoded)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# MODEL
model = models.Sequential([
    layers.Dense(256, activation='relu', input_shape=(40,)),
    layers.Dropout(0.3),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(64, activation='relu'),
    layers.Dense(y.shape[1], activation='softmax')
])

model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

print("🚀 Training...")
model.fit(X_train, y_train, epochs=30, batch_size=32, validation_data=(X_test, y_test))

loss, acc = model.evaluate(X_test, y_test)
print("✅ Accuracy:", acc)

# Save
os.makedirs("backend/models", exist_ok=True)
model.save("backend/models/audio_model.h5")
with open("backend/models/audio_label_encoder.pkl", "wb") as f:
    pickle.dump(encoder, f)

print("🎉 Audio model saved successfully!")