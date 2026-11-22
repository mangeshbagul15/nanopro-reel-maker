import math
import numpy as np
from pathlib import Path
from scipy.io import wavfile

SAMPLE_RATE = 44100

def generate_whoosh(output_path: Path):
    """Generates a crisp cinematic whoosh transition sound effect."""
    duration = 0.35
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    
    # White noise base
    noise = np.random.uniform(-1.0, 1.0, len(t))
    
    # Frequency sweep filter simulation (exponential frequency curve)
    freq = 200 + 3500 * (1.0 - np.cos(np.pi * (t / duration))) / 2.0
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    sweep = np.sin(phase) * 0.4 + noise * 0.6
    
    # Smooth bell envelope
    envelope = np.sin(np.pi * (t / duration)) ** 2
    audio = sweep * envelope * 0.6
    
    audio = np.int16(audio / np.max(np.abs(audio) + 1e-6) * 32767 * 0.7)
    wavfile.write(str(output_path), SAMPLE_RATE, audio)
    print("Generated Whoosh SFX:", output_path)

def generate_lofi_tech_bgm(output_path: Path, duration_sec: float = 65.0):
    """
    Generates a smooth, mellow cyber-tech lo-fi background track:
    - Warm Rhodes/Synth pad chords (Dm9 -> G13 -> Cmaj9 -> Am9)
    - Sub-bass groove (85 BPM)
    - Soft vinyl warmth
    """
    total_samples = int(SAMPLE_RATE * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)
    
    bpm = 85.0
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0  # ~2.82 seconds per bar
    
    # Chord frequencies (Hz)
    chords = [
        [146.83, 174.61, 220.00, 261.63, 329.63], # Dm9
        [196.00, 246.94, 293.66, 329.63, 392.00], # G13
        [130.81, 164.81, 196.00, 246.94, 293.66], # Cmaj9
        [110.00, 130.81, 164.81, 196.00, 246.94]  # Am9
    ]
    bass_notes = [73.42, 98.00, 65.41, 55.00]
    
    audio = np.zeros(total_samples, dtype=np.float32)
    
    # Generate Chord Pads
    for i, chord in enumerate(chords):
        chord_start_time = i * bar_sec
        while chord_start_time < duration_sec:
            c_len = min(bar_sec, duration_sec - chord_start_time)
            idx_start = int(chord_start_time * SAMPLE_RATE)
            idx_end = idx_start + int(c_len * SAMPLE_RATE)
            t_slice = t[idx_start:idx_end] - chord_start_time
            
            # Envelope with soft attack and decay
            env = np.ones_like(t_slice)
            attack_len = int(0.2 * SAMPLE_RATE)
            if len(env) > attack_len:
                env[:attack_len] = np.linspace(0, 1, attack_len)
                env[-attack_len:] = np.linspace(1, 0.4, attack_len)
                
            chord_signal = np.zeros_like(t_slice)
            for freq in chord:
                # Slight vibrato for warm lo-fi tape feel
                vibrato = np.sin(2 * np.pi * 4.5 * t_slice) * 0.004
                tone = np.sin(2 * np.pi * freq * (1.0 + vibrato) * t_slice)
                tone += 0.25 * np.sin(2 * np.pi * (freq * 2) * t_slice)
                chord_signal += tone
                
            chord_signal = chord_signal / len(chord) * env * 0.35
            audio[idx_start:idx_end] += chord_signal
            
            # Bass Note
            b_freq = bass_notes[i]
            bass_tone = np.sin(2 * np.pi * b_freq * t_slice) * env * 0.45
            bass_tone += 0.2 * np.sin(2 * np.pi * (b_freq * 2) * t_slice) * env
            audio[idx_start:idx_end] += bass_tone
            
            chord_start_time += 4 * bar_sec

    # Soft subtle beat pulse (kick on 1 & 3, snare pulse on 2 & 4)
    for beat_idx in range(int(duration_sec / beat_sec)):
        beat_time = beat_idx * beat_sec
        b_sample = int(beat_time * SAMPLE_RATE)
        
        # Soft kick on beats 0 & 2 of bar
        if beat_idx % 4 in [0, 2]:
            k_len = int(0.12 * SAMPLE_RATE)
            if b_sample + k_len < total_samples:
                kt = np.linspace(0, 0.12, k_len, endpoint=False)
                k_freq = 110.0 * np.exp(-35.0 * kt) + 40.0
                k_tone = np.sin(2 * np.pi * k_freq * kt) * np.exp(-25.0 * kt) * 0.25
                audio[b_sample:b_sample+k_len] += k_tone

    # Normalize to -16dB RMS for clean background balance
    max_val = np.max(np.abs(audio)) + 1e-6
    audio = audio / max_val * 0.30
    
    int_audio = np.int16(audio * 32767)
    wavfile.write(str(output_path), SAMPLE_RATE, int_audio)
    print("Generated Lo-Fi Cyber Tech BGM:", output_path)

if __name__ == "__main__":
    out_dir = Path(r"c:\Users\Mangesh\.gemini\antigravity\scratch\nanopro-reel-maker\assets\sfx")
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_whoosh(out_dir / "whoosh.wav")
    generate_lofi_tech_bgm(out_dir / "lofi_cyber_bgm.wav", duration_sec=70.0)
