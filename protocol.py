from enum import Enum
from itertools import product
import random

class Throttle(Enum):
    LOW = 10
    MEDIUM = 50
    HIGH = 100

class Steering(Enum):
    LEFT = -10
    STRAIGHT = 0
    RIGHT = 10

class Lights(Enum):
    ON = "lights_on"
    OFF = "lights_off"

class Direction(Enum):
    FORWARD = "forward"
    REVERSE = "reverse"

class Sound(Enum):
    BEEP = "beep"
    HORN = "horn"
    MUSIC = "music"
    RANDOM = "random"

def play_sound(sound):
    if sound == Sound.RANDOM:
        sound = random.choice(list(Sound)[:-1])  # Exclude RANDOM from choices
    return {
        "action": "play_sound",
        "parameters": {
            "sound": sound.value
        }
    }

def generate_combinations():
    combinations = product(Throttle, Steering, Lights, Direction)
    for throttle, steering, lights, direction in combinations:
        yield {
            "action": "drive",
            "parameters": {
                "throttle": throttle.value,
                "steering": steering.value,
                "lights": lights.value,
                "direction": direction.value
            }
        }

# Test all combinations
for combination in generate_combinations():
    print(combination)

# Test play_sound with specific and random sounds
print(play_sound(Sound.BEEP))
print(play_sound(Sound.RANDOM))