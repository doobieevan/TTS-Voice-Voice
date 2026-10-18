from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_DIR = ROOT / "piper-master" / "src" / "python_run"
VENV = RUN_DIR / ".venv-voice"
PYTHON = VENV / "Scripts" / "python.exe"
VOICE_APP = RUN_DIR / "voice_to_voice.py"
REQS = RUN_DIR / "requirements_voice.txt"
ENV_FILE = ROOT / ".env.voice"
COMPOSE = ROOT / "docker-compose.yml"
DEFAULT_MODEL = "artifish/llama3.2-uncensored"
DEFAULT_CHAT_URL = "http://localhost:11434/v1/chat/completions"


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def save_env(values: dict[str, str]) -> None:
    lines = [
        "# TTS voice menu settings",
        f"LLM_PROVIDER={values.get('LLM_PROVIDER', 'ollama')}",
        f"CHAT_URL={values.get('CHAT_URL', DEFAULT_CHAT_URL)}",
        f"CHAT_MODEL={values.get('CHAT_MODEL', DEFAULT_MODEL)}",
        f"CHAT_API_KEY={values.get('CHAT_API_KEY', 'ollama')}",
        f"WHISPER_MODEL={values.get('WHISPER_MODEL', 'base')}",
        f"WHISPER_DEVICE={values.get('WHISPER_DEVICE', 'cpu')}",
        f"WHISPER_COMPUTE_TYPE={values.get('WHISPER_COMPUTE_TYPE', 'int8')}",
        f"INPUT_DEVICE={values.get('INPUT_DEVICE', '1')}",
        f"PIPER_MODEL={values.get('PIPER_MODEL', '')}",
        f"SAMPLE_RATE={values.get('SAMPLE_RATE', '16000')}",
        f"SILENCE_THRESHOLD={values.get('SILENCE_THRESHOLD', '0.015')}",
        f"SILENCE_SECONDS={values.get('SILENCE_SECONDS', '0.8')}",
        f"MAX_RECORD_SECONDS={values.get('MAX_RECORD_SECONDS', '20')}",
        f"SYSTEM_PROMPT={values.get('SYSTEM_PROMPT', 'You are a concise, helpful voice assistant.')}",
        "",
    ]
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    print("\n> " + " ".join(command))
    return subprocess.run(command, cwd=ROOT, text=True, check=check)


def ensure_setup() -> bool:
    if not PYTHON.exists():
        uv_python = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python311" / "python.exe"
        if not uv_python.exists():
            uv_python = Path.home() / ".local" / "share" / "uv" / "python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
        if not uv_python.exists():
            print("Install Python 3.11, then run this menu again.")
            return False
        print("Creating Python 3.11 voice environment...")
        run([str(uv_python), "-m", "venv", str(VENV)])
    run([str(PYTHON), "-m", "pip", "install", "-r", str(REQS)])
    return True


