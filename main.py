# -*- coding: utf-8 -*-
"""
Adapted for Arduplane with optional RTL (Return to Launch), ACRO mode with keyboard control, and mode switching.
"""

from dronekit import connect, VehicleMode
import time
import argparse
import pygame

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

def parse_arguments():
    parser = argparse.ArgumentParser(description='Commands Arduplane using waypoints.')
    parser.add_argument('--connect', help="Vehicle connection target string.")
    parser.add_argument('--rtl', action='store_true', help="Return to launch at the end of the mission.")
    parser.add_argument('--acro', action='store_true', help="Start in ACRO mode with keyboard control.")
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

def initialize_keyboard():
    """
    Initializes pygame to capture keyboard events.
    """
    pygame.init()
    pygame.display.set_mode((100, 100))  # Creates a small window
    print("Keyboard initialized for control input.")

def update_control_params_from_keyboard(vehicle):
    """
    Reads keyboard input and updates global control parameters and mode switching.
    Resets to NEUTRAL_PWM when keys are not pressed.
    """
    global control_params

    # Start with neutral values
    control_params[Pitch] = NEUTRAL_PWM
    control_params[Yaw] = NEUTRAL_PWM
    control_params[Throttle] = NEUTRAL_PWM
    control_params[Roll] = NEUTRAL_PWM

    # Control increments
    pitch_increment = 50
    yaw_increment = 50
    throttle_increment = 10
    roll_increment = 50

    # Check for keyboard input events
    keys = pygame.key.get_pressed()

    # Adjust pitch
    if keys[pygame.K_DOWN]:  # Down key increases pitch
        control_params[Pitch] += pitch_increment
    elif keys[pygame.K_UP]:  # Up key decreases pitch
        control_params[Pitch] -= pitch_increment

    # Adjust yaw
    if keys[pygame.K_LEFT]:
        control_params[Yaw] -= yaw_increment
    elif keys[pygame.K_RIGHT]:
        control_params[Yaw] += yaw_increment

    # Adjust throttle
    if keys[pygame.K_w]:  # Increase throttle
        control_params[Throttle] += throttle_increment
    elif keys[pygame.K_s]:  # Decrease throttle
        control_params[Throttle] -= throttle_increment

    # Adjust roll
    if keys[pygame.K_a]:
        control_params[Roll] -= roll_increment
    elif keys[pygame.K_d]:
        control_params[Roll] += roll_increment

    # Switch to AUTO mode with 'R' key
    if keys[pygame.K_r]:
        vehicle.mode = VehicleMode("AUTO")
        print("Switched to AUTO mode")

    # Switch to ACRO mode with 'T' key
    if keys[pygame.K_t]:
        vehicle.mode = VehicleMode("ACRO")
        print("Switched to ACRO mode")

    # Ensure PWM values stay within acceptable range (1000-2000)
    control_params[Pitch] = max(1000, min(2000, control_params[Pitch]))
    control_params[Yaw] = max(1000, min(2000, control_params[Yaw]))
    control_params[Throttle] = max(1000, min(2000, control_params[Throttle]))
    control_params[Roll] = max(1000, min(2000, control_params[Roll]))

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

def test_roll(vehicle, degree_per_second):
    roll_left, roll_right = calculate_roll_pwm(degree_per_second)

    print("Waiting for STABILIZE mode...")
    while vehicle.mode.name != "STABILIZE":
        time.sleep(1)

    time.sleep(5) # Wait for the vehicle to stabilize

    print("Switched to STABILIZE mode successfully. Starting Roll Test...")
    vehicle.mode = VehicleMode("ACRO")
    vehicle.channels.overrides[Throttle] = 2000

    vehicle.channels.overrides[Roll] = roll_left
    print(f"Setting roll to {roll_left} for 5 seconds")
    time.sleep(5)

    vehicle.channels.overrides[Roll] = roll_right
    print(f"Setting roll to {roll_right} for 7 seconds")
    time.sleep(3)

    vehicle.channels.overrides[Roll] = None
    vehicle.channels.overrides[Throttle] = None
    print("Roll test complete. Overrides cleared.")

