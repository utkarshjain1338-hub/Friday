import sounddevice as sd
import numpy as np
import scipy.signal

def print_sound_level(indata, frames, time, status):
    # indata is shape (frames, channels)
    # resample to 16000
    target_frames = int(frames * 16000 / 44100)
    resampled = scipy.signal.resample(indata[:, 0], target_frames)
    volume_norm = np.linalg.norm(resampled)*10
    print(f"Volume: {volume_norm:.2f}")

try:
    with sd.InputStream(channels=1, samplerate=44100, callback=print_sound_level, blocksize=int(44100*0.08)): # ~1280 frames at 16k
        sd.sleep(3000)
except Exception as e:
    print(f"Error: {e}")
