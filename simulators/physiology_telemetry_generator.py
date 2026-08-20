import os
import time
import random
import math
from datetime import datetime
import requests

# Gateway Config
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000/api/v1/telemetry")
USER_ID = "subject_alpha"
POST_INTERVAL_SECONDS = 2  # Send a telemetry payload every 2 seconds

class PhysiologySimulator:
    """
    Simulates human biological signals with realistic drift, continuous step accumulation,
    and correlated physiological changes (e.g., higher HR drops HRV).
    """
    def __init__(self):
        # Baseline physical state
        self.base_hr = 72.0       # Resting heart rate (BPM)
        self.current_hr = 72.0
        self.base_hrv = 55.0      # Baseline HRV (ms)
        self.total_steps = 3420   # Accumulated daily step count
        self.spo2 = 98.5          # Blood oxygen saturation (%)
        
        # State modifiers
        self.activity_state = "resting"  # "resting", "walking", "exertion"
        self.state_counter = 0

    def _update_state(self):
        """Randomly transitions between physical activity states to test LLM prompt adaptation."""
        self.state_counter += 1
        if self.state_counter > 15:  # Shift states every ~30 seconds of simulation
            self.state_counter = 0
            states = ["resting", "resting", "walking", "exertion"]
            self.activity_state = random.choice(states)
            print(f"\n---> [SIMULATOR STATE SHIFT] Transitioned to: {self.activity_state.upper()} <---")

    def tick(self) -> dict:
        """Calculates next biological state and returns payload."""
        self._update_state()

        # 1. Heart Rate dynamics based on physical state
        if self.activity_state == "resting":
            target_hr = self.base_hr + random.uniform(-3, 3)
            step_increment = 0
        elif self.activity_state == "walking":
            target_hr = 95.0 + random.uniform(-5, 10)
            step_increment = random.randint(2, 5)
        else:  # "exertion"
            target_hr = 140.0 + random.uniform(-10, 20)
            step_increment = random.randint(8, 15)

        # Smooth transition toward target heart rate (Inertia)
        self.current_hr += (target_hr - self.current_hr) * 0.2
        self.total_steps += step_increment

        # 2. HRV (Inverse relationship with Heart Rate: higher HR = lower HRV)
        hr_delta = max(0.0, self.current_hr - self.base_hr)
        hrv_penalty = hr_delta * 0.4
        current_hrv = max(12.0, self.base_hrv - hrv_penalty + random.uniform(-4, 4))

        # 3. SpO2 with slight physical variance
        if self.activity_state == "exertion":
            current_spo2 = max(94.0, min(100.0, self.spo2 - random.uniform(0.1, 0.4)))
        else:
            current_spo2 = max(96.0, min(100.0, self.spo2 + random.uniform(-0.2, 0.2)))

        return {
            "user_id": USER_ID,
            "heart_rate": round(self.current_hr, 1),
            "hrv_ms": round(current_hrv, 1),
            "step_count": self.total_steps,
            "spo2": round(current_spo2, 1)
        }

def run_simulation():
    simulator = PhysiologySimulator()
    print(f"Starting Biological Telemetry Stream Generator...")
    print(f"Target Gateway: {GATEWAY_URL}")
    print(f"Press CTRL+C to stop.\n")

    while True:
        payload = simulator.tick()
        try:
            response = requests.post(GATEWAY_URL, json=payload, timeout=3)
            if response.status_code in (200, 201):
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(
                    f"[{timestamp}] Sent -> HR: {payload['heart_rate']} BPM | "
                    f"HRV: {payload['hrv_ms']} ms | "
                    f"Steps: {payload['step_count']} | "
                    f"SpO2: {payload['spo2']}%"
                )
            else:
                print(f"[ERROR] Gateway responded with status {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"[CONNECTION ERROR] Failed to reach telemetry gateway: {e}")

        time.sleep(POST_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_simulation()
