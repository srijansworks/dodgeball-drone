import cv2, time, csv, json, os
from collections import deque
import numpy as np

# Time-to-contact: tau = r / (dr/dt). Slope comes from a line fit over the last N radius samples.
N = 8              # samples in the fit
MIN_SLOPE = 5.0    # px/s; below this the ball is not clearly approaching, so no tau
LOST_S = 0.3       # no ball for this long clears the samples
samples = deque(maxlen=N)  # (t, r)

# Dodge rule: tau below threshold AND ball growing (tau exists only then) AND ball near image center (it would hit).
TAU_TRIGGER = 0.8     # s, tune later
CENTER_FRAC = 0.3     # ball center within +-30% of image width from the middle
COOLDOWN = 2.0        # s, so one throw gives one dodge, not a burst
last_dodge = -1e9
banner = ("", 0.0)    # (text, time) shown on screen for 1 s

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

log = open("logs/stage3.csv", "w", newline="")
w = csv.writer(log)
w.writerow(["t", "cx", "cy", "r", "slope", "tau", "event"])

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
    tau = slope = None
    if cnts:
        cnt = max(cnts, key=cv2.contourArea)
        (x, y), r = cv2.minEnclosingCircle(cnt)
        if r > 5:
            status = "tracking"
            cv2.circle(frame, (int(x), int(y)), int(r), (0, 255, 0), 2)
            samples.append((t, r))
            if len(samples) >= 4:
                ts, rs = np.array(samples).T
                tt = ts - ts[0]
                slope, icpt = np.polyfit(tt, rs, 1)
                if slope > MIN_SLOPE:
                    # The slope is the average over the window, so measure tau at the window middle, then subtract the half-window age.
                    tm = tt.mean()
                    tau = (slope * tm + icpt) / slope - (tt[-1] - tm)
            event = ""
            half = frame.shape[1] / 2
            if tau is not None and tau < TAU_TRIGGER and abs(x - half) < CENTER_FRAC * 2 * half and t - last_dodge > COOLDOWN:
                event = "DODGE RIGHT" if x <= half else "DODGE LEFT"  # away from the ball; dead center picks right
                last_dodge = t
                banner = (event, t)
                print(event, f"tau={tau:.2f}")
            w.writerow([t, x, y, r, slope, tau, event])
    if status != "tracking" and samples and t - samples[-1][0] > LOST_S:
        samples.clear()
    cv2.putText(frame, f"{status}  y=right call  n=wrong call  q=quit", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    if t - banner[1] < 1.0:
        cv2.putText(frame, banner[0], (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)
    msg = f"tau {tau:.2f} s" if tau is not None else "tau --"
    cv2.putText(frame, msg, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255) if tau is not None and tau < 0.8 else (255, 255, 255), 2)
    cv2.imshow("frame", frame)
    cv2.imshow("mask", mask)
    k = cv2.waitKey(1) & 0xFF
    if k == ord("q"):
        break
    if k in (ord("y"), ord("n")):  # label the last throw so hit/miss is logged
        label = "right call" if k == ord("y") else "wrong call"
        w.writerow([t, "", "", "", "", "", label])
        print(label)

json.dump(v, open(SAVE, "w"))
print("lo =", lo.tolist(), "hi =", hi.tolist())
cap.release()
log.close()
cv2.destroyAllWindows()
