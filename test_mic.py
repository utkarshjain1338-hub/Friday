import sounddevice as sd
import numpy as np

def print_sound_level(indata, frames, time, status):
    volume_norm = np.linalg.norm(indata)*10
    print(f"Volume: {volume_norm:.2f}")

try:
    with sd.InputStream(callback=print_sound_level):
        sd.sleep(3000)
except Exception as e:
    print(f"Error: {e}")
