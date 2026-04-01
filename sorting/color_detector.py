import cv2
import numpy as np

# HSV ranges for target colors
# Individual color ranges
COLOR_RANGES = {
    "green":      {"lower": np.array([35, 80, 80]),    "upper": np.array([85, 255, 255])},
    "blue":       {"lower": np.array([85, 40, 20]),    "upper": np.array([135, 255, 255])},
    "gray":       {"lower": np.array([0, 0, 40]),       "upper": np.array([179, 40, 220])},
}

# Group colors into two categories for sorting output
GROUPS = {
    "green/blue": ["green", "blue"],
    "gray":       ["gray"],
}

# How much of the frame to use as the center ROI (0.0-1.0)
CENTER_CROP = 0.5


def get_color_percentages(frame):
    """Return percentage of center ROI occupied by each target color."""
    h, w = frame.shape[:2]
    # Crop center region
    cx, cy = w // 2, h // 2
    half_w, half_h = int(w * CENTER_CROP / 2), int(h * CENTER_CROP / 2)
    roi = frame[cy - half_h:cy + half_h, cx - half_w:cx + half_w]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    total_pixels = roi.shape[0] * roi.shape[1]

    # Build masks
    pcts = {}
    for name, bounds in COLOR_RANGES.items():
        mask = cv2.inRange(hsv, bounds["lower"], bounds["upper"])
        pcts[name] = np.count_nonzero(mask) / total_pixels * 100
    return pcts, roi


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("ERROR: cannot open camera")
        return

    prev_dominant = None

    print("Color detector running — press 'q' to quit")
    print(f"Camera: 640x480 | Center ROI: {CENTER_CROP*100:.0f}% crop")
    print("-" * 50)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        pcts, roi = get_color_percentages(frame)

        # Sum percentages by group
        MIN_THRESHOLD = 5.0
        group_pcts = {}
        for group_name, members in GROUPS.items():
            group_pcts[group_name] = sum(pcts.get(m, 0) for m in members)

        # Print whenever any group exceeds threshold
        above = {k: v for k, v in group_pcts.items() if v >= MIN_THRESHOLD}
        if above != prev_dominant:
            gb = group_pcts['green/blue']
            gr = group_pcts['gray']
            dominant = max(group_pcts, key=group_pcts.get)
            if dominant == "green/blue" and gb >= MIN_THRESHOLD:
                print(f"Recycling : Right : {gb:.1f}%")
            elif dominant == "gray" and gr >= MIN_THRESHOLD:
                print(f"Trash : Left : {gr:.1f}%")
            else:
                print(f"No detection above threshold")
            prev_dominant = above

        # Overlay group percentages on the ROI
        DISPLAY_COLORS = {"green/blue": (200, 128, 0), "gray": (200, 200, 200)}
        y_off = 30
        for group_name, pct in group_pcts.items():
            bgr = DISPLAY_COLORS[group_name]
            label = f"{group_name}: {pct:.1f}%"
            cv2.putText(roi, label, (10, y_off),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, bgr, 2)
            y_off += 30

        cv2.imshow("Sorting Vision", roi)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or cv2.getWindowProperty("Sorting Vision", cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)


if __name__ == "__main__":
    main()
