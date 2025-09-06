import subprocess
from pathlib import Path

# === Настройки ===
MUSIC_DIR = Path("music")          # папка с песнями
GLUE_FILE = Path("glue/intro.mp3") # интро/джингл
OUT_DIR = Path("gotovo")              # куда класть результат

INTRO_DURATION = 5     # сек — сколько секунд интро звучит в начале
FADE_DURATION = 2      # сек — затухание интро в конце
INTRO_VOLUME = 1.5     # громкость интро (0.0..1.0..), 0.5 = в два раза тише основной

# Кодек/контейнер (ниже логика под MP3; при желании можно ветвить по расширению)
AUDIO_CODEC = ["-c:a", "libmp3lame", "-q:a", "2"]  # q=2 ≈ 190–220 kbps VBR
META_FLAGS  = ["-map_metadata", "0", "-id3v2_version", "3"]  # сохранить теги из 1-го входа (основной песни)

def process_track(track: Path):
    OUT_DIR.mkdir(exist_ok=True)
    out_file = OUT_DIR / track.with_suffix(".mp3").name  # делаем mp3-выход

    # filter_complex:
    # [1:a] atrim=0:N, asetpts=PTS-STARTPTS, volume=INTRO_VOLUME, afade(out) -> [a1]
    # [0:a][a1] amix (длина = длина основного) -> mix
    fcomplex = (
        f"[1:a]atrim=0:{INTRO_DURATION},asetpts=PTS-STARTPTS,"
        f"volume={INTRO_VOLUME},"
        f"afade=t=out:st={INTRO_DURATION-FADE_DURATION}:d={FADE_DURATION}[a1];"
        f"[0:a][a1]amix=inputs=2:duration=first:dropout_transition=2[m]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(track),         # 0: основной трек
        "-i", str(GLUE_FILE),     # 1: интро
        "-filter_complex", fcomplex,
        "-map", "[m]",            # мапим микс
        *AUDIO_CODEC,
        *META_FLAGS,
        str(out_file),
    ]
    subprocess.run(cmd, check=True)
    return out_file

def main():
    if not MUSIC_DIR.exists():
        print("❌ Папка 'music' не найдена.")
        return
    if not GLUE_FILE.exists():
        print("❌ Файл интро не найден:", GLUE_FILE)
        return

    # Обрабатываем только аудио (можно расширить список масок при желании)
    files = [p for p in MUSIC_DIR.iterdir() if p.is_file() and p.suffix.lower() in {".mp3"}]
    if not files:
        print("⚠️ В 'music' нет mp3-файлов.")
        return

    print(f"Найдено треков: {len(files)}")
    for track in files:
        try:
            outp = process_track(track)
            print(f"✔ {track.name} → {outp.name}")
        except subprocess.CalledProcessError as e:
            print(f"⚠ Ошибка в '{track.name}': {e}")

    print("\n✅ Готово. Интро наложено на первые "
          f"{INTRO_DURATION} c (fade {FADE_DURATION} c), громкость интро = {INTRO_VOLUME}. "
          "Метаданные/название сохранены.")

if __name__ == "__main__":
    main()
