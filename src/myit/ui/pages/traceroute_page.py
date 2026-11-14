"""MyIT Traceroute ve Güzergah Analizi arayüz sayfası.

Bu modül; hedef IP veya alan adı girilerek ağ atlama noktalarını (hop),
gecikme sürelerini (RTT) canlı tablo şeklinde gösteren, maksimum hop ve
zaman aşımı ayarlarını yöneten kullanıcı arayüzünü içerir.
"""

from typing import List, Optional
from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from myit.modules.network.traceroute_service import (
    HopResult,
    TracerouteWorker,
    validate_traceroute_params,
    validate_traceroute_target,
)


class TraceroutePage(QWidget):
    """Traceroute arayüz sayfası."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[QThread] = None
        self._worker: Optional[TracerouteWorker] = None

        self._all_hops: List[HopResult] = []
        self._init_ui()

    def _init_ui(self):
        """Arayüz bileşenlerini kurar."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # 1. Başlık ve Açıklama
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        title = QLabel("Traceroute (Güzergah Analizi)")
        title.setObjectName("PageHeaderTitle")
        header_layout.addWidget(title)

        subtitle = QLabel("Hedef sisteme giden ağ paketlerinin geçtiği yönlendiricileri ve gecikme sürelerini analiz eder.")
        subtitle.setObjectName("PageHeaderSubtitle")
        header_layout.addWidget(subtitle)

        notice_lbl = QLabel("ℹ️ Bazı yönlendiriciler güvenlik politikaları nedeniyle ICMP yanıtlarını engelleyebilir (*) veya zaman aşımı verebilir.")
        notice_lbl.setObjectName("DiscoveryNoticeLabel")
        header_layout.addWidget(notice_lbl)

        layout.addLayout(header_layout)

        # 2. Kontrol Kartı (Hedef, IP Sürümü, Maks Hop, Timeout ve Butonlar)
        control_card = QFrame()
        control_card.setObjectName("TraceControlCard")
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(18, 16, 18, 16)
        control_layout.setSpacing(12)

        # Satır 1: Hedef ve IP Sürümü
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        lbl_target = QLabel("Hedef Adres:")
        lbl_target.setObjectName("FieldLabel")
        row1.addWidget(lbl_target)

        self.input_target = QLineEdit()
        self.input_target.setObjectName("TraceInput")
        self.input_target.setPlaceholderText("IP adresi veya alan adı (Örn: 8.8.8.8, 192.168.1.1, example.com)")
        self.input_target.returnPressed.connect(self.start_trace)
        row1.addWidget(self.input_target, 3)

        lbl_version = QLabel("IP Sürümü:")
        lbl_version.setObjectName("FieldLabel")
        row1.addWidget(lbl_version)

        self.combo_ip_version = QComboBox()
        self.combo_ip_version.setObjectName("TraceCombo")
        self.combo_ip_version.addItem("Otomatik", "AUTO")
        self.combo_ip_version.addItem("Yalnızca IPv4 (-4)", "IPV4")
        self.combo_ip_version.addItem("Yalnızca IPv6 (-6)", "IPV6")
        row1.addWidget(self.combo_ip_version, 1)

        control_layout.addLayout(row1)

        # Satır 2: Maks Hop ve Zaman Aşımı
        row2 = QHBoxLayout()
        row2.setSpacing(14)

        lbl_hops = QLabel("Maksimum Hop:")
        lbl_hops.setObjectName("FieldLabel")
        row2.addWidget(lbl_hops)

        self.spin_hops = QSpinBox()
        self.spin_hops.setObjectName("TraceSpin")
        self.spin_hops.setRange(1, 30)
        self.spin_hops.setValue(20)
        row2.addWidget(self.spin_hops)

        lbl_timeout = QLabel("Zaman Aşımı (ms):")
        lbl_timeout.setObjectName("FieldLabel")
        row2.addWidget(lbl_timeout)

        self.spin_timeout = QSpinBox()
        self.spin_timeout.setObjectName("TraceSpin")
        self.spin_timeout.setRange(250, 5000)
        self.spin_timeout.setSingleStep(250)
        self.spin_timeout.setValue(1000)
        row2.addWidget(self.spin_timeout)

        row2.addStretch()
        control_layout.addLayout(row2)

        # Satır 3: Butonlar ve Durum Özeti
        row3 = QHBoxLayout()
        row3.setSpacing(10)

        self.btn_start = QPushButton("Başlat")
        self.btn_start.setObjectName("TraceStartBtn")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_trace)
        row3.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Durdur")
        self.btn_stop.setObjectName("TraceStopBtn")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_trace)
        row3.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("Temizle")
        self.btn_clear.setObjectName("TraceClearBtn")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_table)
        row3.addWidget(self.btn_clear)

        row3.addStretch()

        self.lbl_hop_count = QLabel("Ulaşılan Hop: 0")
        self.lbl_hop_count.setObjectName("PortSummaryLabel")
        row3.addWidget(self.lbl_hop_count)

        control_layout.addLayout(row3)

        # Durum bildirim etiketi
        self.lbl_status = QLabel("Hedef belirleyip 'Başlat' butonuna basın.")
        self.lbl_status.setObjectName("TraceStatusLabel")
        control_layout.addWidget(self.lbl_status)

        layout.addWidget(control_card)

        # 3. Sonuç Tablosu
        self.table = QTableWidget(0, 6)
        self.table.setObjectName("DiscoveryTable")
        self.table.setHorizontalHeaderLabels([
            "Hop",
            "IP / Ağ Geçidi",
            "RTT 1",
            "RTT 2",
            "RTT 3",
            "Durum",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

    def set_target(self, target: str):
        """Dışarıdan (örneğin Ağ Keşfi sayfasından) hedef IP aktarır."""
        self.input_target.setText(target)
        self.lbl_status.setText(f"Hedef '{target}' aktarıldı. Hazırsanız 'Başlat' butonuna basın.")

    def start_trace(self):
        """Hedef ve parametreleri doğrular; Traceroute sürecini başlatır."""
        raw_target = self.input_target.text()
        is_valid, err_msg, clean_target = validate_traceroute_target(raw_target)

        if not is_valid:
            self.lbl_status.setText(f"⚠️ {err_msg}")
            return

        hops_val = self.spin_hops.value()
        timeout_val = self.spin_timeout.value()
        valid_params, param_err = validate_traceroute_params(hops_val, timeout_val)
        if not valid_params:
            self.lbl_status.setText(f"⚠️ {param_err}")
            return

        self.clear_table()

        selected_ip_version = self.combo_ip_version.currentData()

        # Kontrolleri kilitle
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_clear.setEnabled(False)
        self.input_target.setEnabled(False)
        self.combo_ip_version.setEnabled(False)
        self.spin_hops.setEnabled(False)
        self.spin_timeout.setEnabled(False)

        self.lbl_status.setText(f"⏳ {clean_target} hedefine güzergah analizi başlatılıyor...")

        # İş parçacığını başlat
        self._thread = QThread()
        self._worker = TracerouteWorker(
            target=clean_target,
            max_hops=hops_val,
            timeout_ms=timeout_val,
            ip_version=selected_ip_version,
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.hop_received.connect(self._on_hop_received)
        self._worker.status_changed.connect(self._on_status_changed)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_trace_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def stop_trace(self):
        """Devam eden Traceroute sürecini güvenle durdurur."""
        if self._worker:
            self._worker.stop()
            self.lbl_status.setText("⏹️ İşlem durduruluyor, alt süreç sonlandırılıyor...")

    def _on_hop_received(self, hop: HopResult):
        """Her yeni atlama noktası (Hop) geldiğinde tabloya ekler."""
        self._all_hops.append(hop)
        self.lbl_hop_count.setText(f"Ulaşılan Hop: {len(self._all_hops)}")
        self._insert_table_row(hop)

    def _insert_table_row(self, hop: HopResult):
        """Tabloya yeni sonuç satırı ekler."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Hop
        item_hop = QTableWidgetItem(str(hop.hop_num))
        item_hop.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, item_hop)

        # IP / Ağ Geçidi
        item_ip = QTableWidgetItem(hop.ip_or_host)
        self.table.setItem(row, 1, item_ip)

        # RTT 1, 2, 3
        for col_idx, rtt_val in enumerate((hop.rtt1, hop.rtt2, hop.rtt3), start=2):
            item_rtt = QTableWidgetItem(rtt_val)
            item_rtt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, col_idx, item_rtt)

        # Durum (Görsel ve metinsel durum)
        item_status = QTableWidgetItem(hop.status)
        if hop.status in ("Yanıt Alındı", "Hedefe Ulaşıldı"):
            item_status.setForeground(Qt.GlobalColor.green)
        elif hop.status == "Kısmi Yanıt":
            item_status.setForeground(Qt.GlobalColor.yellow)
        else:
            item_status.setForeground(Qt.GlobalColor.gray)
        self.table.setItem(row, 5, item_status)

    def _on_status_changed(self, msg: str):
        """Durum bildirimini günceller."""
        self.lbl_status.setText(msg)

    def _on_error(self, err: str):
        """Hata mesajını gösterir."""
        self.lbl_status.setText(f"⚠️ {err}")

    def _on_trace_finished(self):
        """İşlem bittiğinde kontrolleri açar."""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_clear.setEnabled(True)
        self.input_target.setEnabled(True)
        self.combo_ip_version.setEnabled(True)
        self.spin_hops.setEnabled(True)
        self.spin_timeout.setEnabled(True)

        count = len(self._all_hops)
        self.lbl_hop_count.setText(f"Ulaşılan Hop: {count}")

        if not self.lbl_status.text().startswith("⚠️") and not self.lbl_status.text().startswith("⏹️"):
            self.lbl_status.setText(f"✅ Güzergah analizi tamamlandı. {count} hop incelendi.")

    def clear_table(self):
        """Tabloyu ve RAM listesini temizler."""
        self.table.setRowCount(0)
        self._all_hops.clear()
        self.lbl_hop_count.setText("Ulaşılan Hop: 0")
        self.lbl_status.setText("Ekran temizlendi.")

    def cleanup(self):
        """Pencere kapanırken aktif worker'ı ve tracert sürecini temizler."""
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
