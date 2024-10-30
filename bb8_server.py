import time
import os
import asyncio
import signal
import sys
from flask import Flask, request, jsonify
from bleak import BleakError
from droiddepot.connection import DroidConnection, discover_droid
from droiddepot.motor import DroidMotorDirection, DroidMotorIdentifier

app = Flask(__name__)
droid = None

def calculate_motor_speeds(speed, angle):
    base_speed = int(speed)
    left_speed = base_speed
    right_speed = base_speed

    if angle > 0:
        left_speed -= int(angle)
        right_speed += int(angle)
    elif angle < 0:
        left_speed += int(abs(angle))
        right_speed -= int(abs(angle))

    left_speed = max(min(left_speed, 100), -100)
    right_speed = max(min(right_speed, 100), -100)

    return left_speed, right_speed

def normalize_values_to_motor(left_speed, right_speed):
    left_speed = int(left_speed * 1.6)
    right_speed = int(right_speed * 1.6)
    return abs(left_speed), abs(right_speed)

@app.route('/drive', methods=['POST'])
async def drive():
    start_time = time.time()
    try:
        data = request.json
        speed = data.get('speed', 0)
        angle = data.get('angle', 0)

        # Ensure values are within the range -100 to 100
        speed = max(-100, min(100, speed))
        angle = max(-100, min(100, angle))

        if droid is None:
            raise Exception("Droid is not initialized")

        left_speed, right_speed = calculate_motor_speeds(speed, angle)
        direction_map = {
            True: DroidMotorDirection.Forward,
            False: DroidMotorDirection.Backwards
        }
        direction_left = direction_map[left_speed < 0]
        direction_right = direction_map[right_speed < 0]

        left_speed, right_speed = normalize_values_to_motor(left_speed, right_speed)

        await droid.motor_controller.set_motor_speed(direction_left, DroidMotorIdentifier.LeftMotor, left_speed, 300)
        await droid.motor_controller.set_motor_speed(direction_right, DroidMotorIdentifier.RightMotor, right_speed, 300)

        response_time = time.time() - start_time
        print(f"/drive endpoint processed in {response_time:.4f} seconds")
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error in /drive endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/sounds', methods=['POST'])
async def play_sound():
    start_time = time.time()
    try:
        data = request.json
        soundID = data.get('soundID', 0)
        if droid is None:
            raise Exception("Droid is not initialized")
        await droid.audio_controller.play_audio(soundID, 1, True, 100)
        response_time = time.time() - start_time
        print(f"/sounds endpoint processed in {response_time:.4f} seconds")
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error in /sounds endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

async def main():
    global droid
    droid = await discover_droid(retry=True)

    try:
        async with droid as d:
            d: DroidConnection = d

            if not d.droid.is_connected:
                print("Droid not connected!")
                return

            app.run(host='0.0.0.0', port=5000)  # Ensure the server is listening on all interfaces
            
    except OSError as err:
        print(f"Discovery failed due to operating system: {err}")
    except BleakError as err:
        print(f"Discovery failed due to Bleak: {err}")
    except KeyboardInterrupt as err:
        pass
    finally:
        print("Shutting down.")

def signal_handler(sig, frame):
    print("Interrupt received, stopping...")
    if droid is not None:
        asyncio.run(droid.disconnect())
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())