"""MyIT Ağ Araçları ve Ping sayfası.

Bu modül, IP/alan adı girilerek 4 paket veya sürekli modda
ping testi yapılmasını sağlayan, canlı çıktı ve istatistik gösteren
arayüz bileşenini içerir.
"""

from typing import Optional
from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from myit.modules.network.ping_service import (
    PingStatistics,
    PingWorker,
    validate_target,
)


class NetworkPage(QWidget):
    """Ağ Araçları sayfası ve Ping teşhis arayüzü."""

    MAX_LOG_LINES = 500

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[QThread] = None
        self._worker: Optional[PingWorker] = None

        self._init_ui()

    def _init_ui(self):
        """Arayüz bileşenlerini kurar."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # 1. Başlık Bölümü
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)

        title = QLabel("Ağ Araçları")
        title.setObjectName("PageHeaderTitle")
        header_layout.addWidget(title)

        subtitle = QLabel("ICMP Ping teşhisi ve ağ bağlantı kontrolleri")
        subtitle.setObjectName("PageHeaderSubtitle")
        header_layout.addWidget(subtitle)

        layout.addLayout(header_layout)

        # 2. Ping Kontrol Kartı (Girdi ve Eylemler)
        control_card = QFrame()
        control_card.setObjectName("PingControlCard")
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(20, 20, 20, 20)
        control_layout.setSpacing(16)

        card_title = QLabel("Hızlı Ping Testi")
        card_title.setObjectName("CardTitle")
        control_layout.addWidget(card_title)

        # Giriş Satırı (Hedef input, Mod seçimi, Başlat, Durdur, Temizle)
        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(10)

        self.input_target = QLineEdit()
        self.input_target.setObjectName("PingInput")
        self.input_target.setPlaceholderText("Hedef IP veya alan adı (Örn: 8.8.8.8, google.com)")
        self.input_target.returnPressed.connect(self.start_ping)
        inputs_layout.addWidget(self.input_target, 3)

        self.combo_mode = QComboBox()
        self.combo_mode.setObjectName("PingCombo")
        self.combo_mode.addItems(["4 Paket", "Sürekli"])
        inputs_layout.addWidget(self.combo_mode, 1)

        self.btn_start = QPushButton("Başlat")
        self.btn_start.setObjectName("PingStartBtn")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_ping)
        inputs_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Durdur")
        self.btn_stop.setObjectName("PingStopBtn")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_ping)
        inputs_layout.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("Temizle")
        self.btn_clear.setObjectName("PingClearBtn")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_output)
        inputs_layout.addWidget(self.btn_clear)

        control_layout.addLayout(inputs_layout)

        # Durum / Uyarı Etiketi
        self.lbl_feedback = QLabel("Test için bir hedef girin ve 'Başlat' butonuna basın.")
        self.lbl_feedback.setObjectName("PingFeedbackLabel")
        control_layout.addWidget(self.lbl_feedback)

        layout.addWidget(control_card)

        # 3. İstatistik Paneli
        stats_frame = QFrame()
        stats_frame.setObjectName("PingStatsFrame")
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setContentsMargins(16, 12, 16, 12)
        stats_layout.setHorizontalSpacing(24)

        # Gönderilen
        self.lbl_sent_val = QLabel("0")
        self.lbl_sent_val.setObjectName("StatValue")
        lbl_sent = QLabel("Gönderilen:")
        lbl_sent.setObjectName("StatTitle")
        stats_layout.addWidget(lbl_sent, 0, 0)
        stats_layout.addWidget(self.lbl_sent_val, 0, 1)

        # Alınan
        self.lbl_recv_val = QLabel("0")
        self.lbl_recv_val.setObjectName("StatValue")
        lbl_recv = QLabel("Alınan:")
        lbl_recv.setObjectName("StatTitle")
        stats_layout.addWidget(lbl_recv, 0, 2)
        stats_layout.addWidget(self.lbl_recv_val, 0, 3)

        # Kayıp Oranı
        self.lbl_loss_val = QLabel("%0")
        self.lbl_loss_val.setObjectName("StatValue")
        lbl_loss = QLabel("Paket Kaybı:")
        lbl_loss.setObjectName("StatTitle")
        stats_layout.addWidget(lbl_loss, 0, 4)
        stats_layout.addWidget(self.lbl_loss_val, 0, 5)

        # Ortalama Gecikme
        self.lbl_avg_val = QLabel("-")
        self.lbl_avg_val.setObjectName("StatValue")
        lbl_avg = QLabel("Ort. Gecikme:")
        lbl_avg.setObjectName("StatTitle")
        stats_layout.addWidget(lbl_avg, 0, 6)
        stats_layout.addWidget(self.lbl_avg_val, 0, 7)

        stats_layout.setColumnStretch(8, 1)
        layout.addWidget(stats_frame)

        # 4. Canlı Çıktı Konsolu (QPlainTextEdit - Readonly)
        self.console_output = QPlainTextEdit()
        self.console_output.setObjectName("PingConsole")
        self.console_output.setReadOnly(True)
        self.console_output.setMaximumBlockCount(self.MAX_LOG_LINES)
        layout.addWidget(self.console_output, 1)

    def start_ping(self):
        """Ping işlemini doğrular ve arka plan iş parçacığında başlatır."""
        raw_target = self.input_target.text()
        is_valid, result = validate_target(raw_target)

        if not is_valid:
            self.lbl_feedback.setText(f"⚠️ {result}")
            return

        target = result
        is_continuous = (self.combo_mode.currentIndex() == 1)

        # Buton durumları
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.input_target.setEnabled(False)
        self.combo_mode.setEnabled(False)

        mode_text = "Sürekli mod" if is_continuous else "4 paketlik mod"
        self.lbl_feedback.setText(f"⏳ {target} hedefine ping gönderiliyor ({mode_text})...")
        self.append_log(f"--- Ping Başlatıldı: {target} ({mode_text}) ---")

        # İstatistikleri sıfırla
        self._reset_stats()

        # QThread ve Worker yapılandırması
        self._thread = QThread()
        self._worker = PingWorker(target=target, continuous=is_continuous, count=4)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.line_received.connect(self.append_log)
        self._worker.stats_updated.connect(self._update_stats_display)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_ping_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def stop_ping(self):
        """Devam eden ping sürecini sonlandırır."""
        if self._worker:
            self._worker.stop()
            self.lbl_feedback.setText("⏹️ Ping işlemi kullanıcı tarafından durduruldu.")
            self.append_log("--- Ping Kullanıcı Tarafından Durduruldu ---")

    def _on_ping_finished(self):
        """Ping tamamlandığında arayüzü eski haline getirir."""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.input_target.setEnabled(True)
        self.combo_mode.setEnabled(True)

        if not self.lbl_feedback.text().startswith("⏹️") and not self.lbl_feedback.text().startswith("⚠️"):
            self.lbl_feedback.setText("✅ Ping işlemi tamamlandı.")
        self.append_log("--- Ping Tamamlandı ---\n")

    def _on_error(self, err_msg: str):
        """Hata durumunda uyarı verir."""
        self.lbl_feedback.setText(f"⚠️ {err_msg}")
        self.append_log(f"HATA: {err_msg}")

    def append_log(self, text: str):
        """Konsol çıktısına yeni satır ekler."""
        self.console_output.appendPlainText(text)

    def clear_output(self):
        """Yalnızca ekrandaki oturum çıktısını temizler."""
        self.console_output.clear()
        self._reset_stats()
        self.lbl_feedback.setText("Ekran temizlendi.")

    def _reset_stats(self):
        """İstatistik göstergelerini sıfırlar."""
        self.lbl_sent_val.setText("0")
        self.lbl_recv_val.setText("0")
        self.lbl_loss_val.setText("%0")
        self.lbl_avg_val.setText("-")

    def _update_stats_display(self, stats: PingStatistics):
        """İstatistik panelini gelen metriklerle günceller."""
        self.lbl_sent_val.setText(str(stats.sent))
        self.lbl_recv_val.setText(str(stats.received))
        self.lbl_loss_val.setText(f"%{stats.loss_percent:.0f}")
        if stats.avg_latency is not None:
            self.lbl_avg_val.setText(f"{stats.avg_latency} ms")
        else:
            self.lbl_avg_val.setText("-")

    def cleanup(self):
        """Pencere kapanırken aktif süreci ve iş parçacığını temizler."""
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
