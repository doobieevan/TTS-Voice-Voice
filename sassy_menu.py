from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env.sassy"
PYTHON = ROOT / "piper-master" / "src" / "python_run" / ".venv-voice" / "Scripts" / "python.exe"
APP = ROOT / "sassy_voice.py"
COMPOSE = ROOT / "docker-compose.yml"


def load() -> dict[str, str]:
    values = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def save(values: dict[str, str]) -> None:
    ENV_FILE.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n", encoding="utf-8")


def available_voices() -> list[Path]:
    """Return only Piper models with a sibling JSON config."""
    return sorted(
        model for model in ROOT.rglob("*.onnx")
        if ".venv" not in model.parts and model.with_suffix(".onnx.json").is_file()
    )


def choose_voice(values: dict[str, str]) -> None:
    models = available_voices()
    print("\nAvailable Piper models:")
    for index, model in enumerate(models, 1):
        print(f"{index}) {model}")
    choice = input(f"Voice [{values['PIPER_MODEL']}]: ").strip()
    if choice.isdigit() and 0 < int(choice) <= len(models):
        values["PIPER_MODEL"] = str(models[int(choice) - 1])
        save(values)


def choose_mode(values: dict[str, str]) -> None:
    print("\n1) Sassy mode")
    print("2) Edgy fictional banter with profanity and sharper insults")
    print("Edgy mode blocks hate, credible threats, targeted abuse, and self-harm encouragement.")
    choice = input("Select [1]: ").strip() or "1"
    values["PERSONA_MODE"] = "edgy" if choice == "2" else "sassy"
    save(values)


def edit_prompt(values: dict[str, str]) -> None:
    key = "EDGY_SYSTEM_PROMPT" if values.get("PERSONA_MODE") == "edgy" else "SASSY_SYSTEM_PROMPT"
    print("\nCurrent prompt:\n" + values.get(key, ""))
    prompt = input("New prompt, or Enter to keep: ").strip()
    if prompt:
        values[key] = prompt
        save(values)


def settings(values: dict[str, str]) -> None:
    for key in ["PIPER_MODEL", "CHAT_MODEL", "INPUT_DEVICE", "VOICE_SPEED", "VOICE_NOISE", "VOICE_VOLUME", "SASSY_SYSTEM_PROMPT"]:
        print(f"{key}={values.get(key, '')}")


def main() -> None:
    values = load()
    while True:
        print("\n=== SASSY VOICE SYSTEM ===")
        print("1) Start sassy voice")
        print("2) Change Piper voice")
        print("3) Change personality mode")
        print("4) Change personality prompt")
        print("5) Adjust delivery")
        print("6) Show settings")
        print("7) Start Docker Ollama")
        print("8) Exit")
        choice = input("Choose [1]: ").strip() or "1"
        if choice == "1":
            subprocess.run(["docker", "compose", "-f", str(COMPOSE), "up", "-d"], cwd=ROOT, check=True)
            env = os.environ.copy()
            env.update(values)
            subprocess.run([str(PYTHON), str(APP)], cwd=ROOT, env=env, check=False)
        elif choice == "2": choose_voice(values); values = load()
        elif choice == "3": choose_mode(values); values = load()
        elif choice == "4": edit_prompt(values); values = load()
        elif choice == "5":
            for key in ["VOICE_SPEED", "VOICE_NOISE", "VOICE_VOLUME"]:
                current = values[key]
                value = input(f"{key} [{current}]: ").strip()
                if value: values[key] = value
            save(values)
        elif choice == "6": settings(values)
        elif choice == "7": subprocess.run(["docker", "compose", "-f", str(COMPOSE), "up", "-d"], cwd=ROOT, check=True)
        elif choice == "8": return
        else: print("That option is not on the menu. Try again.")


if __name__ == "__main__":
    main()
