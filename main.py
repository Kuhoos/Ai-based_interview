from vision.eye_tracking import run_eye_tracking, stop_eye_tracking
from chatbot.bot import chatbot
import threading

if __name__ == "__main__":
    stop_event = threading.Event()
    t1 = threading.Thread(target=run_eye_tracking, args=(stop_event,), daemon=True)
    t1.start()

    try:
        chatbot()
    finally:
        stop_event.set()
        stop_eye_tracking()
        t1.join(timeout=2)