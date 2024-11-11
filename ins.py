from dronekit import connect, VehicleMode
import time
from pymavlink import mavutil
import logging
import csv
from datetime import datetime

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

# Initialize CSV file for telemetry data
csv_file = open("telemetry_log.csv", mode="w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["time", "vehicle_mode", "yaw", "pitch", "throttle", "latitude", "longitude", "altitude", "command_sent"])

def set_raw_imu_stream_rate(vehicle, rate_hz=10):
    vehicle._master.mav.request_data_stream_send(
        vehicle._master.target_system,
        vehicle._master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_RAW_SENSORS,  # Stream type for raw sensors
        rate_hz,
        1  # Start streaming
    )
    logger.info(f"Requested RAW_IMU stream at {rate_hz} Hz")

def set_gps_stream_rate(vehicle, rate_hz=1):
    vehicle._master.mav.request_data_stream_send(
        vehicle._master.target_system,
        vehicle._master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_POSITION,  # Stream type for GPS data
        rate_hz,
        1  # Start streaming
    )
    logger.info(f"Requested GPS_RAW_INT stream at {rate_hz} Hz")

def imu_callback(self, name, message):
    # Extract yaw, pitch, and throttle data
    yaw = message.zgyro
    pitch = message.xgyro
    throttle = 1500  # Placeholder, replace with actual throttle if available
    mode = self.mode.name  # Capture the current vehicle mode

    # Log to CSV
    csv_writer.writerow([datetime.now(), mode, yaw, pitch, throttle, "", "", "", "IMU data"])

def gps_callback(self, name, message):
    # Extract GPS data
    latitude = message.lat / 1e7  # Convert to degrees
    longitude = message.lon / 1e7  # Convert to degrees
    altitude = message.alt / 1e3  # Convert to meters
    mode = self.mode.name  # Capture the current vehicle mode

    # Log to CSV
    csv_writer.writerow([datetime.now(), mode, "", "", "", latitude, longitude, altitude, "GPS data"])

def main():
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
            # Capture the vehicle mode and any command sent
            mode = vehicle.mode.name
            command_sent = ""  # Placeholder for commands if sent in the future
            csv_writer.writerow([datetime.now(), mode, "", "", "", "", "", "", f"Mode: {mode}, Command: {command_sent}"])
            logger.info(f"VEHICLE MODE: {mode}")
            time.sleep(1)  # Adjust sleep time as needed

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")

    finally:
        logger.info("Closing vehicle connection")
        vehicle.close()
        csv_file.close()


if __name__ == "__main__":
    main()
