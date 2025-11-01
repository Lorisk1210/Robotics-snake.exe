import cv2
import numpy as np

# === Kameraquelle ===
STREAM_URL = "https://interactions.ics.unisg.ch/61-102/cam4/live-stream"

# === HSV-Bereich für Grün anpassen, wenn nötig ===
LOWER_GREEN = np.array([25, 40, 30])   # etwas breiter für reales Licht
UPPER_GREEN = np.array([95, 255, 255])


def detect_dice(frame):
    """
    Erkennt grüne Würfel und zählt helle Punkte (Pips).
    Rückgabe: (Liste von Dices, Maskenbild)
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # --- Farbbereich für grüne Würfel ---
    mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    # --- mögliche Würfel (quadratische Konturen) ---
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    dices = []

    for c in contours:
        area = cv2.contourArea(c)
        if area < 800:
            continue

        x, y, w, h = cv2.boundingRect(c)
        ratio = w / float(h)

        # Quadratisch → wahrscheinlicher Würfel
        if 0.8 < ratio < 1.2:
            roi = frame[y:y+h, x:x+w]
            value = read_dice_value(roi)
            cx, cy = int(x + w / 2), int(y + h / 2)
            dices.append({
                "center": (cx, cy),
                "value": value,
                "bbox": (x, y, w, h)
            })

    return dices, mask


def read_dice_value(roi):
    """
    Stabilisierte Punkterkennung:
    - weniger Rauschen
    - adaptive Thresholds mit lokalem Mittelwert
    - Auto-Invert bleibt aktiv
    """
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # stärkeres Weichzeichnen
    blur = cv2.GaussianBlur(gray, (7, 7), 1.5)

    # adaptive Thresholds (lokaler Mittelwert statt Gaussian)
    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        15, 4
    )

    # invertierte Variante testen
    inverted = cv2.bitwise_not(thresh)
    candidates = [thresh, inverted]

    best_count = 0
    best_img = thresh

    for t in candidates:
        # Morphologische Kombination: Open → Close → Dilate
        kernel = np.ones((3, 3), np.uint8)
        clean = cv2.morphologyEx(t, cv2.MORPH_OPEN, kernel, iterations=2)
        clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel, iterations=1)
        clean = cv2.dilate(clean, np.ones((3, 3), np.uint8), iterations=1)

        # kleine Konturen filtern
        cnts, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        pips = [c for c in cnts if 15 < cv2.contourArea(c) < 400]

        if len(pips) > best_count:
            best_count = len(pips)
            best_img = clean

    # Debug anzeigen
    cv2.imshow("ROI (Ausschnitt Würfel)", roi)
    cv2.imshow("Pip Detection", best_img)
    cv2.waitKey(1)

    return best_count



def main():
    cap = cv2.VideoCapture(STREAM_URL)
    if not cap.isOpened():
        print("❌ Kamera-Stream nicht erreichbar.")
        return

    print("🎲 Grüne Würfel-Erkennung läuft – drücke 'q' zum Beenden.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        dices, mask = detect_dice(frame)

        # --- Ergebnisse anzeigen ---
        for dice in dices:
            x, y, w, h = dice["bbox"]
            cx, cy = dice["center"]

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(frame, f"{dice['value']}",
                        (x + w + 5, y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)

        cv2.imshow("Green Dice Detection", frame)
        cv2.imshow("Mask", mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
