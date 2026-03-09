#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ColorEdit launcher."""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def check_dependencies() -> bool:
    """Check runtime dependencies."""
    missing = []

    for module_name, package_name in (
        ("cv2", "opencv-python"),
        ("numpy", "numpy"),
        ("PIL", "Pillow"),
        ("matplotlib", "matplotlib"),
        ("PySide6", "PySide6"),
    ):
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)

    if not missing:
        return True

    print("Missing dependencies:")
    for dep in missing:
        print(f"  - {dep}")
    print("\nInstall with:")
    print("  pip install -r requirements.txt")
    return False


def main() -> None:
    print("=" * 50)
    print("ColorEdit - HSV Mask Editor")
    print("Version: 1.1.0")
    print("=" * 50)

    if not check_dependencies():
        sys.exit(1)

    try:
        from src.main import main as app_main

        app_main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as exc:
        print(f"\nLaunch failed: {exc}")
        print("Please verify your environment and dependencies.")
        sys.exit(1)


if __name__ == "__main__":
    main()
