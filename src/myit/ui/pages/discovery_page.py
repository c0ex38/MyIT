"""MyIT Ağ Keşfi (Network Discovery) arayüz sayfası.

Bu modül; aktif ağ bağdaştırıcılarını listeleyen, otomatik hesaplanan CIDR
aralığıyla yerel ağdaki cihazları tespit eden, canlı sonuç tablosu ve
ilerleme çubuğu sunan kullanıcı arayüzünü içerir.
"""

from typing import Callable, Dict, List, Optional
from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from myit.modules.network.discovery_service import (
    DiscoveredDevice,
    DiscoveryWorker,
    NetworkAdapterInfo,
    get_network_adapters,
    validate_cidr,
)


class DiscoveryPage(QWidget):
    """Ağ Keşfi arayüz sayfası."""

    def __init__(
        self,
        on_send_to_ping: Optional[Callable[[str], None]] = None,
        on_send_to_port_scan: Optional[Callable[[str], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.on_send_to_ping = on_send_to_ping
        self.on_send_to_port_scan = on_send_to_port_scan

        self._adapters: List[NetworkAdapterInfo] = []
        self._thread: Optional[QThread] = None
        self._worker: Optional[DiscoveryWorker] = None

        # Bulunan cihazları hafızada tut (RAM only)
        self._all_devices: List[DiscoveredDevice] = []

        self._init_ui()
        self.refresh_adapters()

    def _init_ui(self):
        """Arayüz bileşenlerini kurar."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # 1. Başlık ve Açıklama
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        title = QLabel("Ağ Cihaz Keşfi")
        title.setObjectName("PageHeaderTitle")
        header_layout.addWidget(title)

        subtitle = QLabel("Yerel ağdaki (L2/L3) aktif cihazları, IP, MAC ve alan adlarını tespit eder.")
        subtitle.setObjectName("PageHeaderSubtitle")
        header_layout.addWidget(subtitle)

        # Yasal / Güvenlik Uyarısı
        warning_lbl = QLabel("ℹ️ Yalnızca yetkili veya sahibi olduğunuz yerel ağlarda tarama yapın. İlk sürümde en fazla /24 desteklenir.")
        warning_lbl.setObjectName("DiscoveryNoticeLabel")
        header_layout.addWidget(warning_lbl)

        layout.addLayout(header_layout)

        # 2. Kontrol Kartı (Bağdaştırıcı Seçimi, CIDR ve Aksiyonlar)
        control_card = QFrame()
        control_card.setObjectName("DiscoveryControlCard")
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(18, 16, 18, 16)
        control_layout.setSpacing(12)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        lbl_adapter = QLabel("Ağ Bağdaştırıcısı:")
        lbl_adapter.setObjectName("FieldLabel")
        row1.addWidget(lbl_adapter)

        self.combo_adapters = QComboBox()
        self.combo_adapters.setObjectName("DiscoveryCombo")
        self.combo_adapters.currentIndexChanged.connect(self._on_adapter_selected)
        row1.addWidget(self.combo_adapters, 3)

        btn_refresh = QPushButton("Yenile")
        btn_refresh.setObjectName("DiscoveryRefreshBtn")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_adapters)
        row1.addWidget(btn_refresh)

        row1.addStretch(1)
        control_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)

        lbl_cidr = QLabel("Tarama CIDR:")
        lbl_cidr.setObjectName("FieldLabel")
        row2.addWidget(lbl_cidr)

        self.input_cidr = QLineEdit()
        self.input_cidr.setObjectName("DiscoveryInput")
        self.input_cidr.setPlaceholderText("Örn: 192.168.1.0/24")
        self.input_cidr.returnPressed.connect(self.start_scan)
        row2.addWidget(self.input_cidr, 2)

        self.btn_start = QPushButton("Taramayı Başlat")
        self.btn_start.setObjectName("DiscoveryStartBtn")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self.start_scan)
        row2.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Durdur")
        self.btn_stop.setObjectName("DiscoveryStopBtn")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_scan)
        row2.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("Temizle")
        self.btn_clear.setObjectName("DiscoveryClearBtn")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_table)
        row2.addWidget(self.btn_clear)

        control_layout.addLayout(row2)

        # Durum ve Geri Bildirim
        self.lbl_status = QLabel("Hazır. Bir bağdaştırıcı seçip 'Taramayı Başlat' butonuna basın.")
        self.lbl_status.setObjectName("DiscoveryStatusLabel")
        control_layout.addWidget(self.lbl_status)

        layout.addWidget(control_card)

        # 3. İlerleme ve Filtre Çubuğu
        progress_bar_layout = QHBoxLayout()
        progress_bar_layout.setSpacing(14)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("DiscoveryProgressBar")
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m (%p%)")
        progress_bar_layout.addWidget(self.progress_bar, 1)

        self.chk_show_unreachable = QCheckBox("Yanıtsız IP'leri de göster")
        self.chk_show_unreachable.setObjectName("DiscoveryFilterCheck")
        self.chk_show_unreachable.setChecked(False)
        self.chk_show_unreachable.toggled.connect(self._apply_filter)
        progress_bar_layout.addWidget(self.chk_show_unreachable)

        layout.addLayout(progress_bar_layout)

        # 4. Sonuç Tablosu
        self.table = QTableWidget(0, 6)
        self.table.setObjectName("DiscoveryTable")
        self.table.setHorizontalHeaderLabels(["IP Adresi", "Hostname (DNS)", "MAC Adresi", "Durum", "Gecikme (ms)", "Eylemler"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

    def refresh_adapters(self):
        """Aktif ağ bağdaştırıcılarını yeniden sorgular ve listeler."""
        self._adapters = get_network_adapters()
        self.combo_adapters.clear()

        if not self._adapters:
            self.combo_adapters.addItem("Aktif bağdaştırıcı bulunamadı (elle CIDR girin)", None)
            self.lbl_status.setText("⚠️ Otomatik bağdaştırıcı algılanamadı. Lütfen elle bir yerel CIDR girin.")
            return

        for adapter in self._adapters:
            gw_info = f" (Ağ Geçidi: {adapter.gateway})" if adapter.gateway else ""
            display_text = f"{adapter.alias} — {adapter.ip_address}/{adapter.prefix_length}{gw_info}"
            self.combo_adapters.addItem(display_text, adapter)

        self.combo_adapters.setCurrentIndex(0)
        self._on_adapter_selected(0)

    def _on_adapter_selected(self, index: int):
        """Bağdaştırıcı seçildiğinde CIDR giriş kutusunu günceller."""
        if index < 0 or index >= len(self._adapters):
            return
        adapter = self._adapters[index]
        self.input_cidr.setText(adapter.cidr)
        self.lbl_status.setText(f"Seçili bağdaştırıcı: {adapter.alias} ({adapter.ip_address})")

    def start_scan(self):
        """CIDR aralığını doğrular ve keşif taramasını başlatır."""
        cidr_text = self.input_cidr.text()
        is_valid, msg, net = validate_cidr(cidr_text)

        if not is_valid or net is None:
            self.lbl_status.setText(f"⚠️ {msg}")
            return

        self.clear_table()

        # Gateway IP tespiti
        selected_adapter = self.combo_adapters.currentData()
        gw_ip = selected_adapter.gateway if isinstance(selected_adapter, NetworkAdapterInfo) else None

        total_hosts = len(list(net.hosts()))
        self.progress_bar.setRange(0, total_hosts)
        self.progress_bar.setValue(0)

        # Kontrollerin durumunu güncelle
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_clear.setEnabled(False)
        self.input_cidr.setEnabled(False)
        self.combo_adapters.setEnabled(False)

        self.lbl_status.setText(f"⏳ {net} aralığı taranıyor ({total_hosts} hedef)...")

        # İş parçacığını başlat
        self._thread = QThread()
        self._worker = DiscoveryWorker(network=net, gateway_ip=gw_ip)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.device_found.connect(self._on_device_found)
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.status_changed.connect(self._on_status_changed)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def stop_scan(self):
        """Devam eden taramayı iptal eder."""
        if self._worker:
            self._worker.stop()
            self.lbl_status.setText("⏹️ Tarama durduruluyor, bekleyen işler sonlandırılıyor...")

    def _on_device_found(self, device: DiscoveredDevice):
        """Yeni bir cihaz sonucu geldiğinde RAM listesine ve tabloya ekler."""
        self._all_devices.append(device)

        # Filtreye göre tabloya ekle
        show_unreachable = self.chk_show_unreachable.isChecked()
        if device.status == "Erişilebilir" or show_unreachable:
            self._insert_table_row(device)

    def _insert_table_row(self, device: DiscoveredDevice):
        """Tabloya yeni bir satır yerleştirir."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # IP
        ip_text = f"⭐ {device.ip} (Ağ Geçidi)" if device.is_gateway else device.ip
        item_ip = QTableWidgetItem(ip_text)
        item_ip.setData(Qt.ItemDataRole.UserRole, device.ip)
        self.table.setItem(row, 0, item_ip)

        # Hostname
        self.table.setItem(row, 1, QTableWidgetItem(device.hostname))

        # MAC
        self.table.setItem(row, 2, QTableWidgetItem(device.mac_address))

        # Durum
        item_status = QTableWidgetItem(device.status)
        if device.status == "Erişilebilir":
            item_status.setForeground(Qt.GlobalColor.green)
        else:
            item_status.setForeground(Qt.GlobalColor.gray)
        self.table.setItem(row, 3, item_status)

        # Gecikme
        lat_text = f"{device.latency} ms" if device.latency is not None else "-"
        self.table.setItem(row, 4, QTableWidgetItem(lat_text))

        # Eylem Butonları Paneli (Ping ve Port Tara)
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(4, 2, 4, 2)
        action_layout.setSpacing(6)

        btn_ping = QPushButton("Ping")
        btn_ping.setObjectName("TablePingBtn")
        btn_ping.setCursor(Qt.CursorShape.PointingHandCursor)
        target_ip = device.ip
        btn_ping.clicked.connect(lambda checked=False, tip=target_ip: self._send_to_ping(tip))
        action_layout.addWidget(btn_ping)

        btn_port = QPushButton("Port Tara")
        btn_port.setObjectName("TablePortBtn")
        btn_port.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_port.clicked.connect(lambda checked=False, tip=target_ip: self._send_to_port_scan(tip))
        action_layout.addWidget(btn_port)

        self.table.setCellWidget(row, 5, action_widget)

    def _send_to_ping(self, target_ip: str):
        """Seçili cihazın IP'sini Ping aracına aktarır."""
        if self.on_send_to_ping:
            self.on_send_to_ping(target_ip)

    def _send_to_port_scan(self, target_ip: str):
        """Seçili cihazın IP'sini Port Tarayıcı aracına aktarır (otomatik tarama başlatmaz)."""
        if self.on_send_to_port_scan:
            self.on_send_to_port_scan(target_ip)

    def _on_progress(self, current: int, total: int):
        """İlerleme çubuğunu günceller."""
        self.progress_bar.setValue(current)

    def _on_status_changed(self, msg: str):
        """Durum bildirimini günceller."""
        self.lbl_status.setText(msg)

    def _on_error(self, err: str):
        """Hata bildirimini gösterir."""
        self.lbl_status.setText(f"⚠️ {err}")

    def _on_scan_finished(self):
        """Tarama bittiğinde butonları eski durumuna getirir."""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_clear.setEnabled(True)
        self.input_cidr.setEnabled(True)
        self.combo_adapters.setEnabled(True)

        reachable_count = sum(1 for d in self._all_devices if d.status == "Erişilebilir")
        total_scanned = len(self._all_devices)

        if reachable_count == 0 and total_scanned > 0:
            self.lbl_status.setText("ℹ️ Tarama bitti. Ping yanıtı veren cihaz bulunamadı; güvenlik duvarı veya ICMP engeli olabilir.")
        else:
            self.lbl_status.setText(f"✅ Tarama tamamlandı. {total_scanned} IP tarandı, {reachable_count} aktif cihaz tespit edildi.")

    def _apply_filter(self):
        """Yanıtsız cihazları gösterme filtresini uygular."""
        self.table.setRowCount(0)
        show_unreachable = self.chk_show_unreachable.isChecked()
        for device in self._all_devices:
            if device.status == "Erişilebilir" or show_unreachable:
                self._insert_table_row(device)

    def clear_table(self):
        """Tabloyu ve RAM listesini sıfırlar."""
        self.table.setRowCount(0)
        self._all_devices.clear()
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Ekran temizlendi.")

    def cleanup(self):
        """Pencere kapanırken aktif taramayı sonlandırır."""
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
