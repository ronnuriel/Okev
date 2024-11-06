from dronekit import connect, VehicleMode
import time
from pymavlink import mavutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("vehicle_data.log"),  # Log to a file
        logging.StreamHandler()                   # Log to the console
    ]
)
logger = logging.getLogger(__name__)

def set_raw_imu_stream_rate(vehicle, rate_hz=10):
    """
    Sets the stream rate for RAW_IMU messages.
    :param vehicle: DroneKit vehicle instance.
    :param rate_hz: The desired rate in Hz (e.g., 10 for 10 Hz).
    """
    vehicle._master.mav.request_data_stream_send(
        vehicle._master.target_system,
        vehicle._master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_RAW_SENSORS,  # Stream type for raw sensors
        rate_hz,
        1  # Start streaming
    )
    logger.info(f"Requested RAW_IMU stream at {rate_hz} Hz")

def set_gps_stream_rate(vehicle, rate_hz=1):
    """
    Sets the stream rate for GPS_RAW_INT messages.
    :param vehicle: DroneKit vehicle instance.
    :param rate_hz: The desired rate in Hz (e.g., 1 for 1 Hz).
    """
    vehicle._master.mav.request_data_stream_send(
        vehicle._master.target_system,
        vehicle._master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_POSITION,  # Stream type for GPS data
        rate_hz,
        1  # Start streaming
    )
    logger.info(f"Requested GPS_RAW_INT stream at {rate_hz} Hz")

def imu_callback(self, name, message):
    """
    Callback function to handle incoming RAW_IMU messages and print INS data.
    """
    # Accelerometer data in raw units (may vary based on autopilot)
    logger.info(f"Accelerometer: x={message.xacc}, y={message.yacc}, z={message.zacc}")

    # Gyroscope data in raw units
    logger.info(f"Gyroscope: x={message.xgyro}, y={message.ygyro}, z={message.zgyro}")

    # Magnetometer data in raw units
    logger.info(f"Magnetometer: x={message.xmag}, y={message.ymag}, z={message.zmag}")
    logger.info("-" * 50)

def gps_callback(self, name, message):
    """
    Callback function to handle incoming GPS_RAW_INT messages and print GPS data.
    """
    # GPS data in degrees and meters
    latitude = message.lat / 1e7  # Convert to degrees
    longitude = message.lon / 1e7  # Convert to degrees
    altitude = message.alt / 1e3  # Convert to meters

    logger.info(f"GPS Location: Latitude={latitude:.7f}, Longitude={longitude:.7f}, Altitude={altitude:.2f} meters")
    logger.info(f"Satellites Visible: {message.satellites_visible}, Fix Type: {message.fix_type}")
    logger.info("-" * 50)

def main():
    # Connect to the Vehicle
    connection_string = "udp:0.0.0.0:14551"  # Replace with your connection string
    logger.info(f'Connecting to vehicle on: {connection_string}')
    vehicle = connect(connection_string, wait_ready=True)

    try:
        logger.info("Connected to vehicle. Setting up data streams...")

        # Set stream rates for RAW_IMU and GPS_RAW_INT messages
        set_raw_imu_stream_rate(vehicle, rate_hz=50)
        set_gps_stream_rate(vehicle, rate_hz=1)

        # Add listeners for RAW_IMU and GPS_RAW_INT messages
        vehicle.add_message_listener('RAW_IMU', imu_callback)
        vehicle.add_message_listener('GPS_RAW_INT', gps_callback)

        # Keep the script running to listen to messages
        while True:
            logger.info(f"VEHICLE MODE: {vehicle.mode}")
            time.sleep(1)  # Adjust sleep time as needed

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")

    finally:
        # Ensure the vehicle is closed properly
        logger.info("Closing vehicle connection")
        vehicle.close()


if __name__ == "__main__":
    main()
