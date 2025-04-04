import sys
import os
import re
import subprocess
import logging
from PyQt6.QtWidgets import (QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QLabel, QLineEdit, QComboBox,
                             QProgressBar, QMessageBox, QTabWidget, QFormLayout, QFrame,
                             QButtonGroup, QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QSize, QTimer
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QPixmap, QColor, QPalette

logging.basicConfig(filename="conversion.log", level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

class SettingsManager:
    def __init__(self):
        self.themes = {
            "Светлая": self.light_theme,
            "Тёмная": self.dark_theme,
            "Синяя": self.blue_theme,
            "Системная": self.system_theme
        }
        self.current_theme = "Светлая"
        
    def apply_theme(self, theme_name, app):
        if theme_name in self.themes:
            self.themes[theme_name](app)
            self.current_theme = theme_name
            
    def light_theme(self, app):
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(233, 231, 227))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        app.setPalette(palette)
        
    def dark_theme(self, app):
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        app.setPalette(palette)
        
    def blue_theme(self, app):
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 40, 60))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(20, 30, 50))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 50, 70))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(10, 20, 40))
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(30, 40, 60))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Highlight, QColor(70, 100, 150))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        app.setPalette(palette)
        
    def system_theme(self, app):
        app.setStyle("")
        palette = app.style().standardPalette()
        if palette.window().color().lightness() > 128:
            palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        else:
            palette.setColor(QPalette.ColorRole.Base, QColor(50, 50, 50))
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        app.setPalette(palette)

class ConverterThread(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)

    def __init__(self, input_file, output_file, format, crf=None, audio_bitrate=None, parent=None):
        super().__init__(parent)
        self.input_file = input_file
        self.output_file = output_file
        self.format = format
        self.crf = crf
        self.audio_bitrate = audio_bitrate
        self.process = None
        self._is_running = True
        self.duration = 0

    def get_video_duration(self):
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                  'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                  self.input_file]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return float(result.stdout.strip())
        except Exception as e:
            logging.error(f"Ошибка получения длительности: {e}")
            return 0

    def run(self):
        try:
            self.duration = self.get_video_duration()
            logging.info(f"Длительность видео: {self.duration} сек")

            ffmpeg_cmd = ["ffmpeg", "-y", "-i", self.input_file]
            
            if self.format in ["mp4", "avi", "mov", "gif", "webm", "mkv"]:
                ffmpeg_cmd.extend(["-c:v", "libx264"])
                
                if self.crf:
                    ffmpeg_cmd.extend(["-crf", str(self.crf)])
                
                if self.format == "gif":
                    ffmpeg_cmd.extend([
                        "-vf", "fps=10,scale=640:-1:flags=lanczos",
                        "-c:v", "gif"
                    ])
                elif self.format == "webm":
                    ffmpeg_cmd.extend(["-c:v", "libvpx-vp9"])
                
                ffmpeg_cmd.extend([
                    "-c:a", "aac",
                    "-b:a", self.audio_bitrate if self.audio_bitrate else "128k"
                ])
            
            elif self.format in ["mp3", "wav", "flac", "ogg", "aac"]:
                ffmpeg_cmd.extend(["-vn"])
                
                if self.format == "mp3":
                    ffmpeg_cmd.extend(["-c:a", "libmp3lame", "-q:a", "2"])
                elif self.format == "flac":
                    ffmpeg_cmd.extend(["-c:a", "flac"])
                elif self.format == "ogg":
                    ffmpeg_cmd.extend(["-c:a", "libvorbis"])
                elif self.format == "aac":
                    ffmpeg_cmd.extend(["-c:a", "aac"])
                
                if self.audio_bitrate:
                    ffmpeg_cmd.extend(["-b:a", self.audio_bitrate])

            ffmpeg_cmd.append(self.output_file)
            
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                universal_newlines=True,
                text=True
            )

            pattern = re.compile(r'time=(\d+):(\d+):(\d+).(\d+)')
            
            while self._is_running:
                line = self.process.stderr.readline()
                if not line:
                    break
                
                match = pattern.search(line)
                if match and self.duration > 0:
                    hours, minutes, seconds, _ = map(float, match.groups())
                    current_time = hours * 3600 + minutes * 60 + seconds
                    progress = int((current_time / self.duration) * 100)
                    self.progress_signal.emit(min(progress, 100))
                
                logging.debug(line.strip())

            self.process.wait()
            
            if self.process.returncode == 0:
                logging.info(f"Успешная конвертация в {self.output_file}")
                self.progress_signal.emit(100)
                self.finished_signal.emit(0)
            else:
                error_msg = self.process.stderr.read()
                logging.error(f"Ошибка конвертации: {error_msg}")
                self.error_signal.emit(f"Ошибка FFmpeg: {error_msg}")
                self.finished_signal.emit(1)

        except Exception as e:
            logging.error(f"Ошибка в процессе конвертации: {str(e)}")
            self.error_signal.emit(f"Ошибка: {str(e)}")
            self.finished_signal.emit(1)

    def stop(self):
        self._is_running = False
        if self.process:
            self.process.terminate()
        self.quit()
        self.wait(2000)

