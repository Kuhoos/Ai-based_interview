import requests
import speech_recognition as sr
import sounddevice as sd
import pyttsx3

from vision.eye_tracking import set_status

# ---------------------------
# TEXT TO SPEECH
# ---------------------------
engine = pyttsx3.init()
engine.setProperty('rate', 150)
import pyttsx3
import time

def speak(text):
    print("🔊 Speaking:", text)

    engine = pyttsx3.init('sapi5')   # create new engine every time
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)

    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)

    engine.say(text)
    engine.runAndWait()
    engine.stop()

    time.sleep(0.3)  # prevents freezing
# ---------------------------
# RECORD AUDIO WITH BETTER SETTINGS
# ---------------------------
SAMPLERATE = 16000
RECORD_SECONDS = 3  # Reduced from 5 seconds

recognizer = sr.Recognizer()
# Microphone calibration removed - not essential for basic functionality

def get_input_device_info():
    try:
        # Try to get a valid input device
        devices = sd.query_devices()
        
        # Find first device with input channels
        for idx, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                return idx, device
        
        # If no device found, raise error
        raise RuntimeError("No input device with microphone found.")
    except Exception as e:
        print("❌ Audio device error:", e)
        try:
            devices = sd.query_devices()
            print("Available audio devices:")
            for idx, device in enumerate(devices):
                print(f"  {idx}: {device['name']} (input_channels={device['max_input_channels']})")
        except Exception:
            pass
        return None


def record_audio(duration=RECORD_SECONDS):
    try:
        set_status("Recording...")
        print("🎤 Recording...")

        device_info = get_input_device_info()
        if device_info is None:
            print("⚠️ Using default microphone...")
            device_info = (None, None)

        input_device, _ = device_info
        recording = sd.rec(
            int(duration * SAMPLERATE),
            samplerate=SAMPLERATE,
            channels=1,
            dtype='int16',
            device=input_device
        )
        sd.wait()

        if recording.size == 0 or not recording.any():
            print("❌ No audio captured. Check your microphone and try again.")
            return None

        audio_data = sr.AudioData(recording.tobytes(), SAMPLERATE, 2)
        return audio_data

    except Exception as e:
        print("❌ Recording Error:", e)
        return None

# ---------------------------
# SPEECH TO TEXT WITH FALLBACK
# ---------------------------
def listen_with_fallback():
    """Try speech recognition, fallback to text input if it fails"""
    print("\n🎤 Say something or type 'text' to switch to text mode...")

    # Try speech first
    audio_data = record_audio(duration=3)  # Shorter recording

    if audio_data is None:
        print("❌ Audio recording failed. Switching to text mode...")
        return get_text_input()

    try:
        text = recognizer.recognize_google(audio_data, language='en-US')
        if text.lower().strip() == 'text':
            print("🔤 Switching to text mode...")
            return get_text_input()
        print("🧑 You:", text)
        return text

    except sr.UnknownValueError:
        print("❌ Could not understand audio. Try speaking louder or switch to text mode by saying 'text'.")
        return None

    except sr.RequestError as e:
        print("❌ Speech recognition service error:", e)
        print("🔤 Switching to text mode...")
        return get_text_input()

    except Exception as e:
        print("❌ Speech recognition error:", e)
        print("🔤 Switching to text mode...")
        return get_text_input()

def get_text_input():
    """Get input from text/keyboard"""
    try:
        text = input("🔤 Type your message: ").strip()
        if text:
            print("🧑 You:", text)
            return text
    except KeyboardInterrupt:
        return "exit"
    return None

def listen():
    """Main listening function with fallback"""
    return listen_with_fallback()

# ---------------------------
# AI RESPONSE (OLLAMA)
# ---------------------------
def get_ai_response(user_input):
    try:
        print("🤔 Thinking... (sending to Ollama)")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": user_input,
                "stream": False
            },
            timeout=120
        )

        if response.status_code != 200:
            print(f"❌ Ollama HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return "I'm having trouble connecting right now."

        response_json = response.json()

        if "response" in response_json:
            ai_response = response_json["response"].strip()
            print(f"✅ AI Response received ({len(ai_response)} chars)")
            return ai_response
        else:
            print(f"❌ Unexpected Ollama response format: {response_json}")
            return "I'm having trouble understanding that."

    except requests.exceptions.Timeout:
        print("❌ Ollama Timeout: Request took too long")
        return "Sorry, I'm taking too long to respond. Please try again."
    except requests.exceptions.ConnectionError:
        print("❌ Ollama Connection Error: Make sure Ollama is running on http://localhost:11434")
        return "I cannot connect to the AI service. Is Ollama running?"
    except Exception as e:
        print("❌ Ollama Error:", e)
        return "I'm having trouble connecting right now."

# ---------------------------
# MAIN CHATBOT LOOP
# ---------------------------
def chatbot():

    print("🎙️ AI Assistant Started")
    speak("Hello! I am your AI assistant. Start speaking or say 'text' to type.")

    failed_attempts = 0
    max_failed_attempts = 3  # Reduced from 5

    while True:
        try:
            set_status("Listening...")
            user_input = listen()

            if user_input is None:
                failed_attempts += 1
                if failed_attempts >= max_failed_attempts:
                    print(f"❌ Too many failed attempts ({max_failed_attempts}). Try saying 'text' to switch to typing mode.")
                    speak("Having trouble understanding. Try saying 'text' to switch to typing mode.")
                    failed_attempts = 0
                continue

            failed_attempts = 0  # Reset counter on successful input

            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                speak("Goodbye!")
                break

            set_status("Thinking...")
            response = get_ai_response(user_input)

            if response and response.strip():
                set_status("Speaking...")
                speak(response)
            else:
                speak("I didn't get a response. Please try again.")

        except KeyboardInterrupt:
            print("\n🛑 Chatbot stopped.")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            speak("An error occurred. Let me try again.")