# -*- coding: utf-8 -*-
"""
Adapted for Arduplane with optional RTL (Return to Launch) and ACRO mode with increased pitch rate for climbing
"""

from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import argparse
import threading

# Channel mappings for Arduplane
Roll = 1
Pitch = 2
Throttle = 3
Yaw = 4

def parse_arguments():
    parser = argparse.ArgumentParser(description='Commands Arduplane using waypoints.')
    parser.add_argument('--connect', help="Vehicle connection target string.")
    parser.add_argument('--rtl', action='store_true', help="Return to launch at the end of the mission.")
    parser.add_argument('--acro', action='store_true', help="Switch to ACRO mode at the end with configurable parameters.")
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

def activate_acro_mode(vehicle, stop_event):
    """
    Continuously listens for new control parameters and applies them in ACRO mode.
    """
    print("Switching to ACRO mode.")
    vehicle.mode = VehicleMode("ACRO")

    while not stop_event.is_set():
        # Simulate receiving control parameters from a client
        control_params = get_control_params_from_client()

        # Apply each override from the control_params dictionary
        for channel, value in control_params.items():
            print(f"Setting channel {channel} to {value}")
            vehicle.channels.overrides[channel] = value

        # Sleep briefly to simulate continuous data updates
        time.sleep(1)

    # Clear the overrides when stopping
    print("Clearing channel overrides and exiting ACRO mode.")
    vehicle.channels.overrides = {}

def get_control_params_from_client():
    """
    Simulates receiving control parameters from a client.
    Replace this with actual client data retrieval logic.
    """
    # Example control parameters - replace with actual data reception logic
    return {Pitch: 1500, Yaw: 1500, Throttle: 1500, Roll: 1450}


def activate_acro_mode1(vehicle, stop_event):
    """
    Continuously listens for new control parameters and applies them in ACRO mode.
    """
    print("Switching to ACRO mode.")
    vehicle.mode = VehicleMode("ACRO")

    while not stop_event.is_set():
        # Simulate receiving control parameters from a client
        control_params = get_control_params_from_client1()

        # Apply each override from the control_params dictionary
        for channel, value in control_params.items():
            print(f"Setting channel {channel} to {value}")
            vehicle.channels.overrides[channel] = value

        # Sleep briefly to simulate continuous data updates
        time.sleep(1)

    # Clear the overrides when stopping
    print("Clearing channel overrides and exiting ACRO mode.")
    vehicle.channels.overrides = {}

def get_control_params_from_client1():
    print("Switching to ACRO mode. 1111111111111111")
    """
    Simulates receiving control parameters from a client.
    Replace this with actual client data retrieval logic.
    """
    # Example control parameters - replace with actual data reception logic
    return {Pitch: 1500, Yaw: 1500, Throttle: 1500, Roll: 1550}
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

    try:
        arm_and_takeoff(vehicle)

        print("Setting target airspeed to 10")
        vehicle.airspeed = 10

        # print("Going towards first waypoint...")
        # point1 = LocationGlobalRelative(-35.361354, 149.165218, 100)
        # vehicle.simple_goto(point1)
        # time.sleep(1)
        #
        # print("Going towards second waypoint...")
        # point2 = LocationGlobalRelative(-35.363244, 149.168801, 100)
        # vehicle.simple_goto(point2)
        # time.sleep(1)

        # Check if RTL or ACRO mode should be activated
        if args.rtl:
            print("Returning to Launch (RTL mode activated)")
            vehicle.mode = VehicleMode("RTL")
        elif args.acro:
            # Start ACRO mode in a separate thread that continuously listens for control parameters
            stop_event = threading.Event()
            acro_thread = threading.Thread(target=activate_acro_mode, args=(vehicle, stop_event))
            acro_thread.start()

            # Run in ACRO mode for a specified duration or until stopped
            time.sleep(5)  # Example duration in ACRO mode
            stop_event.set()  # Signal the thread to stop
            acro_thread.join()  # Wait for the thread to finish

            print("Switching to ACRO mode. 1111111111111111")
            stop_event = threading.Event()
            acro_thread = threading.Thread(target=activate_acro_mode1, args=(vehicle, stop_event))
            acro_thread.start()

            # Run in ACRO mode for a specified duration or until stopped
            time.sleep(10)  # Example duration in ACRO mode
            stop_event.set()  # Signal the thread to stop
            acro_thread.join()  # Wait for the thread to finish

    finally:
        # Ensure the vehicle is closed and RTL is activated
        print("Returning to Launch (RTL mode activated)")
        vehicle.mode = VehicleMode("RTL")
        time.sleep(30)

        print("Close vehicle object")
        vehicle.close()

        # Shut down simulator if it was started
        if sitl:
            sitl.stop()
        print("Completed")

if __name__ == "__main__":
    main()