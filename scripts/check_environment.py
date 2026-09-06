#!/usr/bin/env python3
"""Verify the local environment for the ME7027 coursework.

Reports on the Python interpreter, the packages listed in requirements.txt,
and the Quanser QCar SDK (which ships with the QCar software rather than
PyPI, so it is optional unless --require-quanser is passed).

Uses only the standard library so it can be run *before* the dependencies
are installed.

    python scripts/check_environment.py
    python scripts/check_environment.py --require-quanser
"""

from __future__ import annotations

import argparse
import importlib.util
import platform
import sys
from typing import NamedTuple

MIN_PYTHON = (3, 9)

# Distribution name -> module name, for the packages a script actually imports.
CORE_PACKAGES: dict[str, str] = {
    "numpy": "numpy",
    "scipy": "scipy",
    "pandas": "pandas",
    "opencv-contrib-python": "cv2",
    "scikit-image": "skimage",
    "Pillow": "PIL",
    "matplotlib": "matplotlib",
    "scikit-learn": "sklearn",
    "scikit-fuzzy": "skfuzzy",
    "filterpy": "filterpy",
}

# Heavier optional pieces: only needed to retrain the CNNs.
DEEP_LEARNING_PACKAGES: dict[str, str] = {
    "torch": "torch",
    "torchvision": "torchvision",
    "tensorflow": "tensorflow",
}

# Quanser QCar SDK. Installed from the Quanser distribution, never from PyPI.
QUANSER_PACKAGES: dict[str, str] = {
    "quanser-apis (HIL/communications)": "quanser",
    "Quanser PAL (physical/virtual QCar)": "pal",
    "Quanser QVL (Interactive Labs)": "qvl",
}


class Result(NamedTuple):
    label: str
    found: bool
    detail: str


def _version_of(label: str, module_name: str) -> str:
    """Best-effort version lookup that does not import the module.

    Tries the distribution name from the label first, since it often differs
    from the import name (opencv-contrib-python -> cv2, Pillow -> PIL), then
    falls back to the module name.
    """
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - Python < 3.8
        return "installed"

    # Labels may carry a trailing note, e.g. "quanser-apis (HIL/…)".
    dist = label.split("(")[0].strip()
    candidates = (dist, module_name, module_name.replace("_", "-"))
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return version(candidate)
        except PackageNotFoundError:
            continue
        except Exception:
            break
    return "installed"


def check_group(packages: dict[str, str]) -> list[Result]:
    results: list[Result] = []
    for label, module_name in packages.items():
        try:
            spec = importlib.util.find_spec(module_name)
        except (ImportError, ValueError):
            spec = None
        if spec is None:
            results.append(Result(label, False, "not found"))
        else:
            results.append(Result(label, True, _version_of(label, module_name)))
    return results


def report(title: str, results: list[Result]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    width = max((len(r.label) for r in results), default=0)
    for r in results:
        mark = "OK  " if r.found else "MISS"
        print(f"  [{mark}] {r.label.ljust(width)}  {r.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check the Python environment for the ME7027 coursework."
    )
    parser.add_argument(
        "--require-quanser",
        action="store_true",
        help="Treat a missing Quanser QCar SDK as a failure (use on the QCar "
        "or on a machine with Quanser Interactive Labs installed).",
    )
    parser.add_argument(
        "--require-deep-learning",
        action="store_true",
        help="Treat missing torch/tensorflow as a failure.",
    )
    args = parser.parse_args()

    print("ME7027 - Design of Autonomous Systems: environment check")
    print("=" * 56)
    print(f"  Python     {platform.python_version()} ({sys.executable})")
    print(f"  Platform   {platform.platform()}")

    failures: list[str] = []

    if sys.version_info < MIN_PYTHON:
        failures.append(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required, "
            f"found {platform.python_version()}"
        )

    core = check_group(CORE_PACKAGES)
    report("Core packages (required)", core)
    missing_core = [r.label for r in core if not r.found]
    if missing_core:
        failures.append(
            f"{len(missing_core)} core package(s) missing: {', '.join(missing_core)}"
        )

    dl = check_group(DEEP_LEARNING_PACKAGES)
    report("Deep learning (needed only to retrain the CNNs)", dl)
    missing_dl = [r.label for r in dl if not r.found]
    if missing_dl and args.require_deep_learning:
        failures.append(f"deep learning package(s) missing: {', '.join(missing_dl)}")

    quanser = check_group(QUANSER_PACKAGES)
    report("Quanser QCar SDK (not on PyPI - ships with the QCar software)", quanser)
    missing_quanser = [r.label for r in quanser if not r.found]
    if missing_quanser and args.require_quanser:
        failures.append(f"Quanser SDK component(s) missing: {', '.join(missing_quanser)}")

    print()
    if failures:
        print("RESULT: not ready")
        for f in failures:
            print(f"  - {f}")
        print("\nInstall the Python dependencies with:")
        print("    pip install -r requirements.txt")
        if missing_quanser and args.require_quanser:
            print(
                "\nThe Quanser SDK is installed by the QCar / Quanser Interactive\n"
                "Labs installer. See the QCar setup section of README.md."
            )
        return 1

    print("RESULT: ready")
    if missing_quanser:
        print(
            "  (Quanser SDK absent - fine for offline CV/deep-learning work,\n"
            "   required for the QCar scripts under scripts/qcar/.)"
        )
    if missing_dl:
        print("  (torch/tensorflow absent - fine unless retraining the CNNs.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
