import sounddevice as sd
import numpy as np

def print_sound_level(indata, frames, time, status):
    if status:
        print("Status:", status)
    volume_norm = np.linalg.norm(indata)*10
    print(f"Volume: {volume_norm:.2f}")

print("Opening stream...")
try:
    with sd.InputStream(channels=1, samplerate=16000, callback=print_sound_level, blocksize=1280):
        print("Stream opened. Sleeping...")
        sd.sleep(3000)
except Exception as e:
    print(f"Error: {e}")
print("Done.")
