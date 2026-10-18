from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_DIR = ROOT / "piper-master" / "src" / "python_run"
# Import the installed Windows piper-tts wheel, not the repository's legacy
# piper package, which requires Linux-only piper_phonemize.
from piper import PiperVoice  # noqa: E402
from piper.config import SynthesisConfig  # noqa: E402

# Load shared microphone and chat helpers without allowing their directory to
# shadow the installed Piper package.
VOICE_HELPERS = RUN_DIR / "voice_to_voice.py"
import numpy as np  # noqa: E402
import sounddevice as sd  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402
import importlib.util  # noqa: E402

helper_spec = importlib.util.spec_from_file_location("voice_helpers", VOICE_HELPERS)
if helper_spec is None or helper_spec.loader is None:
    raise RuntimeError(f"Cannot load voice helpers from {VOICE_HELPERS}")
voice_helpers = importlib.util.module_from_spec(helper_spec)
helper_spec.loader.exec_module(voice_helpers)
chat_completion = voice_helpers.chat_completion
record_until_silence = voice_helpers.record_until_silence
resolve_input_device = voice_helpers.resolve_input_device


def speak(voice: PiperVoice, text: str, speed: float, noise: float, volume: float) -> None:
    config = SynthesisConfig(length_scale=1.0 / speed, noise_scale=noise, volume=volume)
    raw = b"".join(chunk.audio_int16_bytes for chunk in voice.synthesize(text, syn_config=config))
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    sd.play(audio, voice.config.sample_rate)
    sd.wait()


def main() -> None:
    model_path = Path(os.environ["PIPER_MODEL"]).resolve()
    if not model_path.is_file():
        raise FileNotFoundError(f"Piper model not found: {model_path}")
    config_path = model_path.with_suffix(".onnx.json")
    if not config_path.is_file():
        raise FileNotFoundError(f"Piper config not found beside model: {config_path}")
    input_device = resolve_input_device(os.getenv("INPUT_DEVICE", "1"))
    sample_rate = int(os.getenv("SAMPLE_RATE", "16000"))
    threshold = float(os.getenv("SILENCE_THRESHOLD", "0.00005"))
    silence_seconds = float(os.getenv("SILENCE_SECONDS", "0.9"))
    max_seconds = float(os.getenv("MAX_RECORD_SECONDS", "20"))
    speed = float(os.getenv("VOICE_SPEED", "1.12"))
    noise = float(os.getenv("VOICE_NOISE", "0.8"))
    volume = float(os.getenv("VOICE_VOLUME", "1.0"))
    chat_url = os.getenv("CHAT_URL", "http://localhost:11434/v1/chat/completions")
    chat_model = os.getenv("CHAT_MODEL", "artifish/llama3.2-uncensored")
    api_key = os.getenv("CHAT_API_KEY", "ollama")
    persona_mode = os.getenv("PERSONA_MODE", "sassy").lower()
    default_prompt = os.getenv("SASSY_SYSTEM_PROMPT", "You are a sassy, sarcastic voice assistant with fast, clever comebacks. Be playful and blunt, never hateful, threatening, or abusive. Keep replies short enough to speak naturally. Answer the question first, then add a witty line when it fits.")
    if persona_mode == "edgy":
        default_prompt = os.getenv("EDGY_SYSTEM_PROMPT", default_prompt)

    print("Loading sassy voice system...", flush=True)
    stt = WhisperModel(os.getenv("WHISPER_MODEL", "base"), device=os.getenv("WHISPER_DEVICE", "cpu"), compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"))
    voice = PiperVoice.load(model_path)
    messages = [{"role": "system", "content": default_prompt}]
    print(f"Mode: {persona_mode}", flush=True)

    try:
        while True:
            input("\nPress Enter, then speak: ")
            audio = record_until_silence(sample_rate, threshold, silence_seconds, max_seconds, input_device=input_device)
            if audio.size == 0:
                continue
            print("Transcribing...", flush=True)
            segments, _ = stt.transcribe(audio, vad_filter=True)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            if not text:
                print("I heard absolutely nothing. The microphone remains suspicious.")
                continue
            print(f"You: {text}")
            messages.append({"role": "user", "content": text})
            print("Thinking of a comeback...", flush=True)
            reply = chat_completion(chat_url, chat_model, api_key, messages)
            messages.append({"role": "assistant", "content": reply})
            print(f"Sassy assistant: {reply}")
            speak(voice, reply, speed, noise, volume)
    except KeyboardInterrupt:
        print("\nSassy mode stopped.")


if __name__ == "__main__":
    main()
