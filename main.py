# -*- coding: utf-8 -*-
"""
Adapted for Arduplane with optional RTL (Return to Launch), ACRO mode with keyboard control, and mode switching.
"""

from dronekit import connect, VehicleMode
import time
import argparse
import pygame

# Channel mappings for Arduplane
Roll = 1  # Added Roll channel
Pitch = 2
Throttle = 3
Yaw = 4

# Neutral PWM value
NEUTRAL_PWM = 1500

#Roll rate factor
ROLL_RATE_FACTOR = 0 # Set to 0 for now

# Yaw rate factor
YAW_RATE_FACTOR = 0 # Set to 0 for now

# Pitch rate factor
PITCH_RATE_FACTOR = 0 # Set to 0 for now

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
    throttle_increment = 10  # Smaller increment for finer throttle control
    roll_increment = 50

    # Check for keyboard input events
    keys = pygame.key.get_pressed()

    # Adjust pitch (DOWN and UP arrow keys, reversed logic)
    if keys[pygame.K_DOWN]:  # Down key increases pitch (move up)
        control_params[Pitch] += pitch_increment
    elif keys[pygame.K_UP]:  # Up key decreases pitch (move down)
        control_params[Pitch] -= pitch_increment

    # Adjust yaw (LEFT and RIGHT arrow keys)
    if keys[pygame.K_LEFT]:
        control_params[Yaw] -= yaw_increment
    elif keys[pygame.K_RIGHT]:
        control_params[Yaw] += yaw_increment

    # Adjust throttle (W and S keys)
    if keys[pygame.K_w]:  # Increase throttle
        control_params[Throttle] += throttle_increment
    elif keys[pygame.K_s]:  # Decrease throttle
        control_params[Throttle] -= throttle_increment

    # Adjust roll (A and D keys)
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


#    roll_left = NEUTRAL_PWM + (degree_per_second * ROLL_RATE_FACTOR)
#   roll_right = NEUTRAL_PWM + (degree_per_second * ROLL_RATE_FACTOR)

def test_roll(vehicle, degree_per_second):
    """
    Perform a test to set the roll channel to -50 from middle (1450) for 5 seconds,
    then +50 from middle (1550) for 7 seconds.
    """
    roll_left = NEUTRAL_PWM + (degree_per_second * ROLL_RATE_FACTOR)
    roll_right = NEUTRAL_PWM + (degree_per_second * ROLL_RATE_FACTOR)
    # Wait for the vehicle to switch to STABILIZE mode
    print("Waiting for STABILIZE mode...")
    while vehicle.mode.name != "STABILIZE":
        time.sleep(1)

    print("Switched to STABILIZE mode successfully. Starting Test...")
    print("Pitch test starting...")

    # Change vehicle mode to ACRO
    vehicle.mode = VehicleMode("ACRO")
    print("Roll test starting...")

    #Setting Throttle to 1500
    vehicle.channels.overrides[Throttle] = 2000

    # Set roll to 1450 (-50 from middle)
    vehicle.channels.overrides[Roll] = roll_left
    print(f"Setting roll to {roll_left} for 5 seconds")
    time.sleep(5)

    # Set roll to 1550 (+50 from middle)
    vehicle.channels.overrides[Roll] = roll_right
    print(f"Setting roll to {roll_right} for 7 seconds")
    time.sleep(10)

    # Clear the overrides
    vehicle.channels.overrides[Roll] = None
    vehicle.channels.overrides[Throttle] = None
    print("Roll test complete. Overrides cleared.")

def test_pitch(vehicle):
    """
    Perform a test to set the pitch channel to -50 from middle (1450) for 5 seconds,
    then +50 from middle (1550) for 7 seconds.
    """
    pitch_down = NEUTRAL_PWM - 50  # 1450
    pitch_up = NEUTRAL_PWM + 50  # 1550
    # Wait for the vehicle to switch to STABILIZE mode
    print("Waiting for STABILIZE mode...")
    while vehicle.mode.name != "STABILIZE":
        time.sleep(1)

    print("Switched to STABILIZE mode successfully. Starting Test...")
    print("Pitch test starting...")

    # Change vehicle mode to ACRO
    vehicle.mode = VehicleMode("ACRO")

    # Setting Throttle to 1500
    vehicle.channels.overrides[Throttle] = 2000

    # Set pitch to 1450 (-50 from middle)
    vehicle.channels.overrides[Pitch] = pitch_down
    print(f"Setting pitch to {pitch_down} for 2 seconds")
    time.sleep(2)

    # Set pitch to 1550 (+50 from middle)
    vehicle.channels.overrides[Pitch] = pitch_up
    print(f"Setting pitch to {pitch_up} for 2 seconds")
    time.sleep(2)

    # Clear the overrides
    vehicle.channels.overrides[Pitch] = None
    vehicle.channels.overrides[Throttle] = None
    print("Pitch test complete. Overrides cleared.")