class MediaConverter:
    def __init__(self, main_window):
        self.main_window = main_window
        self.converter_thread = None

    def validate_input(self):
        if not self.main_window.ui.drag_drop_area.file_path:
            QMessageBox.critical(self.main_window, "Ошибка", "Пожалуйста, укажите входной файл.")
            return False
        if not os.path.exists(self.main_window.ui.drag_drop_area.file_path):
            QMessageBox.critical(self.main_window, "Ошибка", "Указанный входной файл не существует.")
            return False
        return True

    def get_output_file(self, output_format):
        default_name = os.path.splitext(os.path.basename(self.main_window.ui.drag_drop_area.file_path))[0] + f".{output_format}"
        return QFileDialog.getSaveFileName(
            self.main_window, 
            "Сохранить файл как...", 
            default_name, 
            f"{output_format.upper()} файлы (*.{output_format})"
        )[0]

    def get_output_format(self):
        if self.main_window.ui.tab_widget.currentIndex() == 0:  # Видео вкладка
            if self.main_window.ui.video_format_group.checkedButton():
                return self.main_window.ui.video_format_group.checkedButton().toolTip().lower()
        elif self.main_window.ui.tab_widget.currentIndex() == 1:  # Аудио вкладка
            if self.main_window.ui.audio_format_group.checkedButton():
                return self.main_window.ui.audio_format_group.checkedButton().toolTip().lower()
        return None
    
    def get_crf_value(self):
        return self.main_window.ui.crf_combo.currentData()
    
    def get_audio_bitrate(self):
        return self.main_window.ui.audio_bitrate_combo.currentData()
    
    def start_conversion(self):
        if not self.validate_input():
            return

        output_format = self.get_output_format()
        if not output_format:
            QMessageBox.critical(self.main_window, "Ошибка", "Пожалуйста, выберите формат для конвертации.")
            return

        output_file = self.get_output_file(output_format)
        if not output_file:
            return

        self.prepare_conversion()

        if self.converter_thread and self.converter_thread.isRunning():
            self.converter_thread.stop()

        self.converter_thread = ConverterThread(
            input_file=self.main_window.ui.drag_drop_area.file_path,
            output_file=output_file,
            format=output_format,
            crf=self.get_crf_value() if output_format in ["mp4", "avi", "mov", "gif", "webm", "mkv"] else None,
            audio_bitrate=self.get_audio_bitrate() if output_format in ["mp3", "wav", "flac", "ogg", "aac"] else "128k",
            parent=self.main_window
        )
        
        self.converter_thread.finished_signal.connect(self.conversion_finished)
        self.converter_thread.error_signal.connect(self.conversion_error)
        self.converter_thread.progress_signal.connect(self.update_progress)
        self.converter_thread.start()

    def update_progress(self, value):
        self.main_window.ui.progress_bar.setValue(value)
        self.main_window.ui.progress_label.setText(f"Прогресс: {value}%")

    def prepare_conversion(self):
        self.main_window.ui.convert_button.setEnabled(False)
        self.main_window.ui.progress_bar.setValue(0)
        if hasattr(self.main_window.ui, 'progress_label'):
            self.main_window.ui.progress_label.setText("Прогресс: 0%")

    def conversion_error(self, message):
        QMessageBox.critical(self.main_window, "Ошибка", message)
        self.main_window.ui.convert_button.setEnabled(True)

    def conversion_finished(self, return_code):
        self.main_window.ui.convert_button.setEnabled(True)
        
        if return_code == 0:
            QMessageBox.information(
                self.main_window,
                "Успех",
                f"Конвертация успешно завершена!\nФайл сохранен как:\n{os.path.basename(self.converter_thread.output_file)}"
            )
        else:
            QMessageBox.warning(
                self.main_window,
                "Ошибка",
                "Конвертация не выполнена! Проверьте лог для подробностей."
            )

