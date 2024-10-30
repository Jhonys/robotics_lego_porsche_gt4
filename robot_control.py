# robot_control.py

from flask import Flask, request, jsonify
import asyncio
import time
import signal
import sys
from LEGO_Technic_42176_XBOX_RC import TechnicMoveHub

app = Flask(__name__)
hub = None

# Expected ranges for POST data:
# speed: -100 to 100
# angle: -100 to 100
# lights: 0 to 1 (assuming binary state for lights, adjust if different)
@app.route('/drive', methods=['POST'])
async def drive():
    start_time = time.time()
    try:
        data = request.json
        speed = data.get('speed', 0)
        angle = data.get('angle', 0)
        lights = data.get('lights', 0)

        # Ensure values are within the range -100 to 100
        speed = max(-100, min(100, speed))
        angle = max(-100, min(100, angle))
        lights = max(0, min(1, lights))

        if hub is None:
            raise Exception("Hub is not initialized")
        await hub.drive(speed, angle, lights)
        response_time = time.time() - start_time
        print(f"/drive endpoint processed in {response_time:.4f} seconds")
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error in /drive endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/lights', methods=['POST'])
async def change_lights():
    start_time = time.time()
    try:
        data = request.json
        colorID = data.get('colorID', 0)
        if hub is None:
            raise Exception("Hub is not initialized")
        await hub.change_led_color(colorID)
        response_time = time.time() - start_time
        print(f"/lights endpoint processed in {response_time:.4f} seconds")
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error in /lights endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

async def main():
    global hub
    device_name = "Technic Move"  # Replace with your BLE device's name
    hub = TechnicMoveHub(device_name)
    if not await hub.scan_and_connect():
        print("Technic hub not found!")
        return

    await hub.calibrate_steering()
    print("Hub connected and calibrated")
    app.run(host='0.0.0.0', port=5000)  # Ensure the server is listening on all interfaces

def signal_handler(sig, frame):
    print("Interrupt received, stopping...")
    if hub is not None:
        asyncio.run(hub.disconnect())
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())