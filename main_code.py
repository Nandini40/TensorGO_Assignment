import assemblyai as aai
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
import ollama
import cv2
import sounddevice as sd
import numpy as np

class AI_Assistant:
    def __init__(self) -> None:
        # Set your API keys directly
        aai.settings.api_key = "a2c2280f7759456b906e6e873911c090"  # AssemblyAI API key
        
        self.client = ElevenLabs(
            api_key="sk_304571241de25e22ce71f6d3c9fce99291ca9a803c49c70c"  # ElevenLabs API key
        )

        self.transcriber = None

        self.full_transcript = [
            {"role": "system", "content": "You are a language model called Llama 3, answer the question"}
        ]
        
        # Webcam setup
        self.cap = cv2.VideoCapture(0)

    def start_transcription(self):
        self.transcriber = aai.RealtimeTranscriber(
            sample_rate=16000,
            on_data=self.on_data,
            on_error=self.on_error,
            on_open=self.on_open,
            on_close=self.on_close,
        )

        self.transcriber.connect()
        self.start_microphone_stream()
    
    def start_microphone_stream(self):
        self.microphone_stream = sd.InputStream(samplerate=16000, channels=1, callback=self.audio_callback)
        self.microphone_stream.start()

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.transcriber.send_audio(indata)

    def close_transcription(self):
        if self.transcriber:
            self.transcriber.close()
            self.transcriber = None
        if self.microphone_stream:
            self.microphone_stream.stop()
            self.microphone_stream.close()

    def on_open(self, session_opened: aai.RealtimeSessionOpened):
        print("Transcription session opened.")

    def on_data(self, transcript: aai.RealtimeTranscript):
        if not transcript.text:
            return

        if isinstance(transcript, aai.RealtimeFinalTranscript):
            self.generate_ai_response(transcript)
        else:
            print(transcript.text, end="\r")

    def on_error(self, error: aai.RealtimeError):
        print(f"Error: {error}")
        self.close_transcription()

    def on_close(self):
        print("Transcription session closed.")
        self.close_transcription()

    def generate_ai_response(self, transcript):
        self.close_transcription()

        self.full_transcript.append({"role": "user", "content": transcript.text})
        print(f"\nUSER: {transcript.text}")

        ollama_stream = ollama.chat(
            model="llama3",
            messages=self.full_transcript,
            stream=True,
        )

        print(f"\nLlama 3:", end=" ")

        text_buffer = ""
        full_text = ""
        for chunk in ollama_stream:
            text_buffer = chunk['messages']['content']
            print(text_buffer, flush=True)  # Print the response

            # Convert the text to speech using ElevenLabs
            audio_stream = self.client.generate(
                text=text_buffer, model="eleven_turbo_v2", stream=True
            )
            stream(audio_stream)

            full_text += text_buffer

        self.full_transcript.append({"role": "assistant", "content": full_text})
        self.start_transcription()

    def run_webcam(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            cv2.imshow('Webcam', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
                break

        self.cap.release()
        cv2.destroyAllWindows()

# Create an instance of the AI Assistant and start transcription
if __name__ == "__main__":
    ai_assistant = AI_Assistant()
    ai_assistant.start_transcription()
    ai_assistant.run_webcam()