def docker_model_exists(model: str) -> bool:
    result = subprocess.run(
        ["docker", "exec", "tts-ollama", "ollama", "list"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return False
    names = {line.split()[0].removesuffix(":latest") for line in result.stdout.splitlines()[1:] if line.split()}
    return model.removesuffix(":latest") in names


def wait_for_ollama() -> None:
    for _ in range(30):
        result = subprocess.run(
            ["docker", "exec", "tts-ollama", "ollama", "list"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("Ollama did not become ready within 30 seconds")


def docker_up(values: dict[str, str]) -> None:
    run(["docker", "compose", "-f", str(COMPOSE), "up", "-d", "--pull", "always"])
    wait_for_ollama()
    model = values.get("CHAT_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    print(f"Checking Ollama model: {model}")
    if not docker_model_exists(model):
        print(f"Model is absent; pulling {model}...")
        run(["docker", "exec", "tts-ollama", "ollama", "pull", model])
    else:
        print(f"Model is ready: {model}")


def choose_model(values: dict[str, str]) -> None:
    current = values.get("CHAT_MODEL", DEFAULT_MODEL)
    print("\nLM options: 1) artifish/llama3.2-uncensored  2) llama3.2  3) llama3.1  4) qwen2.5  5) custom")
    choice = input(f"Select [{current}]: ").strip()
    models = {"1": DEFAULT_MODEL, "2": "llama3.2", "3": "llama3.1", "4": "qwen2.5"}
    if choice == "5":
        selected = input("Model name: ").strip()
        values["CHAT_MODEL"] = selected or current
    elif choice in models:
        values["CHAT_MODEL"] = models[choice]
    save_env(values)


def choose_provider(values: dict[str, str]) -> None:
    print("\nProvider: 1) Ollama Docker  2) OpenAI-compatible custom")
    choice = input("Select [1]: ").strip() or "1"
    if choice == "2":
        values["LLM_PROVIDER"] = "custom"
        values["CHAT_URL"] = input(f"Chat URL [{values['CHAT_URL']}]: ").strip() or values["CHAT_URL"]
        values["CHAT_MODEL"] = input(f"Model [{values['CHAT_MODEL']}]: ").strip() or values["CHAT_MODEL"]
        values["CHAT_API_KEY"] = input("API key [leave blank to keep current]: ").strip() or values["CHAT_API_KEY"]
    else:
        values.update(LLM_PROVIDER="ollama", CHAT_URL="http://localhost:11434/v1/chat/completions", CHAT_API_KEY="ollama")
    save_env(values)


def choose_audio(values: dict[str, str]) -> None:
    result = run([str(PYTHON), "-c", "import sounddevice as sd; print(sd.query_devices())"], check=False)
    print(result.stdout or "No audio devices returned.")
    device = input(f"Input device [{values.get('INPUT_DEVICE', '1')}]: ").strip()
    if device:
        values["INPUT_DEVICE"] = device
        save_env(values)


def start_voice(values: dict[str, str]) -> None:
    model = values.get("PIPER_MODEL", "").strip()
    if not model or not Path(model).exists():
        models = list(ROOT.rglob("*.onnx"))
        print("\nPiper models found:")
        for index, item in enumerate(models, 1):
            print(f"{index}) {item}")
        selected = input("Choose model number or enter a full .onnx path: ").strip()
        if selected.isdigit() and 0 < int(selected) <= len(models):
            model = str(models[int(selected) - 1])
        else:
            model = selected
        if not model or not Path(model).exists():
            print("A valid Piper .onnx model is required.")
            return
        values["PIPER_MODEL"] = model
        save_env(values)

    docker_up(values)
    command = [str(PYTHON), str(VOICE_APP), "--piper-model", model]
    mapping = {
        "WHISPER_MODEL": "--whisper-model", "WHISPER_DEVICE": "--whisper-device",
        "WHISPER_COMPUTE_TYPE": "--whisper-compute-type", "CHAT_URL": "--chat-url",
        "CHAT_MODEL": "--chat-model", "CHAT_API_KEY": "--api-key", "SYSTEM_PROMPT": "--system",
        "INPUT_DEVICE": "--input-device", "SAMPLE_RATE": "--sample-rate",
        "SILENCE_THRESHOLD": "--silence-threshold", "SILENCE_SECONDS": "--silence-seconds",
        "MAX_RECORD_SECONDS": "--max-record-seconds",
    }
    for key, flag in mapping.items():
        if values.get(key):
            command.extend([flag, values[key]])
    run(command, check=False)


def main() -> None:
    values = load_env()
    while True:
        print("\n=== TTS Voice-to-Voice Menu ===")
        print("1) Start voice assistant")
        print("2) Install/update dependencies")
        print("3) Start Docker Ollama and pull selected LM")
        print("4) Select LM model")
        print("5) Select LLM provider")
        print("6) List/select microphone")
        print("7) Show settings")
        print("8) Exit")
        choice = input("Choose [1]: ").strip() or "1"
        if choice == "1": start_voice(values)
        elif choice == "2": ensure_setup()
        elif choice == "3": docker_up(values)
        elif choice == "4": choose_model(values); values = load_env()
        elif choice == "5": choose_provider(values); values = load_env()
        elif choice == "6": choose_audio(values); values = load_env()
        elif choice == "7": print("\n" + "\n".join(f"{k}={v}" for k, v in values.items()))
        elif choice == "8": break
        else: print("Unknown option.")


if __name__ == "__main__":
    main()
