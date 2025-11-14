import cv2

# Deine Kamerastream-URL
url = "https://interactions.ics.unisg.ch/61-102/cam4/live-stream"

cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Kamera-Stream kann nicht geöffnet werden.")
else:
    print("Kamera-Stream erfolgreich geöffnet!")

    ret, frame = cap.read()
    if ret:
        print("Frame empfangen, Auflösung:", frame.shape[1], "x", frame.shape[0])
        cv2.imshow("Kamera-Test", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Kein Frame empfangen - eventuell nicht kompatibles Format (z. B. RTSP oder MJPEG erforderlich).")

cap.release()
