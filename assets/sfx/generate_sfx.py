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


def generate_pop_snap(output_path: Path):
    """Crisp modern tactile pop/snap for 2s Pattern Interrupt hooks & card transitions."""
    duration = 0.09
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = 920.0 * np.exp(-32.0 * t) + 180.0
    env = np.exp(-42.0 * t) * np.minimum(1.0, t / 0.004)
    sig = (np.sin(2 * np.pi * freq * t) * 0.75 + np.sin(2 * np.pi * freq * 2.1 * t) * 0.25) * env
    int_audio = np.int16(sig / (np.max(np.abs(sig)) + 1e-6) * 32767 * 0.65)
    wavfile.write(str(output_path), SAMPLE_RATE, int_audio)


def generate_alert_ping(output_path: Path):
    """Subtle clean incident radar double-ping for disruptions & error beats."""
    duration = 0.28
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    p1 = np.sin(2 * np.pi * 880.0 * t) * np.exp(-26.0 * t) * np.minimum(1.0, t / 0.008)
    t2 = np.maximum(0.0, t - 0.11)
    gate2 = (t >= 0.11).astype(np.float32)
    p2 = gate2 * np.sin(2 * np.pi * 660.0 * t2) * np.exp(-22.0 * t2) * np.minimum(1.0, t2 / 0.008)
    sig = p1 * 0.65 + p2 * 0.55
    int_audio = np.int16(sig / (np.max(np.abs(sig)) + 1e-6) * 32767 * 0.55)
    wavfile.write(str(output_path), SAMPLE_RATE, int_audio)


def generate_key_tick(output_path: Path):
    """Clean short mechanical keyboard tap cluster for IDE/code reveal moments."""
    duration = 0.24
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    sig = np.zeros_like(t, dtype=np.float32)
    for offset in (0.01, 0.08, 0.15):
        idx = int(offset * SAMPLE_RATE)
        k_len = int(0.03 * SAMPLE_RATE)
        if idx + k_len < len(sig):
            kt = np.linspace(0, 0.03, k_len, endpoint=False)
            click = np.sin(2 * np.pi * 1650.0 * kt) * np.exp(-130.0 * kt)
            click += np.random.uniform(-0.18, 0.18, k_len) * np.exp(-150.0 * kt)
            sig[idx:idx + k_len] += click
    int_audio = np.int16(sig / (np.max(np.abs(sig)) + 1e-6) * 32767 * 0.45)
    wavfile.write(str(output_path), SAMPLE_RATE, int_audio)


def generate_success_chime(output_path: Path):
    """Warm ascending dual-harmonic resolution chime for verified cutovers/fixes."""
    duration = 0.34
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    e1 = np.exp(-10.0 * t) * np.minimum(1.0, t / 0.012)
    c1 = np.sin(2 * np.pi * 523.25 * t) * e1 * 0.5
    t2 = np.maximum(0.0, t - 0.07)
    g2 = (t >= 0.07).astype(np.float32)
    c2 = g2 * np.sin(2 * np.pi * 783.99 * t2) * np.exp(-9.0 * t2) * np.minimum(1.0, t2 / 0.012) * 0.6
    sig = c1 + c2
    int_audio = np.int16(sig / (np.max(np.abs(sig)) + 1e-6) * 32767 * 0.50)
    wavfile.write(str(output_path), SAMPLE_RATE, int_audio)


def generate_dark_cyber_suspense(output_path: Path, duration_sec: float = 70.0):
    """Deep eerie minor sub-bass drone + filtered tension pulse for 3AM War Stories."""
    total_samples = int(SAMPLE_RATE * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)
    drone = (
        np.sin(2 * np.pi * 55.0 * t) * 0.42
        + np.sin(2 * np.pi * 82.41 * t) * 0.25
        + np.sin(2 * np.pi * 116.54 * t + 0.4 * np.sin(2 * np.pi * 0.22 * t)) * 0.16
    )
    beat_sec = 0.60
    pulse = np.zeros_like(t, dtype=np.float32)
    for bi in range(int(duration_sec / beat_sec)):
        b_s = int(bi * beat_sec * SAMPLE_RATE)
        k_len = int(0.14 * SAMPLE_RATE)
        if b_s + k_len < total_samples:
            kt = np.linspace(0, 0.14, k_len, endpoint=False)
            amp = 0.34 if bi % 2 == 0 else 0.14
            pulse[b_s:b_s + k_len] += np.sin(2 * np.pi * 68.0 * np.exp(-16.0 * kt) * kt) * np.exp(-18.0 * kt) * amp
    sig = (drone + pulse) * np.minimum(1.0, t / 0.6)
    sig = sig / (np.max(np.abs(sig)) + 1e-6) * 0.32
    wavfile.write(str(output_path), SAMPLE_RATE, np.int16(sig * 32767))
    print("Generated Dark Cyber Suspense BGM:", output_path)


def generate_upbeat_electro_pulse(output_path: Path, duration_sec: float = 70.0):
    """Energetic 118 BPM tech synth pulse + plucks for Myth-Buster & Cage Match reels."""
    total_samples = int(SAMPLE_RATE * duration_sec)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)
    bpm = 118.0
    step_sec = 60.0 / bpm / 2.0  # eighth notes
    arp_freqs = [130.81, 155.56, 196.00, 233.08, 261.63, 233.08, 196.00, 155.56]
    sig = np.sin(2 * np.pi * 65.41 * t) * 0.18
    for si in range(int(duration_sec / step_sec)):
        idx = int(si * step_sec * SAMPLE_RATE)
        s_len = int(min(step_sec * 0.9, 0.20) * SAMPLE_RATE)
        if idx + s_len < total_samples:
            st_t = np.linspace(0, s_len / SAMPLE_RATE, s_len, endpoint=False)
            f0 = arp_freqs[si % len(arp_freqs)]
            pluck = (np.sin(2 * np.pi * f0 * st_t) * 0.6 + np.sin(2 * np.pi * f0 * 2.0 * st_t) * 0.2) * np.exp(-15.0 * st_t)
            sig[idx:idx + s_len] += pluck * 0.32
        if si % 2 == 0:
            k_len = int(0.09 * SAMPLE_RATE)
            if idx + k_len < total_samples:
                kt = np.linspace(0, 0.09, k_len, endpoint=False)
                sig[idx:idx + k_len] += np.sin(2 * np.pi * (95.0 * np.exp(-32.0 * kt) + 42.0) * kt) * np.exp(-26.0 * kt) * 0.28
    sig = sig / (np.max(np.abs(sig)) + 1e-6) * 0.30
    wavfile.write(str(output_path), SAMPLE_RATE, np.int16(sig * 32767))
    print("Generated Upbeat Electro Pulse BGM:", output_path)


if __name__ == "__main__":
    out_dir = Path(r"c:\Users\Mangesh\.gemini\antigravity\scratch\nanopro-reel-maker\assets\sfx")
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_whoosh(out_dir / "whoosh.wav")
    generate_pop_snap(out_dir / "pop_snap.wav")
    generate_alert_ping(out_dir / "alert_ping.wav")
    generate_key_tick(out_dir / "key_tick.wav")
    generate_success_chime(out_dir / "success_chime.wav")
    generate_lofi_tech_bgm(out_dir / "lofi_cyber_bgm.wav", duration_sec=70.0)
    generate_dark_cyber_suspense(out_dir / "dark_cyber_suspense.wav", duration_sec=70.0)
    generate_upbeat_electro_pulse(out_dir / "upbeat_electro_pulse.wav", duration_sec=70.0)
