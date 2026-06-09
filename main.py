# main.py — AirBand 진입점
import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('AirBand')
    window = MainWindow()
    window.showFullScreen()  # 물리 모니터 전체화면
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
