import cv2
import numpy as np

STREAM_URL = "https://interactions.ics.unisg.ch/61-102/cam2/live-stream"

LOWER_PINK = np.array([145, 20, 130])
UPPER_PINK = np.array([180, 100, 255])

LOWER_PINK_2 = np.array([0, 20, 130])
UPPER_PINK_2 = np.array([10, 100, 255])


def detect_dice(frame):
    if frame is None or frame.size == 0:
        return [], None
    
    blur = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

    mask1 = cv2.inRange(hsv, LOWER_PINK, UPPER_PINK)
    mask2 = cv2.inRange(hsv, LOWER_PINK_2, UPPER_PINK_2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    dices = []

    for c in contours:
        area = cv2.contourArea(c)
        if area < 500:
            continue

        x, y, w, h = cv2.boundingRect(c)
        if w < 20 or h < 20:
            continue
            
        ratio = w / float(h)
        
        if 0.6 < ratio < 1.7:
            padding = 5
            y1 = max(0, y - padding)
            y2 = min(frame.shape[0], y + h + padding)
            x1 = max(0, x - padding)
            x2 = min(frame.shape[1], x + w + padding)
            
            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                continue
                
            value = read_dice_value(roi)
            cx, cy = int(x + w / 2), int(y + h / 2)
            dices.append({
                "center": (cx, cy),
                "value": value,
                "bbox": (x, y, w, h)
            })

    return dices, mask


def read_dice_value(roi):
    if roi is None or roi.size == 0:
        return 0
    
    h_orig, w_orig = roi.shape[:2]
    if h_orig < 10 or w_orig < 10:
        return 0
    
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    v_channel = hsv[:, :, 2]
    v_eq = cv2.equalizeHist(v_channel)
    hsv[:, :, 2] = v_eq
    roi_enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    gray = cv2.cvtColor(roi_enhanced, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    
    block_size = 11 if min(h_orig, w_orig) > 30 else 7
    if block_size % 2 == 0:
        block_size += 1
    
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block_size,
        6
    )
    
    kernel_small = np.ones((2, 2), np.uint8)
    kernel_medium = np.ones((3, 3), np.uint8)
    
    clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_small, iterations=1)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel_medium, iterations=2)
    
    h, w = clean.shape
    border_x = max(2, int(w * 0.12))
    border_y = max(2, int(h * 0.12))
    
    if h > 2 * border_y and w > 2 * border_x:
        clean = clean[border_y:h-border_y, border_x:w-border_x]
    
    if clean.size == 0:
        return 0
    
    cnts, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    roi_area = clean.shape[0] * clean.shape[1]
    min_area = max(50, 0.005 * roi_area)
    max_area = min(1500, 0.15 * roi_area)
    
    valid_pips = []
    for c in cnts:
        area = cv2.contourArea(c)
        if not (min_area <= area <= max_area):
            continue
        
        perimeter = cv2.arcLength(c, True)
        if perimeter == 0:
            continue
        
        circularity = 4 * np.pi * (area / (perimeter ** 2))
        
        if circularity > 0.3:
            valid_pips.append(c)
    
    pip_count = len(valid_pips)
    
    if pip_count > 6:
        valid_pips_sorted = sorted(valid_pips, key=cv2.contourArea, reverse=True)
        pip_count = len([p for p in valid_pips_sorted[:6]])
    
    cv2.imshow("ROI (Dice)", roi)
    debug_img = cv2.cvtColor(clean, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(debug_img, valid_pips, -1, (0, 255, 0), 2)
    cv2.imshow("Pip Detection", debug_img)
    cv2.waitKey(1)
    
    return pip_count







def main():
    cap = cv2.VideoCapture(STREAM_URL)
    if not cap.isOpened():
        print("Kamera-Stream nicht erreichbar.")
        return

    print("Würfelerkennung gestartet – 'q' zum Beenden drücken.")

    # Optionale Auflösungserhöhung
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        dices, mask = detect_dice(frame)

        # Ergebnisse darstellen
        for dice in dices:
            x, y, w, h = dice["bbox"]
            cx, cy = dice["center"]
            value = dice["value"]

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, str(value),
                        (x + w + 5, y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)

            # Ausgabe im Terminal
            print(f"Würfel erkannt an ({cx}, {cy}) mit Wert: {value}")

        cv2.imshow("Dice Detection", frame)
        cv2.imshow("Mask", mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
