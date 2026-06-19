# main.py — AirBand 진입점
import sys
import io
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow
from config import FULLSCREEN, WINDOW_WIDTH, WINDOW_HEIGHT

#터미널 한글 유니코드 출력 인코딩 강제설정 (UnicodeEncodeError 해결)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def main():
    # 라즈베리파이 환경에서 libcamerify가 적용되지 않은 경우 자동 적용 후 재실행
    import os
    import sys
    import shutil
    if 'v4l2-compat.so' not in os.environ.get('LD_PRELOAD', ''):
        if shutil.which('libcamerify'):
            print("[INFO] libcamerify를 통한 자동 재실행을 수행합니다...")
            args = ['libcamerify', sys.executable] + sys.argv
            os.execvp('libcamerify', args)

    # QHD 및 고해상도 환경을 위한 High-DPI 스케일링 활성화
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName('AirBand')

    # 한글 폰트 깨짐(네모 박스) 방지를 위한 커스텀 폰트 로드
    import os
    from PyQt5.QtGui import QFontDatabase, QFont
    font_path = os.path.join(os.path.dirname(__file__), 'assets', 'NotoSansCJK-Regular.ttc')
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                app.setFont(QFont(families[0], 11))

    window = MainWindow()

    if FULLSCREEN:
        window.showFullScreen()
    else:
        window.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        # 화면 중앙에 창 띄우기
        screen_geo = QApplication.primaryScreen().geometry()
        x = (screen_geo.width() - WINDOW_WIDTH) // 2
        y = (screen_geo.height() - WINDOW_HEIGHT) // 2
        window.move(max(0, x), max(0, y))
        window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