def test_pitch(vehicle, degree_per_second):
    pitch_down, pitch_up = calculate_pitch_pwm(degree_per_second)

    print("Waiting for STABILIZE mode...")
    while vehicle.mode.name != "STABILIZE":
        time.sleep(1)

    time.sleep(3) # Wait for the vehicle to stabilize

    print("Switched to STABILIZE mode successfully. Starting Pitch Test...")
    vehicle.mode = VehicleMode("ACRO")
    vehicle.channels.overrides[Throttle] = 2000

    vehicle.channels.overrides[Pitch] = pitch_down
    print(f"Setting pitch to {pitch_down} for 2 seconds")
    time.sleep(2)

    vehicle.channels.overrides[Pitch] = pitch_up
    print(f"Setting pitch to {pitch_up} for 2 seconds")
    time.sleep(2)

    vehicle.channels.overrides[Pitch] = None
    vehicle.channels.overrides[Throttle] = None
    print("Pitch test complete. Overrides cleared.")

def test_yaw(vehicle, degree_per_second):
    yaw_left, yaw_right = calculate_yaw_pwm(degree_per_second)

    print("Waiting for STABILIZE mode...")
    while vehicle.mode.name != "STABILIZE":
        time.sleep(1)

    time.sleep(3) # Wait for the vehicle to stabilize

    print("Switched to STABILIZE mode successfully. Starting Yaw Test...")
    vehicle.mode = VehicleMode("ACRO")
    vehicle.channels.overrides[Throttle] = 2000

    vehicle.channels.overrides[Yaw] = yaw_left
    print(f"Setting yaw to {yaw_left} for 5 seconds")
    time.sleep(5)

    vehicle.channels.overrides[Yaw] = yaw_right
    print(f"Setting yaw to {yaw_right} for 10 seconds")
    time.sleep(10)

    vehicle.channels.overrides[Yaw] = None
    vehicle.channels.overrides[Throttle] = None
    print("Yaw test complete. Overrides cleared.")

def activate_acro_mode(vehicle):
    initialize_keyboard()

    try:
        while True:
            pygame.event.pump()
            update_control_params_from_keyboard(vehicle)

            if vehicle.mode.name == "ACRO":
                for channel, value in control_params.items():
                    print(f"Setting channel {channel} to {value}")
                    vehicle.channels.overrides[channel] = value
            else:
                vehicle.channels.overrides = {}

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Clearing channel overrides and exiting ACRO mode.")
        vehicle.channels.overrides = {}

def main():
    args = parse_arguments()
    connection_string = args.connect
    sitl = None

    if not connection_string:
        import dronekit_sitl
        sitl = dronekit_sitl.start_default(vehicle='plane')
        connection_string = sitl.connection_string()

    print(f'Connecting to vehicle on: {connection_string}')
    vehicle = connect(connection_string, wait_ready=True)

    try:
        pitch_rate = vehicle.parameters.get('ACRO_PITCH_RATE', None)
        yaw_rate = vehicle.parameters.get('ACRO_YAW_RATE', None)
        roll_rate = vehicle.parameters.get('ACRO_ROLL_RATE', None)

        global ROLL_RATE_FACTOR, YAW_RATE_FACTOR, PITCH_RATE_FACTOR
        ROLL_RATE_FACTOR = 500 / roll_rate if roll_rate else 1
        YAW_RATE_FACTOR = 500 / yaw_rate if yaw_rate else 1
        PITCH_RATE_FACTOR = 500 / pitch_rate if pitch_rate else 1

        print("Initial ACRO mode rates:")
        print(f"Pitch Rate: {pitch_rate}")
        print(f"Yaw Rate: {yaw_rate}")
        print(f"Roll Rate: {roll_rate}")

        if args.test:
            test_roll(vehicle, 20)
            vehicle.mode = VehicleMode("STABILIZE")
            time.sleep(5)
            test_pitch(vehicle, 15)
            vehicle.mode = VehicleMode("STABILIZE")
            time.sleep(5)
            test_yaw(vehicle, 90)
        elif args.acro:
            vehicle.mode = VehicleMode("ACRO")
            print("Starting in ACRO mode")
            activate_acro_mode(vehicle)
        else:
            vehicle.mode = VehicleMode("AUTO")
            print("Starting in AUTO mode")

    finally:
        vehicle.mode = VehicleMode("RTL")
        print("Closing vehicle connection.")
        vehicle.close()

        if sitl:
            sitl.stop()
        pygame.quit()
        print("Completed")

if __name__ == "__main__":
    main()
