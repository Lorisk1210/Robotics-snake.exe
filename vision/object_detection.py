import cv2
import numpy as np

# === Kameraquelle ===
STREAM_URL = "https://interactions.ics.unisg.ch/61-102/cam4/live-stream"

def main():
    cap = cv2.VideoCapture(STREAM_URL)
    if not cap.isOpened():
        print("❌ Kamera-Stream nicht erreichbar.")
        return

    print("✅ Kamera gestartet – erkenne grüne Objekte. Drücke 'q' zum Beenden.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # --- leicht weichzeichnen gegen Rauschen ---
        blur = cv2.GaussianBlur(frame, (5, 5), 0)

        # --- Farbraum HSV ---
        hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

        # --- Grünbereich (Hue ca. 35–85) ---
        lower_green = np.array([35, 80, 60])
        upper_green = np.array([85, 255, 255])

        # --- Maske für Grün ---
        mask = cv2.inRange(hsv, lower_green, upper_green)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        # --- Konturen suchen ---
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area < 500:
                continue

            x, y, w, h = cv2.boundingRect(c)
            cx, cy = int(x + w / 2), int(y + h / 2)

            # Zeichne auf das **Originalbild** (nicht Overlay)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(frame, f"green cube ({cx},{cy})", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # --- Ausgabe: echtes Bild ---
        cv2.imshow("Green Cube Detection", frame)
        cv2.imshow("Mask", mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
