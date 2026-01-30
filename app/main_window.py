"""Главное окно Copilot desktop."""

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from PyQt6.QtCore import QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.audio_recorder import AudioRecorder, SAMPLE_RATE, bytes_to_wav
from app.vad import get_last_speech_segment

# Загружаем .env из корня проекта
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")


def _get_vad_min_speech_sec() -> float:
    try:
        return float(os.getenv("VAD_MIN_SPEECH_SEC", "1.0"))
    except ValueError:
        return 1.0


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

        self._process_btn = QPushButton("Обработать последние 15 сек")
        self._process_btn.clicked.connect(self._on_process)
        self._process_btn.setMinimumHeight(44)
        layout.addWidget(self._process_btn)

        self._auto_checkbox = QCheckBox("Авто: проверять каждые 3 сек")
        self._auto_checkbox.setChecked(False)
        self._auto_checkbox.stateChanged.connect(self._on_auto_toggled)
        layout.addWidget(self._auto_checkbox)

        self._recorder = AudioRecorder(on_error=self._on_recorder_error)
        self._worker: ProcessWorker | None = None
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._on_auto_tick)
        self._auto_timer.setInterval(3000)  # 3 сек
        self._last_processed_hash: int | None = None
        self._auto_cooldown_until: float = 0

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Нажмите «Обработать» после того, как собеседник задал вопрос")

    def _on_recorder_error(self, msg: str) -> None:
        QMessageBox.warning(self, "Ошибка записи", msg)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._recorder.start():
            self._status.showMessage("BlackHole не найден — запись недоступна")

    def _on_auto_toggled(self, state: int) -> None:
        if state:
            self._auto_timer.start()
            self._status.showMessage("Авто: включено")
        else:
            self._auto_timer.stop()
            self._status.showMessage("Авто: выключено")

    def _on_auto_tick(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        if not self._recorder._running:
            return
        self._process_auto()

    def _get_audio_to_process(self) -> bytes | None:
        """Возвращает WAV для обработки: VAD-сегмент или полный буфер."""
        raw = self._recorder.get_buffer_raw()
        if not raw or len(raw) < SAMPLE_RATE * 2:
            return None
        min_sec = _get_vad_min_speech_sec()
        segment = get_last_speech_segment(raw, min_speech_sec=min_sec)
        if segment:
            return bytes_to_wav(segment)
        return self._recorder.get_buffer_as_wav()

    def _process_auto(self) -> None:
        """Автообработка: дебаунс, rate limit, отправка."""
        import time as _time

        wav = self._get_audio_to_process()
        if not wav:
            return
        h = hash(wav)
        if h == self._last_processed_hash:
            return
        now = _time.monotonic()
        if now < self._auto_cooldown_until:
            return
        self._last_processed_hash = h
        self._auto_cooldown_until = now + 8.0  # мин. 8 сек между запросами
        self._process_btn.setEnabled(False)
        self._status.showMessage("Авто: обработка...")
        self._worker = ProcessWorker(wav)
        self._worker.finished.connect(self._on_process_finished)
        self._worker.progress.connect(self._status.showMessage)
        self._worker.start()

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
        wav = self._get_audio_to_process()
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
        self._last_processed_hash = None
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
        timing = result.get("timing", {})
        self._question_edit.setPlainText(question or transcript or "(не вопрос)")
        self._answer_edit.setPlainText(answer or "(вопрос не обнаружен)")
        total_ms = timing.get("total_ms")
        status = f"Готово ({total_ms} мс)" if total_ms is not None else "Готово"
        self._status.showMessage(status)

    def closeEvent(self, event) -> None:
        self._auto_timer.stop()
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
