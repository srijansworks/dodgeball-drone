import cv2, time, csv, json, os
import numpy as np

# Manual HSV sliders. The last values are saved to hsv.json on quit and reloaded next run.
SAVE = "hsv.json"
INIT = {"H lo": 5, "S lo": 150, "V lo": 150, "H hi": 20, "S hi": 255, "V hi": 255}
LIMIT = {"H lo": 179, "H hi": 179, "S lo": 255, "S hi": 255, "V lo": 255, "V hi": 255}
try:
    INIT.update(json.load(open(SAVE)))
except (OSError, ValueError):
    pass

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Webcam did not open. Allow camera access for your terminal in System Settings > Privacy & Security > Camera.")

cv2.namedWindow("mask")
for name, val in INIT.items():
    cv2.createTrackbar(name, "mask", val, LIMIT[name], lambda _: None)

log = open("logs/stage1.csv", "w", newline="")
w = csv.writer(log)
w.writerow(["t", "cx", "cy", "r"])

while True:
    ok, frame = cap.read()
    if not ok:
        break
    t = time.time()
    v = {n: cv2.getTrackbarPos(n, "mask") for n in INIT}
    lo = np.array([v["H lo"], v["S lo"], v["V lo"]])
    hi = np.array([v["H hi"], v["S hi"], v["V hi"]])
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lo, hi)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    status = "no ball"
    if cnts:
        cnt = max(cnts, key=cv2.contourArea)
        (x, y), r = cv2.minEnclosingCircle(cnt)
        if r > 5:
            status = "tracking"
            cv2.circle(frame, (int(x), int(y)), int(r), (0, 255, 0), 2)
            w.writerow([t, x, y, r])
    cv2.putText(frame, f"{status}  q=quit", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.imshow("frame", frame)
    cv2.imshow("mask", mask)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

json.dump(v, open(SAVE, "w"))
print("lo =", lo.tolist(), "hi =", hi.tolist())
cap.release()
log.close()
cv2.destroyAllWindows()
