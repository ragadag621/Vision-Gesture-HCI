# 🖐️ GestureSense OS: Advanced AI-Powered System Controller

[![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen)]()
[![AI-Model](https://img.shields.io/badge/AI-MediaPipe-blue)]()
[![Vision](https://img.shields.io/badge/Vision-OpenCV-orange)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%2F%20Linux-lightgrey)]()

An advanced Human-Computer Interaction (HCI) system that bridges the gap between AI perception and OS-level execution. This project is not just a script; it's a full-cycle engineering effort from real-time landmark inference to adaptive signal processing for system control.

https://s2.ezgif.com/tmp/ezgif-2fecfe1e7e6d0474.gif


## 🏗️ Engineering Lifecycle & Effort

This system was built through a rigorous 4-stage engineering process, ensuring high fidelity and low latency:

### 1. Perceptual Engineering (Inference)
* **Real-time Landmark Mapping**: Utilizing MediaPipe's sub-millimeter tracking to map 21 hand joints.
* **Handedness Auto-Correction**: A proprietary logic layer that dynamically adapts to **Left/Right** hand orientation to ensure consistent gesture interpretation.

### 2. Signal Processing (Logic)
* **Adaptive Interpolation**: Using `numpy.interp` to map non-linear physical hand distances into linear system volume decibels.
* **Temporal Stability**: Integrated a state-change monitor to prevent command flickering and ensure a smooth User Experience (UX).

### 3. User Interface (OSD)
* **Real-time Dashboard**: Dynamic On-Screen Display (OSD) providing immediate feedback on system status and finger classification.
* **Visual Anchoring**: Graphical cues (Volume bars, Laser trails) designed to minimize cognitive load on the user.

---

## 🔥 Key Functionalities

| Feature | Gesture Logic | System Impact |
| :--- | :--- | :--- |
| **Precision Volume** | Euclidean distance (Thumb-Index) | Adaptive Audio Gain |
| **Laser Pointer** | Single-point tracking (Index tip) | Interactive Visual OSD |
| **Stealth Mode** | Closed Fist detection | Instant System Mute |
| **Safety Exit** | 5-Finger palm hold (5000ms) | Graceful Process Termination |


---

## 🚀 Quick Start & Deployment

1. **Environment Setup**:
   ```bash
   pip install -r requirements.txt
