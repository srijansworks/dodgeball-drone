# Dodgeball Drone

A DJI Tello that follows my face and dodges a thrown soft ball, then goes back to following me.
Targets a gap Skydio documents: its obstacle avoidance does not detect moving objects.

Instructions: `/Users/srijan/Documents/Srijan Vault/Claude/Dodgeball Drone/Dodgeball Drone Instructions.md`

## Status

Current stage: Stage 0 done, scope set, Stage 1 in progress (code given, not yet run by me).

## Scope (decided 2026-11-15)

This is a separate project from the flyby project in `/Users/srijan/Documents/Flyby Change Detection/`. They have their own folders and their own git repos. Do not merge them.

Hardware: DJI Tello, laptop webcam, an iPhone with 240 fps slow-mo, soft balls. Extra cost target: about $0.

Tier A (the live demo): the Tello follows me and dodges a slow soft throw at 2 to 4 m, using frame-based tau. This does not use an event camera.

Tier B (the event comparison, offline): record throws at 7 to 10 m on 240 fps phone video. Emulate events from that video (v2e, and my own log-difference view). Compare frame-based tau against emulated-event expansion rate. Report which flags the ball earlier, by how many ms, and where each fails.

Tier C (stretch only): a real event camera on loan from a lab or mentor. Not planned. Real sensors cost EUR 1,400 to 2,900 and up.

Why the split: the Tello gives about 24 fps video with unmeasured delay (my own notes guess 200 to 400 ms) and a 54.5 degree field of view (one-point measurement). A 10 cm ball at 8 m is only about 6 px in radius (estimate), too small for tau. So 7 to 10 m throws are only tested offline on phone video.

Honest claim: a frame-based dodge pipeline on a $100 drone with measured latency, plus an offline measured comparison with emulated events. It does not prove that event cameras work for obstacle avoidance. Other labs have shown that. Emulated events from a 30 fps stream cannot beat the frame rate.

Out of scope: the ASC-2400 (toy drone, no computer control, no state feedback). It belongs to the flyby project only.

## Stage log

### Stage 0: grounding (done)

Environment (checked, not assumed):
- Python 3.14.7 at `python3`.
- `opencv-python` 5.0.0.93, `numpy` 2.5.3, `djitellopy` 2.5.0 all installed globally.
- Also installed: `opencv-contrib-python` 5.0.0.93 and `av` 18.1.0. Having both opencv-python and opencv-contrib-python is a known conflict risk. cv2 and av each ship `libavdevice`, which prints an `objc` duplicate-class warning on import. Harmless so far, but a possible cause of mysterious crashes with the webcam.
- The existing project has its own venv: `/Users/srijan/Documents/Projects/dronefollow/venv` (Python 3.14.7).
- `git` and `make` exist. `gh` does not.
- Webcam not tested yet.

Existing follower code (read, not flown):
- Location: `/Users/srijan/Documents/Projects/dronefollow` (NOT `/Users/srijan/Documents/dronefollow` as the vault note says; the note is stale).
- Library: `djitellopy` 2.5.0, OpenCV, laptop-side control over Tello Wi-Fi.
- Loop (`follow_tello.py`): 25 Hz. Read `frame_read.frame`, check if it is a new frame (`dronefollow/frame_timing.py`, object identity), detect target, `FollowController.update` gives a `Command`, `SafetySupervisor.update` gates it, then `tello.send_rc_control(*command.as_tuple())`.
- Control (`dronefollow/control.py`): PID per axis. Horizontal image error becomes YAW, not strafe. Target size becomes forward/back. Vertical error becomes up/down. Deadbands, and speed clamps (yaw 60, fb 30, ud 35). `left_right` is always 0 in follow mode.
- Safety (`dronefollow/safety.py`): states IDLE, SEARCHING, TRACKING, COASTING, LANDING. Lost target: hover 0.6 s, search, land after 6 s. Auto-land on low battery and max flight time.
- Stall guard: no new frame for 0.3 s means hover.
- Keys: `l`/`q` land, DELETE cuts motors.
- Detectors: ArUco marker (`follow_tello.py`), YOLO person/upper body (`follow_person.py`, 664 lines). No face detector found yet. Face follow for this project will need a face detector, to be decided at Stage 5.
- Status per my own notes: research prototype. Video stalls unresolved. No logged autonomous flight with current code. Reverse motion has no rear clearance guard.
- Measured: 24 fps, gaps up to 686 ms on a table run. Detection cost about 2.5 ms/frame (ArUco). Glass-to-glass latency never measured. The "200 to 400 ms" figure in the code is a claim, not a measurement.

Things that matter for this project:
1. Dodge needs the `left_right` channel, which the follower never uses. New territory.
2. Tello video at about 24 fps and 200 ms or more delay is tight against a 0.8 s tau threshold plus a 0.5 s sidestep. Measuring latency in Stage 4 is the make-or-break number.
3. Existing stall timeout is 0.3 s, stricter than the 1 s required here. Keep the stricter one.

Vault notes read: Skydio Coffee Chat, Autonomous Drone Focus Build Video, Autonomous Drone Follower Quick Context, Skydio Month Project (Looming Alarm, same tau math, hand-held only), Pan-Tilt PID Simulator Quick Context, TKS Drone Latency Essay Overview.

What I understood: not yet tested.
Still unclear: which face detector to use, whether the webcam works.

## Results table (fill with real numbers only)

| Measure | Value | Stage |
|---|---|---|
| Video latency (ms) | not measured | 4 |
| Trigger to motion (ms) | not measured | 4 |
| Tau error vs ground truth (ms) | not measured | 2 |
| Dodge success by speed and distance | not measured | 4 |
| False alarm rate while following | not measured | 5 |
| Frame vs event warning time (ms) | not measured | 6 |
