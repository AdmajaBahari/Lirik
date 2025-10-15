import math
import time
import numpy as np
from pydub import AudioSegment
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

console = Console()

# === Fungsi untuk membaca file lirik ===
def load_lyrics(filename):
    lyrics = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and line.startswith('[') and ']' in line:
                    time_part, text_part = line.split(']', 1)
                    time_str = time_part[1:]  # Remove the opening bracket [
                    text_cleaned = text_part.strip()  # Clean the text
                    
                    # Format LRC: [MM:SS.xx]
                    if '.' in time_str:
                        minutes, rest = time_str.split(':')
                        seconds, centiseconds = rest.split('.')
                        time_sec = float(minutes) * 60 + float(seconds) + float(centiseconds) / 100
                    else:
                        minutes, seconds = time_str.split(':')
                        time_sec = float(minutes) * 60 + float(seconds)
                    
                    # Only add if text is not empty
                    if text_cleaned:
                        lyrics.append((time_sec, text_cleaned))
                    
        print(f"Loaded {len(lyrics)} lyrics from {filename}")
        for time_sec, lyric in lyrics:
            print(f"  {time_sec:.1f}s: '{lyric}'")  # Tambah quotes untuk lihat spasi
            
    except FileNotFoundError:
        print(f"File {filename} tidak ditemukan")
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
    
    return sorted(lyrics, key=lambda x: x[0])

def get_lyric_at(t, lyrics):
    """Fungsi yang diperbaiki untuk handle waktu tidak berurutan"""
    current_lyric = ""
    for time_sec, lyric in lyrics:
        if t >= time_sec:
            current_lyric = lyric
        else:
            break
    return current_lyric

# === Efek ketik yang lebih smooth ===
class TypeWriter:
    def __init__(self, speed=0.05):
        self.speed = speed
        self.last_update = 0
        self.current_text = ""
        self.target_text = ""
    
    def update(self, target_text):
        current_time = time.time()
        
        # Jika teks target berubah, reset
        if target_text != self.target_text:
            self.target_text = target_text
            self.current_text = ""
            self.last_update = current_time
            return self.current_text
        
        # Jika sudah selesai, return teks lengkap
        if self.current_text == self.target_text:
            return self.current_text
        
        # Tambah karakter berdasarkan waktu
        if current_time - self.last_update > self.speed:
            chars_to_add = min(2, len(self.target_text) - len(self.current_text))
            if chars_to_add > 0:
                self.current_text += self.target_text[len(self.current_text):len(self.current_text) + chars_to_add]
                self.last_update = current_time
        
        return self.current_text

# === MAIN PROGRAM ===
def main():
    # === Baca lirik ===
    print("Memuat lirik...")
    main_lyrics = load_lyrics("main.lrc")
    support_lyrics = load_lyrics("support.lrc")
    
    # Debug: print semua lyrics yang loaded
    print("\n=== DEBUG LYRICS ===")
    print("Main lyrics:")
    for i, (time_sec, lyric) in enumerate(main_lyrics):
        print(f"  [{i}] {time_sec:.1f}s: '{lyric}'")
    
    print("Support lyrics:")
    for i, (time_sec, lyric) in enumerate(support_lyrics):
        print(f"  [{i}] {time_sec:.1f}s: '{lyric}'")
    
    # Jika tidak ada support lyrics, buat manual dari file yang Anda berikan
    if not support_lyrics:
        print("⚠️  Support lyrics kosong, menggunakan data manual...")
        support_lyrics = [
            (0.0, "She's runnin' out the door"),
            (10.0, "She's runnin' out"),
            (16.0, "She run, run, run, run"),
            (32.0, "Run...")
        ]
    
    print("===================\n")
    
    # Jika main.lrc tidak lengkap, buat manual
    if len(main_lyrics) < 8:
        print("⚠️  Main lyrics tidak lengkap, menggunakan data manual...")
        main_lyrics = [
            (0.0, "You know, you know where you are with"),
            (5.0, "You know where you are with"),
            (10.0, "Floor collapses, floating"),
            (15.0, "Bouncing back"),
            (20.0, "And one day, I am gonna grow wings"),
            (25.0, "A chemical reaction (you know where you are)"),
            (30.0, "Hysterical and useless (you know where you are)"),
            (35.0, "Hysterical and (you know where you are)")
        ]
    
    # Cari durasi maksimum
    max_duration = max(
        max([time for time, _ in main_lyrics]) if main_lyrics else 0,
        max([time for time, _ in support_lyrics]) if support_lyrics else 0
    )
    total_duration = max_duration + 5
    print(f"Durasi visualizer: {total_duration} detik")
    
    # === Buat data waveform (dummy) ===
    print("\nMempersiapkan visualizer...")
    samples = np.random.random(80) * 0.5
    
    # === Visualizer lirik ===
    print("\n=='Let Down' - Radiohead==\n")
    start = time.time()

    # Inisialisasi typewriter
    main_writer = TypeWriter(speed=0.03)
    support_writer = TypeWriter(speed=0.04)

    with Live(refresh_per_second=15, console=console, screen=True) as live:
        last_main = ""
        last_support = ""
        
        while True:
            t = time.time() - start
            if t > total_duration:
                break

            # Update waveform
            idx = int((t / total_duration) * len(samples)) % len(samples)
            bar_length = max(1, int(samples[idx] * 50))
            bar = "█" * bar_length
            waveform = Text(bar, style="bold magenta")

            current_main = get_lyric_at(t, main_lyrics)
            current_support = get_lyric_at(t, support_lyrics)

            # Update typewriter
            main_display = main_writer.update(current_main)
            support_display = support_writer.update(current_support)

            # Debug real-time - lebih detail
            if current_main != last_main:
                print(f"[{t:.1f}s] MAIN: '{current_main}'")
                last_main = current_main
            if current_support != last_support:
                print(f"[{t:.1f}s] SUPPORT: '{current_support}'")
                last_support = current_support

            # Tampilan dengan judul lagu di atas waveform
            content = Text.assemble(
                Text("🎵 Let Down x Creep - Radiohead", style="bold cyan"), "\n\n",  # Judul lagu
                waveform, "\n\n",
                Text(main_display, style="bold white"), "\n",
                Text(support_display, style="dim italic cyan"), "\n\n",
                Text(f"⏱️  {t:.1f}s / {total_duration:.1f}s", style="yellow"), "\n",
                Text("code by bahar", style="dim white")
            )
            
            panel = Panel(
                content,
                title="🎵 Let Down x Creep - Radiohead",
                border_style="blue",
                padding=(1, 2)
            )
            
            live.update(panel)
            
            time.sleep(0.07)

    print("\n🎵 Selesai!")
    print("@adbaharc")

if __name__ == "__main__":
    main()