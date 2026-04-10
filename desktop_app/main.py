from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from desktop_app.controllers.main_controller import MainController
from desktop_app.views.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    controller = MainController(window)
    window.controller = controller
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
