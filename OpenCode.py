import random
import string
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTextEdit, QLineEdit, QToolButton, QFileDialog, \
    QWidget, QPushButton, QHBoxLayout
from PyQt6.QtGui import QIcon, QAction
from PIL import Image
import pytesseract
import openai
from PyQt6.QtCore import QThread, pyqtSignal
import os
from functools import partial


name_this_section = ""


class RequestThread(QThread):
    request_completed = pyqtSignal(str)

    def __init__(self, input_text):
        super().__init__()
        self.input_text = input_text

    def run(self):
        try:
            openai.api_key = "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"
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": f"дай мне ответ по {self.input_text}"}
                ]
            )
            response = completion.choices[0].message.content
            with open(f"{name_this_section}/info.txt", "a") as file:
                file.write(f"{self.input_text}${response}")
            self.request_completed.emit(response)
        except Exception as err:
            self.request_completed.emit(f"Ошибка при запросе к ИИ: {str(err)}")

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RUGPT")
        self.setGeometry(100, 100, 400, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        attach_image_button = QPushButton("📷")
        attach_image_button.clicked.connect(self.scan_image)
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("Введите ваш вопрос")
        send_button = QPushButton("Отправить")
        send_button.setFixedWidth(100)

        horizontal_layout = QHBoxLayout()
        horizontal_layout.addWidget(attach_image_button)
        horizontal_layout.addWidget(self.input_text)
        horizontal_layout.addWidget(send_button)
        layout.addWidget(self.output_text)
        layout.addLayout(horizontal_layout)
        central_widget.setLayout(layout)
        send_button.clicked.connect(self.send_request)

        # Создаем верхнюю панель меню
        menubar = self .menuBar()

        history_menu = menubar.addMenu("Секции")
        options_menu = menubar.addMenu("Настройки")
        help_menu = menubar.addMenu("Помощь")

        add_sec = QAction("Добавить новую", self)
        clear_sec = QAction(f"Очистка секции - {name_this_section}",  self)
        history_action = QAction("Выбрать существующую", self)
        history_menu.addAction(add_sec)
        history_menu.addAction(clear_sec)
        history_menu.addAction(history_action)
        if os.path.exists("sections"):
            subfolders = [f.name for f in os.scandir("sections") if f.is_dir()]
            for subfolder in subfolders:
                action = QAction(subfolder, self)
                action.triggered.connect(partial(self.clk_section, subfolder))
                history_menu.addAction(action)
        options_action = QAction("View", self)
        options_menu.addAction(options_action)
        # Действие для раздела Help
        help_action = QAction("Открыть центр помощи", self)
        help_action.triggered.connect(self.open_help_center)
        clear_sec.triggered.connect(self.clear_section)
        add_sec.triggered.connect(self.add_section)
        # Добавляем действие в раздел Help
        help_menu.addAction(help_action)

        self.load_section()

    def add_message(self, text, is_user=True):
        if is_user:
            message = f"Вы: {text}\n"
        else:
            message = f"RUGPT: {text}\n"
        self.output_text.append(message)

    def scan_image(self):
        image_file, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "",
                                                    "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
        if image_file:
            self.recognize_text(image_file)

    def recognize_text(self, image_file):
        try:
            image = Image.open(image_file)
            text = pytesseract.image_to_string(image)
            self.input_text.setText(text)
            self.send_request()
        except Exception as e:
            self.add_message("Ошибка при распознавании текста на изображении.")
            print(e)

    def clear_section(self):
        global name_this_section
        self.output_text.clear()
        with open(f"{name_this_section}/info.txt", "w") as file:
            file.write("")

    def open_help_center(self):
        help_url = "https://example.com/help"
        pass

    def add_section(self):
        global name_this_section
        key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
        # Создать папку
        folder_full_path = os.path.join("sections", f"section_{key}")
        os.makedirs(folder_full_path, exist_ok=True)

        # Создать пустой файл info.txt внутри созданной папки
        file_full_path = os.path.join(folder_full_path, "info.txt")
        open(file_full_path, 'w').close()
        name_this_section = folder_full_path
        self.select_section()

    def select_section(self):
        global name_this_section
        self.setWindowTitle(f"RUGPT - {name_this_section}")
        with open(f"{name_this_section}/info.txt", "r") as file:
            data = file.read()
        lst = data.split("$")
        if len(lst) > 1:
            res = ""
            for i in range(len(lst)):
                if i % 2 == 0:
                    self.add_message(lst[i], is_user=True)
                else:
                    self.add_message(lst[i], is_user=False)

    def load_section(self):
        global name_this_section
        # Путь к директории 'sections'
        sections_dir = 'sections'
        if not os.path.exists(sections_dir):
            os.mkdir(sections_dir)
        section_text_dir = os.path.join(sections_dir, 'section_test')
        if not os.path.exists(section_text_dir):
            os.mkdir(section_text_dir)
        info_file_path = os.path.join(section_text_dir, 'info.txt')
        if not os.path.exists(info_file_path):
            with open(info_file_path, 'w') as info_file:
                info_file.write("")

        subfolders = [f.path for f in os.scandir("sections") if f.is_dir()]
        name_this_section = subfolders[0]
        self.setWindowTitle(f"RUGPT - {name_this_section}")
        with open(f"{name_this_section}/info.txt", "r") as file:
            data = file.read()
        lst = data.split("$")
        if len(lst) > 1:
            res = ""
            for i in range(len(lst)):
                if i % 2 == 0:
                    self.add_message(lst[i], is_user=True)
                else:
                    self.add_message(lst[i], is_user=False)

    def clk_section(self, subfolder):
        global name_this_section
        self.output_text.clear()
        name_this_section = "sections/"+subfolder
        self.select_section()

    def send_request(self):
        input_text = self.input_text.text()
        self.input_text.clear()
        self.setWindowTitle("RUGPT печатает..")
        if input_text:
            self.add_message(input_text, is_user=True)  # Отображаем введенный текст в чате
            self.request_thread = RequestThread(input_text)
            self.request_thread.request_completed.connect(self.handle_response)
            self.request_thread.start()
        else:
            self.add_message("Ошибка: пустой запрос.", is_user=True)

    def handle_response(self, response):
        global name_this_section
        self.add_message(response, is_user=False)
        self.setWindowTitle(f"RUGPT - {name_this_section}")

def main():
    app = QApplication(sys.argv)
    window = MyWindow()
    window.setStyleSheet("""
        QMainWindow {
            background: #b3b4ff;
        }
        QTextEdit {
            background: rgba(255, 255, 255, 0.9);
            border: 2px solid #c7c7c7;
            border-radius: 5px;
            padding: 5px;
            color: #333;
        }
        QLineEdit {
            background: rgba(255, 255, 255, 0.9);
            border: 2px solid #c7c7c7;
            border-radius: 5px;
            padding: 5px;
            color: #333;
        }
        QPushButton {
            background: #007AFF;
            border: none;
            border-radius: 5px;
            color: #fff;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background: #0059B3;
        }
    """)
    window.setWindowOpacity(0.85)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
