from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from desktop_app.controllers.main_controller import MainController
from desktop_app.views.main_window import MainWindow


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    app = QApplication(sys.argv)
    app.setApplicationName("SARA Analytics Desktop")
    window = MainWindow()
    controller = MainController(window)
    window.controller = controller
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
