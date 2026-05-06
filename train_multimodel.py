# train_multimodel.py
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.services.video_audio_fusion import process_video 
import cv2, numpy as np, subprocess, librosa, tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


DATASET = "dataset/videos"
FRAME_SIZE = (48,48)
AUDIO_DIM = 40

emotion_map = {
    "01":"Neutral","02":"Calm","03":"Happy","04":"Sad",
    "05":"Angry","06":"Fearful","07":"Disgust","08":"Surprise"
}

def extract_audio(video):
    wav = "temp.wav"
    subprocess.run(["ffmpeg","-y","-i",video,"-ac","1","-ar","22050",wav],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav

def audio_feat(wav):
    try:
        y,sr = librosa.load(wav, sr=22050)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=AUDIO_DIM)
        return np.mean(mfcc.T, axis=0)
    except:
        return np.zeros(AUDIO_DIM)

def frame_feat(video):
    cap = cv2.VideoCapture(video)
    feats=[]
    while True:
        ret,f = cap.read()
        if not ret: break
        g=cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        g=cv2.resize(g, FRAME_SIZE)/255.0
        feats.append(g.flatten())
    cap.release()
    return np.mean(feats, axis=0)

X, y = [], []

for label in os.listdir(DATASET):
    label_path = os.path.join(DATASET, label)

    if not os.path.isdir(label_path):
        continue

    for file in os.listdir(label_path):
        if file.lower().endswith(".mp4"):
            video_path = os.path.join(label_path, file)

            print("Processing:", video_path)

            feat = process_video(video_path)

            if feat is not None:
                X.append(feat)
                y.append(label)

print("TOTAL SAMPLES:", len(X))

# 🔥 CRITICAL FIX
if len(X) == 0:
    print("❌ ERROR: No data loaded")
    exit()

X=np.array(X)
le=LabelEncoder()
y=tf.keras.utils.to_categorical(le.fit_transform(y))

Xtr,Xval,ytr,yval=train_test_split(X,y,test_size=0.2)

model=tf.keras.Sequential([
    tf.keras.layers.Dense(512,activation='relu',input_shape=(X.shape[1],)),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(256,activation='relu'),
    tf.keras.layers.Dense(len(le.classes_),activation='softmax')
])

model.compile(optimizer='adam',loss='categorical_crossentropy',metrics=['accuracy'])
model.fit(Xtr,ytr,validation_data=(Xval,yval),epochs=25)

os.makedirs("backend/model",exist_ok=True)
model.save("backend/model/emotion_multimodel.h5")
np.save("backend/model/labels.npy", le.classes_)

print("✅multimodal Training Done")