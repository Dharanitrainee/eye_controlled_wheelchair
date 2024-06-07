import pyttsx3 as tts
import threading
import cv2
import math
import utils
import numpy as np
import mediapipe as mp
import speech_recognition
import sys
import time
import serial

FONTS = cv2.FONT_HERSHEY_COMPLEX

name_assistant = "Hinata"

engine = tts.init()
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[1].id)
engine.setProperty("rate", 150)


def speak(data):
    engine.say(data)
    print(name_assistant + " : " + data)
    engine.runAndWait()


mp_face_mesh = mp.solutions.face_mesh

FACE_OVAL = [
    10,
    338,
    297,
    332,
    284,
    251,
    389,
    356,
    454,
    323,
    361,
    288,
    397,
    365,
    379,
    378,
    400,
    377,
    152,
    148,
    176,
    149,
    150,
    136,
    172,
    58,
    132,
    93,
    234,
    127,
    162,
    21,
    54,
    103,
    67,
    109,
]
LIPS = [
    61,
    146,
    91,
    181,
    84,
    17,
    314,
    405,
    321,
    375,
    291,
    308,
    324,
    318,
    402,
    317,
    14,
    87,
    178,
    88,
    95,
    185,
    40,
    39,
    37,
    0,
    267,
    269,
    270,
    409,
    415,
    310,
    311,
    312,
    13,
    82,
    81,
    42,
    183,
    78,
]
LOWER_LIPS = [
    61,
    146,
    91,
    181,
    84,
    17,
    314,
    405,
    321,
    375,
    291,
    308,
    324,
    318,
    402,
    317,
    14,
    87,
    178,
    88,
    95,
]
UPPER_LIPS = [
    185,
    40,
    39,
    37,
    0,
    267,
    269,
    270,
    409,
    415,
    310,
    311,
    312,
    13,
    82,
    81,
    42,
    183,
    78,
]
LEFT_EYEBROW = [336, 296, 334, 293, 300, 276, 283, 282, 295, 285]
RIGHT_EYEBROW = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
LEFT_EYE = [
    362,
    382,
    381,
    380,
    374,
    373,
    390,
    249,
    263,
    466,
    388,
    387,
    386,
    385,
    384,
    398,
]
RIGHT_EYE = [
    33,
    7,
    163,
    144,
    145,
    153,
    154,
    155,
    133,
    173,
    157,
    158,
    159,
    160,
    161,
    246,
]
LEFT_IRIS = [469, 470, 471, 472]
RIGHT_IRIS = [474, 475, 476, 477]
L_H_LEFT = [33]
L_H_Right = [133]
R_H_LEFT = [362]
R_H_RIGHT = [263]
RV_TOP = [159]
RV_BOTTOM = [145]


def initialize_arduino(port='COM17', baudrate=9600):
    try:
        arduino = serial.Serial(port=port, baudrate=baudrate)
        print("Successfully connected to Arduino.")
        return arduino
    except serial.SerialException:
        print("Failed to connect to Arduino. Please check the connection.")
        return None


def send_to_arduino(arduino_controller, data):
    try:
        arduino_controller.write(str(data).encode())
        print("Data sent to Arduino:", data)
        time.sleep(0.19)
        arduino_controller.flush()
    except AttributeError:
        print("Arduino is not initialized.")
    except serial.SerialException:
        print("Failed to send data to Arduino.")


def close_arduino(controller):
    if controller is not None:
        controller.close()
        print("Arduino connection closed.")


vid = cv2.VideoCapture(0)
width, height = 800, 600
vid.set(cv2.CAP_PROP_FRAME_WIDTH, width)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
arduino = None
tracking_active = True


def euclidean_distance(point1, point2):
    x1, y1 = point1.ravel()
    x2, y2 = point2.ravel()
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance


def iris_position(iris_center, right_point, left_point):
    center_to_right_dist = euclidean_distance(iris_center, right_point)
    total_distance = euclidean_distance(right_point, left_point)
    ratio = center_to_right_dist / total_distance
    iris_position = ""
    if ratio <= 0.42:
        iris_position = "right"
    elif ratio > 0.42 and ratio <= 0.57:
        iris_position = "center"
    else:
        iris_position = "left"
    return iris_position, ratio


def blink(img, landmarks, left_indices):
    global arduino
    RH_TOP = landmarks[left_indices[12]]
    RH_BOTTOM = landmarks[left_indices[4]]
    cv2.line(img, RH_TOP, RH_BOTTOM, utils.GREEN, 2)
    RV_DISTANCE = euclidean_distance(RH_TOP, RH_BOTTOM)
    RV_DISTANCE = int(RV_DISTANCE)
    RV_DISTANCE = RV_DISTANCE / 2
    if RV_DISTANCE <= 5:
        send_to_arduino(arduino, 5)
        color = [utils.GRAY, utils.MAGENTA]
        cv2.putText(img, "FORWARD", (200, 50), FONTS, 1.3, utils.PINK, 2)
    elif RV_DISTANCE > 5:
        send_to_arduino(arduino, 6)
        color = [utils.GRAY, utils.MAGENTA]


