import pygame
import aiohttp
import asyncio
import time

def normalize(value):
    if value == 0:
        return 0
    else:
        return (-value + 1)/2

def ease_in_quad(x: float) -> float:
    return x ** 2

def get_left_joystick(joystick):
    x = round(joystick.get_axis(0)*100)
    y = -round(joystick.get_axis(1)*100)
    return (x,y)

def get_right_joystick(joystick):
    x = round(joystick.get_axis(2)*100)
    y = -round(joystick.get_axis(3)*100)
    return (x,y)

def get_steering_wheel(joystick):
    steering = joystick.get_axis(0)
    accelerator_pedal = normalize(joystick.get_axis(1))
    break_pedal = normalize(joystick.get_axis(2))

    if break_pedal > 0.1:
        throttle = -ease_in_quad(break_pedal)
    else:
        throttle = ease_in_quad(accelerator_pedal)
        
    return round(steering*100), round(throttle*100)

def get_Y_button(joystick):
    return joystick.get_button(3)

def get_right_bumper(joystick):
    return joystick.get_button(5)

def get_sound_button(joystick):
    return joystick.get_button(4)  # Assuming button 4 is used for playing sounds

async def send_request(session, url, json_data):
    async with session.post(url, json=json_data) as response:
        return await response.text()

async def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No joystick found")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    
    print(f"Joystick name: {joystick.get_name()}")

    lights = 0
    toggle_old = False
    throttle_old = 0
    steering_old = 0
    lights_old = 0
    was_brake = False

    async with aiohttp.ClientSession() as session:
        try:
            while True:
                pygame.event.pump()

                # steering, throttle = get_steering_wheel(joystick)
                throttle = get_right_joystick(joystick)[1]
                steering = get_left_joystick(joystick)[0]

                # Ensure values are within the range 0 to 100
                # throttle = max(0, min(100, throttle))
                # steering = max(0, min(100, steering))

                brake = get_right_bumper(joystick)
                toggle = get_Y_button(joystick)
                sound_button = get_sound_button(joystick)
                
                if toggle and not toggle_old:
                    if lights == 0:
                        print("lights on")
                        lights = 1
                    else:
                        print("lights off")
                        lights = 0
                toggle_old = toggle

                if brake and not was_brake:
                    joystick.rumble(0.0, 0.3, 300)
                    await send_request(session, 'http://127.0.0.1:5000/drive', {"speed": 0, "angle": steering, "lights": 1})
                    time.sleep(0.4)
                    throttle = 0
                    throttle_old = 0

                if not brake and was_brake:
                    await send_request(session, 'http://127.0.0.1:5000/drive', {"speed": throttle, "angle": steering, "lights": lights})

                was_brake = brake

                # Send request only if there are significant changes
                if abs(steering - steering_old) > 2 or abs(throttle - throttle_old) > 2 or lights != lights_old:
                    print("throttle", throttle, "steering", steering)
                    await send_request(session, 'http://127.0.0.1:5000/drive', {"speed": throttle, "angle": steering, "lights": lights})

                if sound_button:
                    await send_request(session, 'http://127.0.0.1:5000/sounds', {"soundID": 1})  # Example sound ID

                throttle_old = throttle
                steering_old = steering
                lights_old = lights

                await asyncio.sleep(0.1)  # Adjust the sleep time to reduce the frequency of requests

        except KeyboardInterrupt:
            pass
        finally:
            pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())