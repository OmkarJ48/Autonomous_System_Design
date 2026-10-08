#!/usr/bin/env python3
"""Read the QCar sensor suite and print a running summary.

Starting point for the sensor characterisation of Part 1 of the group report
on the QCar side: LiDAR ranges, CSI camera frames, RealSense RGB-D depth, and
the onboard IMU. Runs against the physical QCar or against a virtual QCar in
Quanser Interactive Labs, since the Quanser PAL layer presents the same API
for both.

    python scripts/qcar/qcar_sensors.py --duration 10
    python scripts/qcar/qcar_sensors.py --duration 30 --no-realsense

Prerequisites
-------------
* On the physical QCar: run on the vehicle's onboard computer.
* Virtually: Quanser Interactive Labs running with a QCar spawned.
* The Quanser Python SDK on the path (the `pal` package). It ships with the
  Quanser software; it is not on PyPI. See the QCar section of README.md.

SCAFFOLD: constructor arguments and attribute names in Quanser PAL vary
between SDK releases. Check these calls against the Quanser Python API
documentation for your installed version before relying on them.
"""

from __future__ import annotations

import argparse
import sys
import time

SDK_HINT = """
The Quanser PAL Python SDK (`pal`) was not found.

It is installed by the Quanser QCar software rather than from PyPI. Either:
  * run this script with the Python interpreter that ships with Quanser, or
  * add the Quanser `python` directory to PYTHONPATH, or
  * install it from the local Quanser distribution.

See the "Quanser QCar environment" section of README.md.
""".strip()


def load_sdk(use_lidar: bool, use_cameras: bool, use_realsense: bool):
    """Import the requested PAL components, exiting with guidance if absent."""
    try:
        from pal.products.qcar import QCar

        components = {"QCar": QCar}
        if use_lidar:
            from pal.products.qcar import QCarLidar

            components["QCarLidar"] = QCarLidar
        if use_cameras:
            from pal.products.qcar import QCarCameras

            components["QCarCameras"] = QCarCameras
        if use_realsense:
            from pal.products.qcar import QCarRealSense

            components["QCarRealSense"] = QCarRealSense
    except ImportError:
        print(SDK_HINT, file=sys.stderr)
        raise SystemExit(2)
    return components


def summarise(values) -> str:
    """Compact min/mean/max for an array-like, tolerant of empty input."""
    try:
        n = len(values)
    except TypeError:
        return str(values)
    if n == 0:
        return "no samples"
    try:
        lo, hi = min(values), max(values)
        mean = sum(values) / n
        return f"n={n} min={lo:.3f} mean={mean:.3f} max={hi:.3f}"
    except (TypeError, ValueError):
        return f"n={n}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Seconds to sample for (default: 10).",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=2.0,
        help="Summary print rate in Hz (default: 2).",
    )
    parser.add_argument(
        "--no-lidar", action="store_true", help="Skip the LiDAR."
    )
    parser.add_argument(
        "--no-cameras", action="store_true", help="Skip the CSI cameras."
    )
    parser.add_argument(
        "--no-realsense", action="store_true", help="Skip the RealSense D435."
    )
    args = parser.parse_args()

    use_lidar = not args.no_lidar
    use_cameras = not args.no_cameras
    use_realsense = not args.no_realsense

    sdk = load_sdk(use_lidar, use_cameras, use_realsense)

    qcar = sdk["QCar"](readMode=1, frequency=200)
    lidar = sdk["QCarLidar"]() if use_lidar else None
    cameras = (
        sdk["QCarCameras"](
            enableFront=True, enableBack=False, enableLeft=False, enableRight=False
        )
        if use_cameras
        else None
    )
    realsense = sdk["QCarRealSense"](mode="RGB&DEPTH") if use_realsense else None

    period = 1.0 / args.rate if args.rate > 0 else 0.5
    deadline = time.time() + args.duration
    print(f"Sampling for {args.duration:.1f} s at {args.rate:.1f} Hz ...\n")

    try:
        while time.time() < deadline:
            # Drive commands held at zero: this is a read-only characterisation.
            qcar.read_write_std(throttle=0.0, steering=0.0)

            parts = [
                f"battery={getattr(qcar, 'batteryVoltage', float('nan')):.2f} V",
                f"tach={getattr(qcar, 'motorTach', float('nan')):.3f}",
                f"gyro={getattr(qcar, 'gyroscope', None)}",
                f"accel={getattr(qcar, 'accelerometer', None)}",
            ]

            if lidar is not None:
                lidar.read()
                parts.append(f"lidar[{summarise(getattr(lidar, 'distances', []))}]")

            if cameras is not None:
                cameras.readAll()
                front = getattr(cameras, "csiFront", None)
                frame = getattr(front, "imageData", None) if front else None
                parts.append(f"csiFront={getattr(frame, 'shape', 'no frame')}")

            if realsense is not None:
                realsense.read_depth()
                depth = getattr(realsense, "imageBufferDepthPX", None)
                parts.append(f"depth={getattr(depth, 'shape', 'no frame')}")

            print(" | ".join(parts))
            time.sleep(period)

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        # Terminate in reverse order of construction.
        for device in (realsense, cameras, lidar, qcar):
            if device is None:
                continue
            terminate = getattr(device, "terminate", None)
            if callable(terminate):
                try:
                    terminate()
                except Exception as exc:  # noqa: BLE001 - best-effort cleanup
                    print(f"Cleanup warning: {exc}", file=sys.stderr)
        print("Devices released.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