def tracking():
    global tracking_active
    while tracking_active:
        with mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
        ) as face_mesh:
            while True:
                ret, img = vid.read()
                if not ret or not tracking_active:
                    print("Error: Failed to capture frame.")
                    break
                img = cv2.flip(img, 1)
                rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_h, img_w = img.shape[:2]
                results = face_mesh.process(rgb_frame)
                if results.multi_face_landmarks:
                    mesh_points = np.array(
                        [
                            np.multiply([p.x, p.y], [img_w, img_h]).astype(int)
                            for p in results.multi_face_landmarks[0].landmark
                        ]
                    )
                    blink(img, mesh_points, RIGHT_EYE)
                    cv2.polylines(
                        img, [mesh_points[LEFT_IRIS]], True, (0, 255, 0), 1, cv2.LINE_AA
                    )
                    cv2.polylines(
                        img, [mesh_points[LEFT_EYE]], True, (0, 255, 0), 1, cv2.LINE_AA
                    )
                    cv2.polylines(
                        img, [mesh_points[RIGHT_IRIS]], True, (0, 255, 0), 1, cv2.LINE_AA
                    )
                    cv2.polylines(
                        img, [mesh_points[RIGHT_EYE]], True, (0, 255, 0), 1, cv2.LINE_AA
                    )
                    (l_cx, l_cy), l_radius = cv2.minEnclosingCircle(mesh_points[LEFT_IRIS])
                    (r_cx, r_cy), r_radius = cv2.minEnclosingCircle(mesh_points[RIGHT_IRIS])
                    center_left = np.array([l_cx, l_cy], dtype=np.int32)
                    center_right = np.array([r_cx, r_cy], dtype=np.int32)
                    cv2.circle(
                        img, center_left, int(l_radius), (255, 0, 255), 1, cv2.LINE_AA
                    )
                    cv2.circle(
                        img, center_right, int(r_radius), (255, 0, 255), 1, cv2.LINE_AA
                    )
                    cv2.circle(
                        img, mesh_points[R_H_RIGHT][0], 3, (255, 0, 255), -1, cv2.LINE_AA
                    )
                    cv2.circle(
                        img, mesh_points[R_H_LEFT][0], 3, (0, 255, 255), -1, cv2.LINE_AA
                    )
                    cv2.circle(
                        img, mesh_points[RV_TOP][0], 3, (0, 255, 255), -1, cv2.LINE_AA
                    )
                    cv2.circle(
                        img, mesh_points[RV_BOTTOM][0], 3, (255, 0, 255), -1, cv2.LINE_AA
                    )
                    iris_pos, ratio = iris_position(
                        center_right, mesh_points[R_H_RIGHT], mesh_points[R_H_LEFT][0]
                    )
                    cv2.imshow("output", img)
                    if iris_pos == "center":
                        print("center")
                        send_to_arduino(arduino, 2)
                    elif iris_pos == "right":
                        print("right")
                        send_to_arduino(arduino, 4)
                        cv2.putText(img, "RIGHT", (200, 50), FONTS, 1.3, utils.PINK, 2)
                    elif iris_pos == "left":
                        print("left")
                        send_to_arduino(arduino, 3)
                        cv2.putText(img, "LEFT", (200, 50), FONTS, 1.3, utils.PINK, 2)
                        time.sleep(0.019)
                    if cv2.waitKey(1) == 113:
                        break


def process_audio():
    global tracking_active
    global arduino
    while True:
        try:
            r = speech_recognition.Recognizer()
            r.dynamic_energy_threshold = True
            with speech_recognition.Microphone() as mic:
                audio = r.listen(mic)
                text = r.recognize_google(audio)
                print("Listening")
                statement = text.lower()
                results = ""
                if "shutdown" in statement or "turnoff" in statement:
                    print(f"Detected command: {statement}")
                    speak(
                        "Your personal assistant "
                        + name_assistant
                        + " is shutting down, Goodbye"
                    )
                    close_arduino(arduino)
                    vid.release()
                    cv2.destroyAllWindows()
                    sys.exit(0)

                if "start tracking" in statement or "enable tracking" in statement:
                    speak("Eye tracking has been started")
                    threading.Thread(target=tracking).start()

                if "stop tracking" in statement or "stop" in statement or "end tracking" in statement:
                    speak("Eye tracking has been stopped")
                    tracking_active = False
                    threading.Thread(target=tracking).join()
                    send_to_arduino(arduino, 6)
                    cv2.destroyAllWindows()

                speak(results)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("An error occurred:", e)


def main():
    global arduino
    arduino = initialize_arduino()
    process_audio()


if _name_ == "_main_":
    main()
