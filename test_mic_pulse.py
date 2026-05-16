import sounddevice as sd
import numpy as np

def print_sound_level(indata, frames, time, status):
    vols = np.linalg.norm(indata, axis=0)
    active = np.where(vols > 0)[0]
    if len(active) > 0:
        print(f"Active channels: {active}, Volumes: {vols[active]}")
    else:
        print("0")

try:
    with sd.InputStream(device="pulse"):
        sd.sleep(1000)
except Exception as e:
    print(f"Error: {e}")