def test_yaw(vehicle):
    """
    Perform a test to set the yaw channel to -50 from middle (1450) for 5 seconds,
    then +50 from middle (1550) for 7 seconds.
    """
    yaw_left = NEUTRAL_PWM - 200  # 1450
    yaw_right = NEUTRAL_PWM + 200  # 1550
    # Wait for the vehicle to switch to STABILIZE mode
    print("Waiting for STABILIZE mode...")
    while vehicle.mode.name != "STABILIZE":
        time.sleep(1)

    print("Switched to STABILIZE mode successfully. Starting yaw test...")
    print("Yaw test starting...")
    # Change vehicle mode to ACRO
    vehicle.mode = VehicleMode("ACRO")

    #Setting Throttle to 1500
    vehicle.channels.overrides[Throttle] = 2000

    # Set yaw to 1450 (-50 from middle)
    vehicle.channels.overrides[Yaw] = yaw_left
    print(f"Setting yaw to {yaw_left} for 5 seconds")
    time.sleep(5)

    # Set yaw to 1550 (+50 from middle)
    vehicle.channels.overrides[Yaw] = yaw_right
    print(f"Setting yaw to {yaw_right} for 10 seconds")
    time.sleep(10)

    # Clear the overrides
    vehicle.channels.overrides[Yaw] = None
    vehicle.channels.overrides[Throttle] = None
    print("Yaw test complete. Overrides cleared.")


def activate_acro_mode(vehicle):
    """
    Main loop for controlling the vehicle with keyboard input.
    Handles mode switching between ACRO and AUTO as well.
    """
    # Initialize keyboard for pygame
    initialize_keyboard()

    # Main control loop
    try:
        while True:
            # Process pygame events to capture keyboard state
            pygame.event.pump()

            # Update control parameters from keyboard, including mode switching
            update_control_params_from_keyboard(vehicle)

            # Only apply control parameters if in ACRO mode
            if vehicle.mode.name == "ACRO":
                for channel, value in control_params.items():
                    print(f"Setting channel {channel} to {value}")
                    vehicle.channels.overrides[channel] = value
            else:
                # Clear overrides in non-ACRO modes
                vehicle.channels.overrides = {}

            # Short sleep to avoid excessive CPU usage
            time.sleep(0.1)

    except KeyboardInterrupt:
        # Clear the overrides when stopping
        print("Clearing channel overrides and exiting ACRO mode.")
        vehicle.channels.overrides = {}

def main():
    args = parse_arguments()
    connection_string = args.connect
    sitl = None

    # Start SITL if no connection string specified
    if not connection_string:
        import dronekit_sitl
        sitl = dronekit_sitl.start_default(vehicle='plane')
        connection_string = sitl.connection_string()

    # Connect to the Vehicle
    print(f'Connecting to vehicle on: {connection_string}')
    vehicle = connect(connection_string, wait_ready=True)

    # Print ACRO mode pitch, yaw, and roll rates once after connection
    try:
        # Assuming `vehicle` has attributes or parameters for pitch, yaw, and roll rates in ACRO mode
        pitch_rate = vehicle.parameters.get('ACRO_PITCH_RATE', None)
        yaw_rate = vehicle.parameters.get('ACRO_YAW_RATE', None)
        roll_rate = vehicle.parameters.get('ACRO_ROLL_RATE', None)

        ROLL_RATE_FACTOR = 500/roll_rate
        YAW_RATE_FACTOR = 500/yaw_rate
        PITCH_RATE_FACTOR = 500/pitch_rate

        print("Initial ACRO mode rates:")
        print("-" * 50)
        print(f"Pitch Rate: {pitch_rate}")
        print(f"Yaw Rate: {yaw_rate}")
        print(f"Roll Rate: {roll_rate}")
        print("-" * 50)


        # Proceed with the remaining setup as per user-specified arguments
        if args.test:
            test_roll(vehicle)
            vehicle.mode = VehicleMode("STABILIZE")
            time.sleep(5)
            test_pitch(vehicle)
            vehicle.mode = VehicleMode("STABILIZE")
            time.sleep(5)
            test_yaw(vehicle)
        elif args.acro:
            vehicle.mode = VehicleMode("ACRO")
            print("Starting in ACRO mode")
            activate_acro_mode(vehicle)
        else:
            vehicle.mode = VehicleMode("AUTO")
            print("Starting in AUTO mode")

    finally:
        # Close vehicle object and clean up
        vehicle.mode = VehicleMode("STABILIZE")
        print("Closing vehicle connection.")
        vehicle.close()

        # Shut down SITL if started
        if sitl:
            sitl.stop()
        pygame.quit()
        print("Completed")



if __name__ == "__main__":
    main()
