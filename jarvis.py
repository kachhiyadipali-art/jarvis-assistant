#!/usr/bin/env python3
"""A small, allowlisted voice assistant that can launch apps and search Google."""

from __future__ import annotations

import platform
import re
import subprocess
import sys
import urllib.parse
import webbrowser

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


# Only these explicitly configured applications can be launched. No shell is used.
APP_COMMANDS = {
    "windows": {
        "calculator": ["calc.exe"],
        "notepad": ["notepad.exe"],
        "text editor": ["notepad.exe"],
        "files": ["explorer.exe"],
        "file manager": ["explorer.exe"],
    },
    "darwin": {
        "calculator": ["open", "-a", "Calculator"],
        "notepad": ["open", "-a", "TextEdit"],
        "text editor": ["open", "-a", "TextEdit"],
        "files": ["open", "~"],
        "file manager": ["open", "~"],
    },
    "linux": {
        "calculator": ["gnome-calculator"],
        "notepad": ["gedit"],
        "text editor": ["gedit"],
        "files": ["xdg-open", "~"],
        "file manager": ["xdg-open", "~"],
    },
}


class Jarvis:
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer() if sr else None
        self.voice = None
        if pyttsx3:
            try:
                self.voice = pyttsx3.init()
            except Exception as exc:
                print(f"Text-to-speech is unavailable: {exc}", file=sys.stderr)

    def say(self, message: str) -> None:
        print(f"Jarvis: {message}")
        if self.voice:
            try:
                self.voice.say(message)
                self.voice.runAndWait()
            except Exception as exc:
                print(f"Could not speak response: {exc}", file=sys.stderr)

    def handle(self, command: str) -> bool:
        """Handle one recognized command. Return False when the user wants to quit."""
        command = command.strip().lower()
        if not command:
            return True

        if re.search(r"\b(exit|quit|stop|goodbye)\b", command):
            self.say("Goodbye!")
            return False
        if re.search(r"\b(hello|hi|hey)\b", command):
            self.say("Hello! What can I do for you?")
            return True
        if "help" in command or "what can you do" in command:
            self.say("You can ask me to open Calculator, Notepad, or Files, or search Google for something.")
            return True

        search_match = re.search(r"\bsearch(?:\s+google)?\s+for\s+(.+)", command)
        if search_match:
            query = search_match.group(1).strip()
            if query:
                url = "https://www.google.com/search?" + urllib.parse.urlencode({"q": query})
                self.say(f"Searching Google for {query}.")
                webbrowser.open_new_tab(url)
            else:
                self.say("Please tell me what to search for.")
            return True

        open_match = re.search(r"\bopen\s+(.+)", command)
        if open_match:
            app = open_match.group(1).strip().rstrip(".!?")
            system = platform.system().lower()
            app_table = APP_COMMANDS.get(system, {})
            launch_command = app_table.get(app)
            if launch_command:
                try:
                    subprocess.Popen(launch_command, shell=False)
                    self.say(f"Opening {app}.")
                except FileNotFoundError:
                    self.say(f"I couldn't find {app} on this computer. You may need to install it.")
                except OSError as exc:
                    self.say(f"I couldn't open {app}: {exc}")
            else:
                supported = ", ".join(sorted(app_table)) or "no configured apps"
                self.say(f"I don't have permission to open {app}. Available apps: {supported}.")
            return True

        self.say("I didn't understand that. Say help to hear what I can do.")
        return True

    def listen_once(self) -> str | None:
        if not self.recognizer:
            self.say("Voice recognition is not installed. Install the requirements, then restart me.")
            return None
        try:
            with sr.Microphone() as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
            return self.recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            self.say("Sorry, I didn't catch that.")
            return None
        except sr.RequestError as exc:
            self.say(f"Speech recognition service error: {exc}")
            return None
        except OSError as exc:
            self.say(f"I couldn't access the microphone: {exc}")
            return None

    def run(self) -> None:
        self.say("Jarvis is ready. Say help for commands, or stop to exit.")
        while True:
            try:
                command = self.listen_once()
                if command:
                    print(f"You: {command}")
                    if not self.handle(command):
                        break
            except KeyboardInterrupt:
                self.say("Goodbye!")
                break


def main() -> None:
    if not sr or not pyttsx3:
        missing = []
        if not sr:
            missing.append("SpeechRecognition and PyAudio")
        if not pyttsx3:
            missing.append("pyttsx3")
        print("Missing dependencies: " + ", ".join(missing) + ". Install with: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)
    Jarvis().run()


if __name__ == "__main__":
    main()
