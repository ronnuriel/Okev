import csv
import time
import argparse
import pygame
from datetime import datetime
from dronekit import connect, VehicleMode

# Channel mappings for Arduplane
Roll = 1
Pitch = 2
Throttle = 3
Yaw = 4

# Neutral PWM value
NEUTRAL_PWM = 1500

# Rate factors initialized to 0
ROLL_RATE_FACTOR = 0
YAW_RATE_FACTOR = 0
PITCH_RATE_FACTOR = 0

# Control parameter defaults
control_params = {Pitch: NEUTRAL_PWM, Yaw: NEUTRAL_PWM, Throttle: NEUTRAL_PWM, Roll: NEUTRAL_PWM}

# Initialize CSV file for telemetry data
csv_file = open("telemetry_log.csv", mode="w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["time", "vehicle_mode", "pitch", "yaw", "roll", "throttle", "command_sent"])


def log_to_csv(vehicle, pitch=None, yaw=None, roll=None, throttle=None, command=""):
    """
    Logs the current vehicle mode, pitch, yaw, roll, and throttle to the CSV file.
    """
    csv_writer.writerow([
        datetime.now(),
        vehicle.mode.name,
        pitch if pitch is not None else control_params[Pitch],
        yaw if yaw is not None else control_params[Yaw],
        roll if roll is not None else control_params[Roll],
        throttle if throttle is not None else control_params[Throttle],
        command
    ])


def parse_arguments():
    parser = argparse.ArgumentParser(description='Commands Arduplane using waypoints.')
    parser.add_argument('--connect', help="Vehicle connection target string.")
    parser.add_argument('--test', action='store_true', help="Perform a test of pitch, yaw, and roll channels.")
    return parser.parse_args()


def arm_and_takeoff(vehicle):
    print("Basic pre-arm checks")
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")
    vehicle.mode = VehicleMode("AUTO")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Vehicle armed. Takeoff handled in AUTO mode.")


def calculate_roll_pwm(degree_per_second):
    roll_left = NEUTRAL_PWM - (degree_per_second * ROLL_RATE_FACTOR)
    roll_right = NEUTRAL_PWM + (degree_per_second * ROLL_RATE_FACTOR)
    return int(roll_left), int(roll_right)


def calculate_yaw_pwm(degree_per_second):
    yaw_left = NEUTRAL_PWM - (degree_per_second * YAW_RATE_FACTOR)
    yaw_right = NEUTRAL_PWM + (degree_per_second * YAW_RATE_FACTOR)
    return int(yaw_left), int(yaw_right)


def calculate_pitch_pwm(degree_per_second):
    pitch_down = NEUTRAL_PWM - (degree_per_second * PITCH_RATE_FACTOR)
    pitch_up = NEUTRAL_PWM + (degree_per_second * PITCH_RATE_FACTOR)
    return int(pitch_down), int(pitch_up)


def ground_control_response_test(vehicle, control_channel, pwm_change):
    """
    Tests if the control channel responds on the ground by changing the PWM and observing the actual response.
    """
    print(f"Testing {control_channel} control channel response on the ground...")

    # Apply an incremental change to the control channel
    expected_pwm = NEUTRAL_PWM + pwm_change
    vehicle.channels.overrides[control_channel] = expected_pwm
    time.sleep(1)  # Wait briefly to allow response

    # Record actual PWM value if available (some flight controllers may not report this)
    actual_pwm = vehicle.channels[control_channel]
    log_to_csv(vehicle, control_channel=control_channel, expected_pwm=expected_pwm, actual_pwm=actual_pwm,
               command=f"{control_channel} test - PWM {pwm_change}")

    # Reset to neutral
    vehicle.channels.overrides[control_channel] = None
    time.sleep(1)


def ground_tests(vehicle):
    """
    Perform initial ground tests to verify sensor and basic control functionality.
    """
    print("Starting ground tests...")

    # 1. Check GPS lock status
    if vehicle.gps_0.fix_type < 2:
        print("Warning: GPS fix not stable. Ensure GPS lock before proceeding.")
        log_to_csv(vehicle, command="GPS fix warning")

    # 2. Check battery status
    if vehicle.battery.voltage is None or vehicle.battery.level is None:
        print("Battery status unavailable!")
    else:
        print(f"Battery voltage: {vehicle.battery.voltage}V, Battery level: {vehicle.battery.level}%")
        log_to_csv(vehicle,
                   command=f"Battery check - Voltage: {vehicle.battery.voltage}, Level: {vehicle.battery.level}%")

    # 3. Verify control channel responses
    print("Testing control channels for response...")
    ground_control_response_test(vehicle, Pitch, 100)
    ground_control_response_test(vehicle, Yaw, 100)
    ground_control_response_test(vehicle, Roll, 100)
    ground_control_response_test(vehicle, Throttle, 100)

    log_to_csv(vehicle, command="Control channel check complete")

    print("Ground tests complete. Ready for main tests.")


def test_roll(vehicle, degree_per_second):
    roll_left, roll_right = calculate_roll_pwm(degree_per_second)
    print("Testing roll channel Wait for stabilization mode")
    while vehicle.mode.name != "STABILIZE":
        time.sleep(1)
    time.sleep(5)
    vehicle.mode = VehicleMode("ACRO")
    log_to_csv(vehicle, roll=roll_left, command="Roll test - left")
    vehicle.channels.overrides[Roll] = roll_left
    time.sleep(5)
    vehicle.channels.overrides[Roll] = roll_right
    log_to_csv(vehicle, roll=roll_right, command="Roll test - right")
    time.sleep(3)
    vehicle.channels.overrides[Roll] = None
    vehicle.channels.overrides[Throttle] = None
    log_to_csv(vehicle, command="Roll test complete")


def test_yaw(vehicle, degree_per_second):
    yaw_left, yaw_right = calculate_yaw_pwm(degree_per_second)
    print("Testing yaw channel Wait for stabilization mode")
    while vehicle.mode.name != "STABILIZE":
        time.sleep(1)
    time.sleep(5)
    vehicle.mode = VehicleMode("ACRO")
    log_to_csv(vehicle, yaw=yaw_left, command="Yaw test - left")
    vehicle.channels.overrides[Yaw] = yaw_left
    time.sleep(5)
    vehicle.channels.overrides[Yaw] = yaw_right
    log_to_csv(vehicle, yaw=yaw_right, command="Yaw test - right")
    time.sleep(3)
    vehicle.channels.overrides[Yaw] = None
    vehicle.channels.overrides[Throttle] = None
    log_to_csv(vehicle, command="Yaw test complete")


def test_pitch(vehicle, degree_per_second):
    pitch_down, pitch_up = calculate_pitch_pwm(degree_per_second)
    print("Testing pitch channel Wait for stabilization mode")
    while vehicle.mode.name != "STABILIZE":
        time.sleep(1)
    time.sleep(5)
    vehicle.mode = VehicleMode("ACRO")
    log_to_csv(vehicle, pitch=pitch_down, command="Pitch test - down")
    vehicle.channels.overrides[Pitch] = pitch_down
    time.sleep(5)
    vehicle.channels.overrides[Pitch] = pitch_up
    log_to_csv(vehicle, pitch=pitch_up, command="Pitch test - up")
    time.sleep(3)
    vehicle.channels.overrides[Pitch] = None
    vehicle.channels.overrides[Throttle] = None
    log_to_csv(vehicle, command="Pitch test complete")


def main():
    args = parse_arguments()
    connection_string = args.connect
    sitl = None

    if not connection_string:
        import dronekit_sitl
        sitl = dronekit_sitl.SITL()
        sitl.download('plane', version='stable')
        sitl_args = ['--model', 'plane', '--out', 'udp:127.0.0.1:14550']
        sitl.launch(sitl_args, await_ready=True, restart=True)
        connection_string = 'udp:127.0.0.1:14550'

    print(f'Connecting to vehicle on: {connection_string}')
    vehicle = connect(connection_string, wait_ready=True)

    try:
        # Perform ground tests
        ground_tests(vehicle)

        pitch_rate = vehicle.parameters.get('ACRO_PITCH_RATE', None)
        yaw_rate = vehicle.parameters.get('ACRO_YAW_RATE', None)
        roll_rate = vehicle.parameters.get('ACRO_ROLL_RATE', None)

        global ROLL_RATE_FACTOR, YAW_RATE_FACTOR, PITCH_RATE_FACTOR
        ROLL_RATE_FACTOR = 500 / roll_rate if roll_rate else 1
        YAW_RATE_FACTOR = 500 / yaw_rate if yaw_rate else 1
        PITCH_RATE_FACTOR = 500 / pitch_rate if pitch_rate else 1

        if args.test:
            test_roll(vehicle, 20)
            vehicle.mode = VehicleMode("STABILIZE")
            time.sleep(5)
            test_pitch(vehicle, 15)
            vehicle.mode = VehicleMode("STABILIZE")
            time.sleep(5)
            test_yaw(vehicle, 30)

        else:
            vehicle.mode = VehicleMode("AUTO")
            log_to_csv(vehicle, command="Starting in AUTO mode")

    finally:
        vehicle.mode = VehicleMode("RTL")
        log_to_csv(vehicle, command="RTL mode activated")
        vehicle.close()
        csv_file.close()

        if sitl:
            sitl.stop()
        pygame.quit()
        print("Completed")


if __name__ == "__main__":
    main()
