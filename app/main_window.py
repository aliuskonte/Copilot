"""Главное окно Copilot desktop."""

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.audio_recorder import AudioRecorder

# Загружаем .env из корня проекта
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")


def get_base_url() -> str:
    host = os.getenv("API_HOST", "127.0.0.1")
    port = os.getenv("API_PORT", "8000")
    return f"http://{host}:{port}"


class ProcessWorker(QThread):
    """Воркер для асинхронного вызова API."""

    finished = pyqtSignal(object, object)  # (result: dict | None, error: str | None)
    progress = pyqtSignal(str)

    def __init__(self, audio_wav: bytes) -> None:
        super().__init__()
        self._audio = audio_wav

    def run(self) -> None:
        try:
            self.progress.emit("Транскрибация...")
            base = get_base_url()
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{base}/api/v1/process",
                    files={"audio": ("audio.wav", self._audio, "audio/wav")},
                )
                response.raise_for_status()
                self.finished.emit(response.json(), None)
        except Exception as e:
            self.finished.emit(None, str(e))


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Copilot — помощник на созвонах")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self._question_edit = QPlainTextEdit()
        self._question_edit.setPlaceholderText("Вопрос собеседника появится здесь...")
        self._question_edit.setReadOnly(True)
        self._question_edit.setMaximumHeight(120)
        layout.addWidget(self._question_edit)

        self._answer_edit = QPlainTextEdit()
        self._answer_edit.setPlaceholderText("Ответ LLM появится здесь...")
        self._answer_edit.setReadOnly(True)
        layout.addWidget(self._answer_edit)

        self._process_btn = QPushButton("Обработать последние 30 сек")
        self._process_btn.clicked.connect(self._on_process)
        self._process_btn.setMinimumHeight(44)
        layout.addWidget(self._process_btn)

        self._recorder = AudioRecorder(on_error=self._on_recorder_error)
        self._worker: ProcessWorker | None = None

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Нажмите «Обработать» после того, как собеседник задал вопрос")

    def _on_recorder_error(self, msg: str) -> None:
        QMessageBox.warning(self, "Ошибка записи", msg)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._recorder.start():
            self._status.showMessage("BlackHole не найден — запись недоступна")

    def _on_process(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        if not self._recorder._running:
            QMessageBox.warning(
                self,
                "BlackHole",
                "BlackHole не найден. Установите: brew install blackhole-2ch\n\n"
                "Затем создайте Multi-Output Device в Audio MIDI Setup.",
            )
            return
        self._status.showMessage("Буфер записан, отправка на сервер...")
        wav = self._recorder.get_buffer_as_wav()
        if not wav:
            QMessageBox.warning(
                self,
                "Нет данных",
                "Буфер пуст или слишком короткий. Подождите несколько секунд и попробуйте снова.",
            )
            return
        self._process_btn.setEnabled(False)
        self._status.showMessage("Обработка...")
        self._worker = ProcessWorker(wav)
        self._worker.finished.connect(self._on_process_finished)
        self._worker.progress.connect(self._status.showMessage)
        self._worker.start()

    def _on_process_finished(self, result: dict | None, error: str | None) -> None:
        self._process_btn.setEnabled(True)
        if error:
            self._status.showMessage("Ошибка")
            QMessageBox.critical(
                self,
                "Ошибка API",
                f"Не удалось обработать аудио:\n{error}\n\n"
                "Убедитесь, что backend запущен (uvicorn) и OPENAI_API_KEY задан.",
            )
            return
        if not result:
            return
        transcript = result.get("transcript", "")
        question = result.get("question")
        answer = result.get("answer")
        self._question_edit.setPlainText(question or transcript or "(не вопрос)")
        self._answer_edit.setPlainText(answer or "(вопрос не обнаружен)")
        self._status.showMessage("Готово")

    def closeEvent(self, event) -> None:
        self._recorder.close()
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(2000)
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
