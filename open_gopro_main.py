import asyncio
import cv2
from open_gopro import WirelessGoPro, Params
from open_gopro.constants import WebcamError, WebcamStatus
from open_gopro.gopro_base import GoProBase
from open_gopro.logger import setup_logging

STREAM_URL = r"udp://127.0.0.1:8554"

async def wait_for_webcam_status(gopro: GoProBase, statuses: set[WebcamStatus], timeout: int = 10) -> bool:
    async def poll_for_status() -> bool:
        while True:
            response = (await gopro.http_command.webcam_status()).data
            if response.error != WebcamError.SUCCESS:
                print(f"Received webcam error: {response.error}")
                return False
            if response.status in statuses:
                return True

    try:
        return await asyncio.wait_for(poll_for_status(), timeout)
    except TimeoutError:
        return False

async def main():
    logger = setup_logging(__name__, "INFO")
    gopro: GoProBase | None = None

    try:
        async with WirelessGoPro(target="GoPro 9407", sudo_password="3Nj-P4Q-NN4") as gopro:
            assert gopro
            cohn = False

            if cohn:
                assert await gopro.is_cohn_provisioned
                assert await gopro.configure_cohn()
            else:
                await gopro.http_command.wired_usb_control(control=Params.Toggle.DISABLE)

            print("Created Gopro")

            await gopro.http_command.set_shutter(shutter=Params.Toggle.DISABLE)
            if (await gopro.http_command.webcam_status()).data.status not in {WebcamStatus.OFF, WebcamStatus.IDLE}:
                print("Webcam is currently on. Turning it off.")
                assert (await gopro.http_command.webcam_stop()).ok
                await wait_for_webcam_status(gopro, {WebcamStatus.OFF})

            print("Starting webcam...")
            if (status := (await gopro.http_command.webcam_start()).data.error) != WebcamError.SUCCESS:
                print(f"Couldn't start webcam: {status}")
                return

            await wait_for_webcam_status(gopro, {WebcamStatus.HIGH_POWER_PREVIEW})

            cap = cv2.VideoCapture(STREAM_URL)
            if not cap.isOpened():
                print("Error: Couldn't open video stream.")
                return

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break

                cv2.imshow('GoPro Webcam', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()

            print("Stopping webcam...")
            assert (await gopro.http_command.webcam_stop()).ok
            await wait_for_webcam_status(gopro, {WebcamStatus.OFF, WebcamStatus.IDLE})
            assert (await gopro.http_command.webcam_exit()).ok
            await wait_for_webcam_status(gopro, {WebcamStatus.OFF})
            print("Exiting...")

    except Exception as e:
        logger.error(repr(e))

    if gopro:
        await gopro.close()

if __name__ == "__main__":
    asyncio.run(main())