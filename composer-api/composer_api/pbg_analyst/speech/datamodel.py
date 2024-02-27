import requests
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
import pygame


class Conversationalist:
    def __init__(self, mic_recognizer=None):
        self.r = mic_recognizer or sr.Recognizer()

    def listen(self, dur: int = 5) -> str:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            audio_data = r.record(source, duration=5)
            text = r.recognize_google(audio_data)
            return text

    def interpret(self, input_text: str):
        response = requests.post("http://your_fastapi_server/generate-text/", json={"prompt": input_text})
        generated_text = response.json()["generated_text"]
        return generated_text

    def speak(self, generated_text: str):
        tts = gTTS(generated_text)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)

        pygame.mixer.init()
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():  # Wait for audio to finish playing
            pass
