# joystick_module.py
import pygame
from fastapi import FastAPI
from pydantic import BaseModel
import threading
import time
import random
from enum import Enum
from itertools import product

app = FastAPI()

joystick_values = {
    'steering': 0,
    'accelerator_pedal': 0,
    'A_button': 0,
    'B_button': 0,
    'X_button': 0,
    'Y_button': 0,
    'left_bumper': 0,
    'right_bumper': 0
}

def init_joystick():
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        raise Exception("No joystick found")
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    return joystick

def update_joystick_values(joystick):
    global joystick_values
    while True:
        pygame.event.pump()  # Update joystick state
        joystick_values = {
            'steering': joystick.get_axis(0),  # Left stick horizontal axis
            'accelerator_pedal': joystick.get_axis(5),  # Right trigger
            'A_button': joystick.get_button(0),  # A button
            'B_button': joystick.get_button(1),  # B button
            'X_button': joystick.get_button(2),
            'Y_button': joystick.get_button(3),
            'left_bumper': joystick.get_button(4),
            'right_bumper': joystick.get_button(5)
        }
        time.sleep(0.1)  # Adjust the sleep time as needed

joystick = init_joystick()
joystick_thread = threading.Thread(target=update_joystick_values, args=(joystick,))
joystick_thread.daemon = True
joystick_thread.start()

class Throttle(Enum):
    LOW = 10
    MEDIUM = 50
    HIGH = 100

class Steering(Enum):
    LEFT = -10
    STRAIGHT = 0
    RIGHT = 10

class Direction(Enum):
    FORWARD = "forward"
    REVERSE = "reverse"

class Sound(Enum):
    BEEP = "beep"
    HORN = "horn"
    MUSIC = "music"
    RANDOM = "random"

class Command(BaseModel):
    action: str
    parameters: dict

def play_sound(sound: Sound) -> Command:
    if sound == Sound.RANDOM:
        sound = random.choice(list(Sound)[:-1])  # Exclude RANDOM from choices
    return Command(
        action="play_sound",
        parameters={
            "sound": sound.value
        }
    )

def generate_drive_command(steering: int, throttle: int, direction: str, lights: str) -> Command:
    return Command(
        action="drive",
        parameters={
            "throttle": throttle,
            "steering": steering,
            "direction": direction,
            "lights": lights
        }
    )

@app.get("/joystick")
def get_joystick_values():
    return joystick_values

@app.get("/command")
def get_command():
    steering_value = joystick_values['steering']
    throttle_value = joystick_values['accelerator_pedal']
    a_button = joystick_values['A_button']
    b_button = joystick_values['B_button']
    
    # Map joystick values to protocol values
    if steering_value < -0.5:
        steering = Steering.LEFT.value
    elif steering_value > 0.5:
        steering = Steering.RIGHT.value
    else:
        steering = Steering.STRAIGHT.value
    
    if throttle_value > 0.5:
        throttle = Throttle.HIGH.value
        direction = Direction.FORWARD.value
    elif throttle_value < -0.5:
        throttle = Throttle.HIGH.value
        direction = Direction.REVERSE.value
    else:
        throttle = Throttle.LOW.value
        direction = Direction.FORWARD.value
    
    lights = "lights_on" if a_button else "lights_off"
    
    command = generate_drive_command(steering, throttle, direction, lights)
    
    if b_button:
        sound_command = play_sound(Sound.BEEP)  # You can change the sound type as needed
        return {"drive_command": command, "sound_command": sound_command}
    
    return command

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)