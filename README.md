TTS Voice-to-Voice System
==========================

This folder contains a local voice assistant that:

1. Listens through your microphone.
2. Converts speech to text with Whisper.
3. Sends the text to an Ollama language model.
4. Converts the answer to speech with Piper.
5. Plays the response through your speakers.

The default chat model is:

artifish/llama3.2-uncensored

Quick Start
-----------

1. Make sure Docker Desktop is running.
2. Open PowerShell in this folder.
3. Run:

   voice_menu.bat

4. Choose option 2 to install or update dependencies.
5. Choose option 1 to start the regular voice assistant.
6. Press Enter, speak, and stop speaking when finished.

The first Whisper model load can take some time.

Regular Voice Menu
------------------

voice_menu.bat starts the main menu. It can:

- Start the voice assistant.
- Start Docker Ollama.
- Pull the selected Ollama model if it is missing.
- Select a different language model.
- Select a microphone.
- Display current settings.

Sassy Voice System
------------------

Run:

   sassy_voice.bat

This starts a separate voice assistant with sarcastic, sassy, and quick-comeback behavior.

Its menu allows you to:

- Start sassy voice mode.
- Select a Piper voice.
- Switch between Sassy and Edgy modes.
- Change the personality prompt.
- Adjust voice speed, noise, and volume.
- Start Docker Ollama.

Edgy mode supports fictional rude banter and profanity. It does not enable hate, credible real-world threats, targeted abuse, or self-harm encouragement.

Settings
--------

Regular assistant settings are stored in:

   .env.voice

Sassy assistant settings are stored in:

   .env.sassy

Important settings include:

- CHAT_MODEL: Ollama model name.
- INPUT_DEVICE: Microphone device number or name.
- PIPER_MODEL: Piper .onnx voice model.
- SILENCE_THRESHOLD: Microphone speech detection level.
- VOICE_SPEED: Sassy voice playback speed.

Microphone Troubleshooting
--------------------------

If the assistant does not detect speech:

1. Check Windows microphone permissions.
2. Confirm the microphone input meter moves.
3. Use menu option 6 in voice_menu.bat to list devices.
4. Change INPUT_DEVICE in the appropriate environment file.
5. Try a lower SILENCE_THRESHOLD value, such as:

   SILENCE_THRESHOLD=0.00005

Docker and Ollama
-----------------

Docker Compose starts Ollama automatically and stores models in a persistent Docker volume.

To check the Ollama model list manually:

   docker exec tts-ollama ollama list

To stop the Ollama container:

   docker compose down

Piper Voices
------------

Piper models require both files:

- voice.onnx
- voice.onnx.json

Use the voice menu to select a valid voice. The menu ignores dependency models without matching configuration files.

The included test voice is:

   piper-master/etc/test_voice.onnx

Security
--------

Do not place private API keys or passwords in files that will be shared. The local Ollama setup does not require an API key.
