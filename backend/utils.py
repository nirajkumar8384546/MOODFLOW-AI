import cv2, numpy as np, subprocess, librosa, os

FRAME_SIZE=(48,48)
AUDIO_DIM=40

def extract_audio(video):
    wav="temp.wav"
    subprocess.run(["ffmpeg","-y","-i",video,"-ac","1","-ar","22050",wav],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav

def audio_feat(wav):
    try:
        y,sr=librosa.load(wav,sr=22050)
        mfcc=librosa.feature.mfcc(y=y,sr=sr,n_mfcc=AUDIO_DIM)
        return np.mean(mfcc.T,axis=0)
    except:
        return np.zeros(AUDIO_DIM)

def frame_feat(video):
    cap=cv2.VideoCapture(video)
    feats=[]
    while True:
        ret,f=cap.read()
        if not ret: break
        g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
        g=cv2.resize(g,FRAME_SIZE)/255.0
        feats.append(g.flatten())
    cap.release()
    return np.mean(feats,axis=0)

def process(video):
    wav=extract_audio(video)
    feat=np.concatenate([frame_feat(video), audio_feat(wav)])
    os.remove(wav)
    return feat