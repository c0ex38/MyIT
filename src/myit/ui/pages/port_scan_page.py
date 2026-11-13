"""MyIT TCP Port Tarayıcı arayüz sayfası.

Bu modül; IP/hostname ve hazır veya özel port grupları için
TCP port durumunu sorgulayan, canlı ilerleme ve filtrelenebilir
sonuç tablosu sunan kullanıcı arayüzünü içerir.
"""

from typing import Dict, List, Optional
from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from myit.modules.network.ping_service import validate_target
from myit.modules.network.port_scan_service import (
    COMMON_PORTS,
    PortScanResult,
    PortScanWorker,
    parse_port_expression,
)


class PortScanPage(QWidget):
    """TCP Port Tarayıcı arayüz sayfası."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[QThread] = None
        self._worker: Optional[PortScanWorker] = None

        self._all_results: List[PortScanResult] = []
        self._open_ports_count: int = 0

        self._init_ui()

    def _init_ui(self):
        """Arayüz bileşenlerini kurar."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # 1. Başlık ve Açıklama
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        title = QLabel("TCP Port Tarayıcı")
        title.setObjectName("PageHeaderTitle")
        header_layout.addWidget(title)

        subtitle = QLabel("Seçilen hedef üzerinde standart TCP connect() yöntemiyle portların bağlantı durumunu test eder.")
        subtitle.setObjectName("PageHeaderSubtitle")
        header_layout.addWidget(subtitle)

        notice_lbl = QLabel("ℹ️ Yalnızca izinli olduğunuz hedef sistemlerde tarama yapın. Bir taramada en fazla 256 port test edilebilir.")
        notice_lbl.setObjectName("DiscoveryNoticeLabel")
        header_layout.addWidget(notice_lbl)

        layout.addLayout(header_layout)

        # 2. Kontrol Kartı (Hedef, Port Seçimi, Timeout ve Eylemler)
        control_card = QFrame()
        control_card.setObjectName("PortControlCard")
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(18, 16, 18, 16)
        control_layout.setSpacing(12)

        # Satır 1: Hedef Girişi ve Zaman Aşımı
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        lbl_target = QLabel("Hedef Adres:")
        lbl_target.setObjectName("FieldLabel")
        row1.addWidget(lbl_target)

        self.input_target = QLineEdit()
        self.input_target.setObjectName("PortInput")
        self.input_target.setPlaceholderText("IP adresi veya alan adı (Örn: 192.168.1.1, example.com)")
        self.input_target.returnPressed.connect(self.start_scan)
        row1.addWidget(self.input_target, 3)

        lbl_timeout = QLabel("Zaman Aşımı (sn):")
        lbl_timeout.setObjectName("FieldLabel")
        row1.addWidget(lbl_timeout)

        self.spin_timeout = QDoubleSpinBox()
        self.spin_timeout.setObjectName("PortTimeoutSpin")
        self.spin_timeout.setRange(0.2, 3.0)
        self.spin_timeout.setSingleStep(0.1)
        self.spin_timeout.setValue(0.7)
        self.spin_timeout.setDecimals(1)
        row1.addWidget(self.spin_timeout, 1)

        control_layout.addLayout(row1)

        # Satır 2: Port Grubu Seçimi (Hazır Portlar vs Özel Portlar)
        row2 = QHBoxLayout()
        row2.setSpacing(14)

        self.radio_common = QRadioButton(f"Hazır Standart Portlar ({len(COMMON_PORTS)} port: Web, SSH, RDP vb.)")
        self.radio_common.setObjectName("PortRadio")
        self.radio_common.setChecked(True)
        self.radio_common.toggled.connect(self._on_port_mode_changed)
        row2.addWidget(self.radio_common)

        self.radio_custom = QRadioButton("Özel Port Listesi:")
        self.radio_custom.setObjectName("PortRadio")
        row2.addWidget(self.radio_custom)

        self.input_custom_ports = QLineEdit()
        self.input_custom_ports.setObjectName("PortInput")
        self.input_custom_ports.setPlaceholderText("Örn: 80,443,3389 veya 20-25,8080")
        self.input_custom_ports.setEnabled(False)
        self.input_custom_ports.returnPressed.connect(self.start_scan)
        row2.addWidget(self.input_custom_ports, 2)

        control_layout.addLayout(row2)

        # Satır 3: Butonlar
        row3 = QHBoxLayout()
        row3.setSpacing(10)

        self.btn_start = QPushButton("Taramayı Başlat")
        self.btn_start.setObjectName("PortStartBtn")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_scan)
        row3.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Durdur")
        self.btn_stop.setObjectName("PortStopBtn")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_scan)
        row3.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("Temizle")
        self.btn_clear.setObjectName("PortClearBtn")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_results)
        row3.addWidget(self.btn_clear)

        row3.addStretch()

        self.lbl_summary = QLabel("Açık Port: 0")
        self.lbl_summary.setObjectName("PortSummaryLabel")
        row3.addWidget(self.lbl_summary)

        control_layout.addLayout(row3)

        # Durum bildirim etiketi
        self.lbl_status = QLabel("Hedef belirleyip 'Taramayı Başlat' butonuna basın.")
        self.lbl_status.setObjectName("PortStatusLabel")
        control_layout.addWidget(self.lbl_status)

        layout.addWidget(control_card)

        # 3. İlerleme ve Filtre Çubuğu
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(14)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("DiscoveryProgressBar")
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m port (%p%)")
        progress_layout.addWidget(self.progress_bar, 1)

        self.chk_show_only_open = QCheckBox("Yalnızca açık portları göster")
        self.chk_show_only_open.setObjectName("DiscoveryFilterCheck")
        self.chk_show_only_open.setChecked(False)
        self.chk_show_only_open.toggled.connect(self._apply_filter)
        progress_layout.addWidget(self.chk_show_only_open)

        layout.addLayout(progress_layout)

        # 4. Sonuç Tablosu
        self.table = QTableWidget(0, 5)
        self.table.setObjectName("DiscoveryTable")
        self.table.setHorizontalHeaderLabels([
            "Port",
            "Protokol",
            "Durum",
            "Bilinen Servis",
            "Bağlantı Süresi (ms)",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

    def set_target(self, target: str):
        """Dışarıdan (örneğin Ağ Keşfi sayfasından) hedef IP aktarır."""
        self.input_target.setText(target)
        self.lbl_status.setText(f"Hedef '{target}' aktarıldı. Hazırsanız 'Taramayı Başlat'a basın.")

    def _on_port_mode_changed(self):
        """Hazır portlar / Özel portlar seçimine göre giriş kutusunu etkinleştirir."""
        is_custom = self.radio_custom.isChecked()
        self.input_custom_ports.setEnabled(is_custom)
        if is_custom:
            self.input_custom_ports.setFocus()

    def start_scan(self):
        """Hedef ve portları doğrular; port taramasını başlatır."""
        raw_target = self.input_target.text()
        is_valid, target_clean = validate_target(raw_target)

        if not is_valid:
            self.lbl_status.setText(f"⚠️ {target_clean}")
            return

        # Port listesini belirle
        if self.radio_common.isChecked():
            ports_to_scan = list(COMMON_PORTS)
        else:
            custom_expr = self.input_custom_ports.text()
            valid_ports, err_msg, parsed_ports = parse_port_expression(custom_expr)
            if not valid_ports:
                self.lbl_status.setText(f"⚠️ {err_msg}")
                return
            ports_to_scan = parsed_ports

        self.clear_results()

        timeout_val = float(self.spin_timeout.value())
        total_ports = len(ports_to_scan)

        self.progress_bar.setRange(0, total_ports)
        self.progress_bar.setValue(0)

        # Kontrolleri kilitle
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_clear.setEnabled(False)
        self.input_target.setEnabled(False)
        self.radio_common.setEnabled(False)
        self.radio_custom.setEnabled(False)
        self.input_custom_ports.setEnabled(False)
        self.spin_timeout.setEnabled(False)

        self.lbl_status.setText(f"⏳ {target_clean} hedefinde {total_ports} port taranıyor...")

        # İş parçacığını başlat
        self._thread = QThread()
        self._worker = PortScanWorker(target_host=target_clean, ports=ports_to_scan, timeout_sec=timeout_val)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.port_scanned.connect(self._on_port_scanned)
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.status_changed.connect(self._on_status_changed)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def stop_scan(self):
        """Devam eden taramayı güvenle durdurur."""
        if self._worker:
            self._worker.stop()
            self.lbl_status.setText("⏹️ Tarama durduruluyor, bekleyen soketler sonlandırılıyor...")

    def _on_port_scanned(self, result: PortScanResult):
        """Her port tarandığında tabloya ve listeye ekler."""
        self._all_results.append(result)
        if result.status == "Açık":
            self._open_ports_count += 1
            self.lbl_summary.setText(f"Açık Port: {self._open_ports_count}")

        if not self.chk_show_only_open.isChecked() or result.status == "Açık":
            self._insert_table_row(result)

    def _insert_table_row(self, result: PortScanResult):
        """Tabloya yeni sonuç satırı ekler."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Port
        self.table.setItem(row, 0, QTableWidgetItem(str(result.port)))

        # Protokol
        self.table.setItem(row, 1, QTableWidgetItem(result.protocol))

        # Durum (Renkli görsel vurgu)
        item_status = QTableWidgetItem(result.status)
        if result.status == "Açık":
            item_status.setForeground(Qt.GlobalColor.green)
        elif result.status == "Zaman Aşımı / Filtreli":
            item_status.setForeground(Qt.GlobalColor.yellow)
        else:
            item_status.setForeground(Qt.GlobalColor.gray)
        self.table.setItem(row, 2, item_status)

        # Bilinen Servis
        self.table.setItem(row, 3, QTableWidgetItem(result.service))

        # Süre
        lat_text = f"{result.latency} ms" if result.latency is not None else "-"
        self.table.setItem(row, 4, QTableWidgetItem(lat_text))

    def _on_progress(self, current: int, total: int):
        """İlerleme çubuğunu günceller."""
        self.progress_bar.setValue(current)

    def _on_status_changed(self, msg: str):
        """Durum mesajını günceller."""
        self.lbl_status.setText(msg)

    def _on_error(self, err: str):
        """Hata mesajını gösterir."""
        self.lbl_status.setText(f"⚠️ {err}")

    def _on_scan_finished(self):
        """Tarama tamamlandığında arayüzü eski haline getirir."""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_clear.setEnabled(True)
        self.input_target.setEnabled(True)
        self.radio_common.setEnabled(True)
        self.radio_custom.setEnabled(True)
        self.input_custom_ports.setEnabled(self.radio_custom.isChecked())
        self.spin_timeout.setEnabled(True)

        total_tested = len(self._all_results)
        self.lbl_summary.setText(f"Açık Port: {self._open_ports_count}")

        if not self.lbl_status.text().startswith("⚠️") and not self.lbl_status.text().startswith("⏹️"):
            self.lbl_status.setText(f"✅ Tarama tamamlandı. {total_tested} port test edildi, {self._open_ports_count} açık port tespit edildi.")

    def _apply_filter(self):
        """'Yalnızca açık portları göster' filtresini tabloya uygular."""
        self.table.setRowCount(0)
        only_open = self.chk_show_only_open.isChecked()
        for res in self._all_results:
            if not only_open or res.status == "Açık":
                self._insert_table_row(res)

    def clear_results(self):
        """Sonuçları ve ekranı temizler (Sadece RAM)."""
        self.table.setRowCount(0)
        self._all_results.clear()
        self._open_ports_count = 0
        self.progress_bar.setValue(0)
        self.lbl_summary.setText("Açık Port: 0")
        self.lbl_status.setText("Ekran temizlendi.")

    def cleanup(self):
        """Pencere kapanırken aktif iş parçacığını ve soketleri kapatır."""
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
