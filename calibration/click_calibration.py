import cv2
import numpy as np

# === Einstellungen ===
STREAM_URL = "https://interactions.ics.unisg.ch/61-102/cam4/live-stream"
SAVE_PATH = "homography_matrix.npz"

clicked_points = []

def click_event(event, x, y, flags, param):
    """Klick-Callback zum Erfassen der Pixelkoordinaten."""
    global clicked_points, frame
    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_points.append((x, y))
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        cv2.putText(frame, f"{len(clicked_points)}", (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Calibration", frame)
        print(f"Punkt {len(clicked_points)}: Pixelkoordinaten = ({x}, {y})")

def main():
    global frame
    cap = cv2.VideoCapture(STREAM_URL)
    if not cap.isOpened():
        print("❌ Kamerastream konnte nicht geöffnet werden.")
        return

    print("✅ Kamera geöffnet. Klicke nacheinander auf 4–6 Referenzpunkte im Bild.")
    print("   Danach schließe das Fenster (Taste ESC).")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Kein Frame empfangen – Stream evtl. unterbrochen.")
            break

        display = frame.copy()
        for i, pt in enumerate(clicked_points):
            cv2.circle(display, pt, 5, (0, 255, 0), -1)
            cv2.putText(display, str(i + 1), (pt[0] + 10, pt[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Calibration", display)
        cv2.setMouseCallback("Calibration", click_event)

        key = cv2.waitKey(10) & 0xFF
        if key == 27:  # ESC zum Beenden
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(clicked_points) < 4:
        print("❌ Zu wenige Punkte. Mindestens 4 nötig.")
        return

    print("\n📏 Jetzt bitte die realen (X,Y)-Koordinaten der Punkte eingeben (in mm).")
    real_points = []
    for i, (px, py) in enumerate(clicked_points):
        X = float(input(f"Punkt {i+1} – reale X-Koordinate (mm): "))
        Y = float(input(f"Punkt {i+1} – reale Y-Koordinate (mm): "))
        real_points.append((X, Y))

    src = np.array(clicked_points, dtype=np.float32)
    dst = np.array(real_points, dtype=np.float32)

    H, _ = cv2.findHomography(src, dst)
    np.savez(SAVE_PATH, H=H)
    print(f"\n✅ Homographie berechnet und gespeichert unter '{SAVE_PATH}'")
    print("   Beispiel-Umrechnung:")
    print(f"   Pixelpunkt (100,100) → {cv2.perspectiveTransform(np.array([[[100,100]]], np.float32), H)[0][0]}")

if __name__ == "__main__":
    main()
