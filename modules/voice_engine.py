import os
import riva.client
import speech_recognition as sr
import pygame
import io
from dotenv import load_dotenv

load_dotenv()

class VoiceEngine:
    def __init__(self):
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.server = "grpc.nvcf.nvidia.com:443"
        
        # EAR ID (NVIDIA Canary-1B ASR)
        self.asr_function_id = "b0e8b4a5-217c-40b7-9b96-17d84e666317"
        # MOUTH ID (NVIDIA Magpie-TTS-Multilingual)
        self.tts_function_id = "877104f7-e885-42b9-8de8-f6e4c6303969"
        
        # Authentication for Listening (ASR)
        self.asr_auth = riva.client.Auth(
            uri=self.server,
            use_ssl=True,
            metadata_args=[
                ("function-id", self.asr_function_id),
                ("authorization", f"Bearer {self.api_key}")
            ]
        )
        
        # Authentication for Speaking (TTS)
        self.tts_auth = riva.client.Auth(
            uri=self.server,
            use_ssl=True,
            metadata_args=[
                ("function-id", self.tts_function_id),
                ("authorization", f"Bearer {self.api_key}")
            ]
        )

        # Initialize separate services
        self.riva_asr = riva.client.ASRService(self.asr_auth)
        self.riva_tts = riva.client.SpeechSynthesisService(self.tts_auth)
        
        # Initialize Audio Output
        pygame.mixer.quit()
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
        self.recognizer = sr.Recognizer()

    def listen(self):
        """Transcribe speech using NVIDIA Canary-1B via gRPC"""
        with sr.Microphone(sample_rate=16000) as source:
            print("[Jarvis] Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                # Convert to raw PCM bytes
                content = audio.get_raw_data(convert_rate=16000, convert_width=2)
                
                config = riva.client.RecognitionConfig(
                    encoding=riva.client.AudioEncoding.LINEAR_PCM,
                    sample_rate_hertz=16000,
                    language_code="en-US",
                    max_alternatives=1,
                    enable_automatic_punctuation=True,
                )

                response = self.riva_asr.offline_recognize(content, config)
                
                if response.results:
                    transcript = response.results[0].alternatives[0].transcript
                    print(f"User: {transcript}")
                    return transcript
                return ""
            except Exception as e:
                print(f"[Voice Error] ASR Failure: {e}")
                return ""

    def speak(self, text):
        """Synthesize speech using NVIDIA Magpie-TTS via gRPC"""
        if not text:
            return
            
        print(f"[Jarvis] Speaking: {text}")

        try:
            # Using the specific Magpie voice name from the documentation
            processed_text = text.replace("Hello", "Hello,")
            response = self.riva_tts.synthesize(
                text=processed_text,
                voice_name="Magpie-Multilingual.EN-US.Mia", 
                language_code="en-US",
                
                encoding=riva.client.AudioEncoding.LINEAR_PCM,
                sample_rate_hz=22050 
            )

            # Load the raw PCM bytes directly into a pygame Sound object
            sound = pygame.mixer.Sound(buffer=response.audio)
            sound.play()
            
            # Wait for playback to finish
            while pygame.mixer.get_busy():
                pygame.time.Clock().tick(10)

        except Exception as e:
            print(f"[Speak Error] TTS Failure: {e}")