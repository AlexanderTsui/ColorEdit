#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ColorEdit application entrypoint."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import setup_logger


def main() -> None:
    """Start the Qt application."""
    logger = setup_logger()
    logger.info("Starting ColorEdit")

    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        logger.error("PySide6 is not installed. Run: pip install -r requirements.txt")
        sys.exit(1)

    from src.gui_qt.main_window import ColorEditMainWindow

    app = QApplication(sys.argv)
    window = ColorEditMainWindow()
    window.show()
    exit_code = app.exec()
    logger.info("ColorEdit exited")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
