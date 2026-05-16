import sounddevice as sd
import numpy as np
import scipy.signal

def print_sound_level(indata, frames, time, status):
    print("Shape:", indata.shape)
    volume_norm = np.linalg.norm(indata[:, 0])*10
    print(f"Volume: {volume_norm:.2f}")

try:
    with sd.InputStream(callback=print_sound_level):
        sd.sleep(1000)
except Exception as e:
    print(f"Error: {e}")
