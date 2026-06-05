import cv2

# global status (used by chatbot)
status = "Idle"

# Event to signal the eye-tracking thread to stop.
stop_event = None

def set_status(text):
    global status
    status = text

def stop_eye_tracking():
    global stop_event
    if stop_event is not None:
        stop_event.set()

def run_eye_tracking(stop_event_arg=None):
    global status, stop_event
    stop_event = stop_event_arg

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    cap = cv2.VideoCapture(0)

    while True:
        if stop_event is not None and stop_event.is_set():
            break

        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        direction = "No Face"

        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_center_x = x + w / 2
            frame_center_x = frame.shape[1] / 2
            offset = (face_center_x - frame_center_x) / frame_center_x

            if offset < -0.2:
                direction = "Looking Left"
            elif offset > 0.2:
                direction = "Looking Right"
            else:
                direction = "Looking Center"

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.putText(frame, f"Eye: {direction}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.putText(frame, f"Status: {status}", (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

        cv2.imshow("Eye Tracking", frame)

        if cv2.getWindowProperty("Eye Tracking", cv2.WND_PROP_VISIBLE) < 1:
            break

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()