#!/usr/bin/env python3
"""
QwenTTS Test Client

Отправляет запрос на синтез речи на работающий QwenTTS-адаптер
и сохраняет WAV-файл.

Использование:

    # Один раз запустить сервер:
    cd QwenTTS
    .venv/Scripts/python qwentts_adapter_server.py

    # В другом терминале отправить тест:
    python test_qwen.py -t "Привет, Скайрим!"
    python test_qwen.py -t "Куда направишься?" -s femalecoward -l ru -o test.wav
    python test_qwen.py -t "Akatosh bless you" -l english -o eng_test.wav
"""

import argparse
import io
import json
import wave
from pathlib import Path
from urllib.request import Request, urlopen


def send_tts(
    text: str,
    speaker: str = "default",
    language: str = "ru",
    server_url: str = "http://127.0.0.1:7861",
) -> bytes:
    """Send a TTS request to the QwenTTS adapter and return raw WAV bytes."""
    payload = json.dumps({
        "text": text,
        "speaker_wav": speaker,
        "language": language,
    }).encode("utf-8")

    req = Request(
        url=f"{server_url.rstrip('/')}/tts_to_audio/",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(req, timeout=300) as resp:
        return resp.read()


def play_wav(wav_bytes: bytes) -> None:
    """Play WAV using Windows built-in Sound Player (fallback: print path)."""
    import tempfile, subprocess
    tmp = Path(tempfile.gettempdir()) / "qwentts_test_output.wav"
    tmp.write_bytes(wav_bytes)
    try:
        subprocess.Popen(["start", "", str(tmp)], shell=True)
        print(f"  Playing: {tmp}")
    except Exception:
        print(f"  Saved to: {tmp}")


def wav_info(wav_bytes: bytes) -> None:
    """Print WAV duration and format info."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as w:
        channels = w.getnchannels()
        width = w.getsampwidth()
        rate = w.getframerate()
        frames = w.getnframes()
        dur = frames / rate if rate > 0 else 0
        print(f"  WAV: {channels}ch, {width*8}bit, {rate}Hz, {dur:.2f}s, {len(wav_bytes)//1024}KB")


def main():
    parser = argparse.ArgumentParser(
        description="Отправить тестовый TTS-запрос на QwenTTS-адаптер",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  test_qwen.py -t "Привет, Скайрим!"
  test_qwen.py -t "Куда направишься?" -s femalecoward -l ru -o output.wav
  test_qwen.py -t "Hello, world" -l english -o hello.wav
  test_qwen.py --url http://192.168.1.100:7861 -t "Тест по сети"
        """,
    )
    parser.add_argument("-t", "--text", default="Привет, Скайрим! Проверка связи.", help="Текст для синтеза")
    parser.add_argument("-s", "--speaker", default="default", help="Имя спикера из voice_refs.json")
    parser.add_argument("-l", "--language", default="ru", help="Язык (ru, en, russian, english, ...)")
    parser.add_argument("-o", "--output", help="Сохранить WAV в файл (по умочанию открыть проигрыватель)")
    parser.add_argument("--url", default="http://127.0.0.1:7861", help="URL сервера (default: %(default)s)")
    parser.add_argument("--no-play", action="store_true", help="Не открыать проигрыватель")

    args = parser.parse_args()

    print(f"Сервер: {args.url}")
    print(f"Текст:  {args.text[:80]}...")
    print(f"Спикер: {args.speaker}")
    print(f"Язык:   {args.language}")
    print()
    print("Отправка запроса...", flush=True)

    try:
        wav_bytes = send_tts(args.text, args.speaker, args.language, args.url)
    except Exception as exc:
        print(f"ОШИБКА: {exc}")
        print()
        print("Возможные причины:")
        print("  1. Сервер не запущен — запусти Start_QwenTTS_Persistent.bat")
        print(f"  2. Неверный URL — проверь --url (сейчас: {args.url})")
        print("  3. Спикер не найден — спикер будет заменён на 'default'")
        return

    print(f"Получено {len(wav_bytes)} байт")
    wav_info(wav_bytes)

    if args.output:
        Path(args.output).write_bytes(wav_bytes)
        print(f"Сохранено: {args.output}")
    elif not args.no_play:
        play_wav(wav_bytes)
    else:
        tmp = Path("qwentts_test_output.wav")
        tmp.write_bytes(wav_bytes)
        print(f"Сохранено: {tmp}")

    print()
    print("Готово!")


if __name__ == "__main__":
    main()
