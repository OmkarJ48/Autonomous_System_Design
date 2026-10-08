#!/usr/bin/env python3
"""Virtual QCar in Quanser Interactive Labs (QLabs): spawn, drive, grab a frame.

Starting point for the Virtual QCar Simulation described in Part 4 of the
group report. It connects to a running QLabs instance, spawns a QCar, drives
a short open-loop manoeuvre, and pulls one RGB frame off the front camera.

    python scripts/qcar/qlabs_virtual_qcar.py
    python scripts/qcar/qlabs_virtual_qcar.py --host 192.168.2.15 --duration 8

Prerequisites
-------------
* Quanser Interactive Labs installed and running, with a QCar workspace open.
* The Quanser Python SDK on the path (the `qvl` package). It ships with the
  Quanser software; it is not on PyPI. See the QCar section of README.md.

SCAFFOLD: the QLabs API surface changes between SDK releases (notably
QLabsQCar vs QLabsQCar2). Check the calls below against the Quanser Python
API documentation for the version installed on your machine before relying
on them.
"""

from __future__ import annotations

import argparse
import sys
import time

SDK_HINT = """
The Quanser QLabs Python SDK (`qvl`) was not found.

It is installed by Quanser Interactive Labs rather than from PyPI. Either:
  * run this script with the Python interpreter that ships with Quanser, or
  * add the Quanser `python` directory to PYTHONPATH, or
  * install it from the local Quanser distribution.

See the "Quanser QCar environment" section of README.md.
""".strip()


def load_sdk():
    """Import the QLabs SDK, exiting with guidance if it is unavailable."""
    try:
        from qvl.qcar import QLabsQCar
        from qvl.qlabs import QuanserInteractiveLabs
    except ImportError:
        print(SDK_HINT, file=sys.stderr)
        raise SystemExit(2)
    return QuanserInteractiveLabs, QLabsQCar


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--host",
        default="localhost",
        help="Address of the machine running QLabs (default: localhost).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Seconds to drive before stopping (default: 5).",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=0.3,
        help="Forward drive command, roughly m/s (default: 0.3).",
    )
    parser.add_argument(
        "--turn",
        type=float,
        default=0.0,
        help="Steering command in radians, positive is left (default: 0).",
    )
    args = parser.parse_args()

    QuanserInteractiveLabs, QLabsQCar = load_sdk()

    qlabs = QuanserInteractiveLabs()
    print(f"Connecting to QLabs at {args.host} ...")
    if not qlabs.open(args.host):
        print(
            f"Could not connect to QLabs at {args.host}. Is it running with a "
            "QCar workspace open?",
            file=sys.stderr,
        )
        return 1
    print("Connected.")

    try:
        # Start from a clean workspace so repeat runs are reproducible.
        qlabs.destroy_all_spawned_actors()

        car = QLabsQCar(qlabs)
        car.spawn_id_degrees(
            actorNumber=0,
            location=[0.0, 0.0, 0.0],
            rotation=[0.0, 0.0, 0.0],
            scale=[1.0, 1.0, 1.0],
            configuration=0,
            waitForConfirmation=True,
        )
        print("QCar spawned at the origin.")

        # Open-loop manoeuvre. Closed-loop lane following replaces this call
        # with the PD controller described in Part 4 of the report.
        print(f"Driving for {args.duration:.1f} s "
              f"(speed={args.speed}, turn={args.turn}) ...")
        deadline = time.time() + args.duration
        while time.time() < deadline:
            car.set_velocity_and_request_state(
                forward=args.speed,
                turn=args.turn,
                headlights=False,
                leftTurnSignal=False,
                rightTurnSignal=False,
                brakeSignal=False,
                reverseSignal=False,
            )
            time.sleep(0.05)

        # Stop before releasing the actor.
        car.set_velocity_and_request_state(
            forward=0.0,
            turn=0.0,
            headlights=False,
            leftTurnSignal=False,
            rightTurnSignal=False,
            brakeSignal=True,
            reverseSignal=False,
        )
        print("Stopped.")

        # One RGB frame, the entry point for the CV and CNN pipelines.
        ok, image = car.get_image(camera=QLabsQCar.CAMERA_RGB)
        if ok:
            print(f"Captured front RGB frame: shape={getattr(image, 'shape', '?')}")
        else:
            print("Camera read failed.", file=sys.stderr)

    finally:
        qlabs.close()
        print("Disconnected from QLabs.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
