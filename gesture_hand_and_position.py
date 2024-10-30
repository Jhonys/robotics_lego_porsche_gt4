import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import aiohttp
import asyncio

# Initialize MediaPipe Hands and Drawing Utilities
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Initialize Gesture Recognizer
base_options = python.BaseOptions(model_asset_path='gesture_recognizer.task', delegate=python.BaseOptions.Delegate.CPU)
options = vision.GestureRecognizerOptions(base_options=base_options)
recognizer = vision.GestureRecognizer.create_from_options(options)

# Initialize Hands for position detection
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,
                       min_detection_confidence=0.5,
                       min_tracking_confidence=0.5)

def detectAndProcessGesture(image):
    # Convert the BGR image to RGB for gesture recognition
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_rgb = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    
    # Process the image and detect gestures
    results = recognizer.recognize(image_rgb)
    horizontal = 0 # center
    vertical = 0 # stop
    sound = False # no sound

    if len(results.gestures) > 0:
        top_gesture = results.gestures[0][0]
        if top_gesture:
            gesture = top_gesture.category_name
            if gesture == "Pointing_Up":
                vertical = -1 # forward
            elif gesture == "Victory":
                vertical = 1 # backward
            elif gesture == "Thumb_Down":
                horizontal = -1 # left
            elif gesture == "Thumb_Up":
                horizontal = 1 # right
            elif gesture == "Open_Palm":
                vertical = 0 # stop
            elif gesture == "ILoveYou":
                sound = True

    return horizontal, vertical, sound

async def infoProtocol(session, horizontal, vertical):
    # horizontal = -1 left, 0 center, 1 right
    # vertical = -1 forward, 0 stop, 1 backward

    # Send the command to the robot control endpoint
    try:
        async with session.post('http://localhost:5000/drive', json={
            'speed': vertical * 100,  # Assuming speed is controlled by vertical gesture
            'angle': horizontal * 100  # Assuming angle is controlled by horizontal position
        }) as response:
            if response.status == 200:
                print("Drive command sent successfully")
            else:
                print(f"Failed to send drive command: {response.status}")
    except Exception as e:
        print(f"Error sending drive command: {e}")

async def sendSoundCommand(session):
    # Send the sound command to the robot control endpoint
    try:
        async with session.post('http://localhost:5000/sounds', json={
            'soundID': 1  # Example sound ID
        }) as response:
            if response.status == 200:
                print("Sound command sent successfully")
            else:
                print(f"Failed to send sound command: {response.status}")
    except Exception as e:
        print(f"Error sending sound command: {e}")

def getHorizontalPositionHand(image):
    # Convert the BGR image to RGB for position detection
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Process the RGB image
    results = hands.process(image_rgb)
    
    # Get image width
    image_width = image.shape[1]
    
    # Divide the horizontal axis of the image into three parts
    left_boundary = image_width // 3
    right_boundary = left_boundary * 2
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw the hand annotations on the image.
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Get the x coordinate of the wrist (landmark 0)
            wrist_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x * image_width
            
            # Determine the hand position
            if wrist_x < left_boundary:
                return -1 # left
            elif wrist_x > right_boundary:
                return 1 # right
            else:
                return 0 # center - rotation stops
    else:
        return 0 # center - rotation stops

async def main():
    cap = cv2.VideoCapture(1)
    previous_command = None

    async with aiohttp.ClientSession() as session:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Process each frame for both gesture and position
            horizontal, vertical, sound = detectAndProcessGesture(image)

            # Determine the command to send based on the detected gesture
            if vertical != 0:
                command = ('vertical', vertical)
            elif horizontal != 0:
                command = ('horizontal', horizontal)
            else:
                command = ('stop', 0)

            # Check if the command has changed
            if command != previous_command:
                if command[0] == 'vertical':
                    await infoProtocol(session, 0, command[1])
                elif command[0] == 'horizontal':
                    await infoProtocol(session, command[1], 0)
                elif command[0] == 'stop':
                    await infoProtocol(session, 0, 0)
                previous_command = command

            # Send sound command if sound gesture is detected
            if sound:
                await sendSoundCommand(session)

            # Display the processed image
            cv2.imshow('Hand Recognition', image)
            if cv2.waitKey(5) & 0xFF == 27:  # Press 'ESC' to exit
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(main())