class RoundedButton(QPushButton):
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(150, 50)
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(24, 24))
        self.setStyleSheet("""
            QPushButton {
                background-color: #20B2AA;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #48D1CC;
            }
            QPushButton:pressed {
                background-color: #008B8B;
            }
            QPushButton:checked {
                background-color: #008B8B;
            }
        """)

class IconOnlyButton(QPushButton):
    def __init__(self, icon_path, parent=None):
        super().__init__("", parent)
        self.setIcon(QIcon(icon_path))
        self.setIconSize(QSize(48, 48))
        self.setStyleSheet("""
            QPushButton {
                border: 1px solid #8f8f91;
                border-radius: 10px;
                padding: 12px;
                min-width: 80px;
                min-height: 80px;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #d0d0d0;
                border: 2px solid #20B2AA;
            }
        """)
        self.setCheckable(True)

class DragDropArea(QFrame):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setAcceptDrops(True)
        self.setFixedHeight(120)
        
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Перетащите файл сюда или кликните для выбора")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 14px;")
        self.layout.addWidget(self.label)
        self.file_path = ""
        
        self.update_style()

    def update_style(self):
        theme = getattr(self.main_window, 'ui', None) and self.main_window.ui.settings_manager.current_theme or "Светлая"
        
        if theme == "Тёмная":
            self.setStyleSheet("""
                QFrame {
                    border: 2px dashed #FF6B6B;
                    border-radius: 5px;
                    background-color: rgba(53, 53, 53, 0.5);
                }
                QLabel {
                    color: white;
                }
            """)
        elif theme == "Синяя":
            self.setStyleSheet("""
                QFrame {
                    border: 2px dashed #FF6B6B;
                    border-radius: 5px;
                    background-color: rgba(30, 40, 60, 0.5);
                }
                QLabel {
                    color: white;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 2px dashed #20B2AA;
                    border-radius: 5px;
                    background-color: rgba(249, 249, 249, 0.5);
                }
                QLabel {
                    color: black;
                }
            """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    border: 2px dashed #FF6B6B;
                    border-radius: 5px;
                    background-color: rgba(200, 200, 200, 0.3);
                }
                QLabel {
                    color: inherit;
                }
            """)

    def dragLeaveEvent(self, event):
        self.update_style()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and os.path.isfile(urls[0].toLocalFile()):
                self.file_path = urls[0].toLocalFile()
                self.label.setText(os.path.basename(self.file_path))
                self.setStyleSheet("""
                    QFrame {
                        border: 2px solid #20B2AA;
                        border-radius: 5px;
                    }
                    QLabel {
                        color: inherit;
                    }
                """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.main_window.open_file_dialog()

class MediaConverterUI:
    def __init__(self, main_window):
        self.main_window = main_window
        self.tab_widget = None
        self.settings_manager = SettingsManager()
        self.setup_ui()

    def setup_ui(self):
        self.setup_main_window()
        self.setup_left_panel()
        self.setup_tabs()
        self.setup_right_panel()

    def setup_main_window(self):
        self.main_window.setWindowTitle("Конвертер Медиа")
        self.main_window.setWindowIcon(QIcon("icon.png"))
        self.main_window.setGeometry(100, 100, 850, 600)
        self.central_widget = QWidget()
        self.main_window.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

    def setup_left_panel(self):
        self.left_panel = QVBoxLayout()
        self.left_panel.setContentsMargins(15, 20, 15, 20)
        self.left_panel.setSpacing(15)
        
        self.video_mode_button = RoundedButton("Видео", "pngs/video.png")
        self.audio_mode_button = RoundedButton("Аудио", "pngs/audio.png")
        self.settings_button = RoundedButton("Настройки", "pngs/settings.png")
        
        self.video_mode_button.setCheckable(True)
        self.audio_mode_button.setCheckable(True)
        self.video_mode_button.setChecked(True)
        
        self.video_mode_button.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        self.audio_mode_button.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        self.settings_button.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        
        self.left_panel.addWidget(self.video_mode_button)
        self.left_panel.addWidget(self.audio_mode_button)
        self.left_panel.addStretch()
        self.left_panel.addWidget(self.settings_button)
        
        self.main_layout.addLayout(self.left_panel, 1)

    def setup_tabs(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().hide()
        
        self.setup_video_tab()
        self.setup_audio_tab()
        self.setup_settings_tab()
        
        self.tab_widget.addTab(self.video_tab, "")
        self.tab_widget.addTab(self.audio_tab, "")
        self.tab_widget.addTab(self.settings_tab, "")

    def setup_video_tab(self):
        self.video_tab = QWidget()
        video_layout = QVBoxLayout(self.video_tab)
        
        video_formats_frame = QFrame()
        video_formats_layout = QGridLayout(video_formats_frame)
        
        self.video_format_group = QButtonGroup()
        self.video_format_group.setExclusive(True)
        for i, (fmt, icon) in enumerate([
            ("mp4", "pngs/mp4.png"),
            ("avi", "pngs/avi.png"), 
            ("mov", "pngs/mov.png"),
            ("gif", "pngs/gif.png"),
            ("webm", "pngs/webm.png"),
            ("mkv", "pngs/mkv.png")
        ]):
            btn = IconOnlyButton(icon)
            btn.setToolTip(fmt.upper())
            self.video_format_group.addButton(btn, i)
            video_formats_layout.addWidget(btn, i//3, i%3)
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Качество видео:"))
    
        self.crf_combo = QComboBox()
        self.crf_combo.addItem("Максимальное (CRF 18)", 18)
        self.crf_combo.addItem("Отличное (CRF 20)", 20)
        self.crf_combo.addItem("Хорошее (CRF 23 - по умолчанию)", 23)
        self.crf_combo.addItem("Среднее (CRF 26)", 26)
        self.crf_combo.addItem("Экономное (CRF 28)", 28)
        self.crf_combo.setCurrentIndex(2)
    
        quality_layout.addWidget(self.crf_combo)
        
        video_layout.addWidget(QLabel("Выберите формат:"))
        video_layout.addWidget(video_formats_frame)
        video_layout.addLayout(quality_layout)
        video_layout.addStretch()

    def setup_audio_tab(self):
        self.audio_tab = QWidget()
        audio_layout = QVBoxLayout(self.audio_tab)
        
        audio_formats_frame = QFrame()
        audio_formats_layout = QGridLayout(audio_formats_frame)
        
        self.audio_format_group = QButtonGroup()
        self.audio_format_group.setExclusive(True)
        for i, (fmt, icon) in enumerate([
            ("mp3", "pngs/mp3.png"),
            ("wav", "pngs/wav.png"), 
            ("flac", "pngs/flac.png"),
            ("ogg", "pngs/ogg.png"),
            ("aac", "pngs/aac.png")
        ]):
            btn = IconOnlyButton(icon)
            btn.setToolTip(fmt.upper())
            self.audio_format_group.addButton(btn, i)
            audio_formats_layout.addWidget(btn, i//3, i%3)
        
        bitrate_layout = QHBoxLayout()
        bitrate_layout.addWidget(QLabel("Качество звука:"))
    
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItem("Высокое (320 kbps)", "320k")
        self.audio_bitrate_combo.addItem("Хорошее (256 kbps)", "256k")
        self.audio_bitrate_combo.addItem("Стандартное (192 kbps)", "192k")
        self.audio_bitrate_combo.addItem("Базовое (128 kbps)", "128k")
        self.audio_bitrate_combo.addItem("Экономное (64 kbps)", "64k")
        self.audio_bitrate_combo.setCurrentIndex(3)
    
        bitrate_layout.addWidget(self.audio_bitrate_combo)
        
        audio_layout.addWidget(QLabel("Выберите формат:"))
        audio_layout.addWidget(audio_formats_frame)
        audio_layout.addLayout(bitrate_layout)
        audio_layout.addStretch()

    def setup_settings_tab(self):
        self.settings_tab = QWidget()
        settings_layout = QVBoxLayout(self.settings_tab)
        
        theme_group = QFrame()
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.settings_manager.themes.keys())
        self.theme_combo.setCurrentText(self.settings_manager.current_theme)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        
        theme_layout.addRow(QLabel("Тема:"), self.theme_combo)
        
        settings_layout.addWidget(QLabel("Настройки интерфейса:"))
        settings_layout.addWidget(theme_group)
        settings_layout.addStretch()

    def change_theme(self, theme_name):
        self.settings_manager.apply_theme(theme_name, QApplication.instance())
        self.update_drag_drop_style()

    def update_drag_drop_style(self):
        if hasattr(self, 'drag_drop_area'):
            self.drag_drop_area.update_style()

    def setup_right_panel(self):
        self.right_panel = QVBoxLayout()
        self.right_panel.setContentsMargins(10, 10, 10, 10)
        self.right_panel.setSpacing(15)
        
        self.drag_drop_area = DragDropArea(self.main_window)
        
        self.convert_button = RoundedButton("Конвертировать")
        self.convert_button.setFixedSize(200, 50)
        self.convert_button.clicked.connect(self.main_window.start_conversion)
        
        button_container = QHBoxLayout()
        button_container.addStretch(1)
        button_container.addWidget(self.convert_button)
        button_container.addStretch(1)
        
        self.progress_label = QLabel("Прогресс: 0%")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.right_panel.addWidget(self.drag_drop_area)
        self.right_panel.addWidget(self.tab_widget)
        self.right_panel.addLayout(button_container)
        self.right_panel.addWidget(self.progress_label)
        self.right_panel.addWidget(self.progress_bar)
        
        self.main_layout.addLayout(self.right_panel, 3)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = MediaConverterUI(self)
        self.converter = MediaConverter(self)
        QTimer.singleShot(100, self.force_style_update)

    def force_style_update(self):
        if hasattr(self.ui, 'drag_drop_area'):
            self.ui.drag_drop_area.update_style()

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выбрать файл", 
            "", 
            "Медиа файлы (*.mp4 *.avi *.mov *.mkv *.webm *.mp3 *.wav *.flac *.ogg *.aac)"
        )
        if file_path:
            self.ui.drag_drop_area.file_path = file_path
            self.ui.drag_drop_area.label.setText(os.path.basename(file_path))
            self.ui.drag_drop_area.setStyleSheet("""
                QFrame {
                    border: 2px solid #20B2AA;
                    border-radius: 5px;
                }
                QLabel {
                    color: inherit;
                }
            """)

    def start_conversion(self):
        self.converter.start_conversion()

    def closeEvent(self, event):
        if hasattr(self.converter, 'converter_thread') and self.converter.converter_thread and self.converter.converter_thread.isRunning():
            reply = QMessageBox.question(
                self, 'Конвертация в процессе',
                'Конвертация все еще выполняется. Вы уверены, что хотите закрыть программу?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.converter.converter_thread.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    settings = SettingsManager()
    settings.apply_theme("Светлая", app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())