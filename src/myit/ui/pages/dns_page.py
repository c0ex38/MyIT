"""MyIT DNS Araçları arayüz sayfası.

Bu modül; alan adı girilerek A, AAAA, MX, NS, TXT, CNAME, SOA ve Tümü
kayıt türlerini sistem veya özel DNS sunucusu üzerinden sorgulayan,
sonuç tablosu ve durum paneli sunan kullanıcı arayüzünü içerir.
"""

from typing import List, Optional
from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from myit.modules.network.dns_service import (
    SUPPORTED_RECORD_TYPES,
    DnsQueryWorker,
    DnsRecordItem,
    DnsQueryResult,
    validate_dns_server,
    validate_domain,
)


class DnsPage(QWidget):
    """DNS Araçları arayüz sayfası."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[QThread] = None
        self._worker: Optional[DnsQueryWorker] = None

        self._all_records: List[DnsRecordItem] = []
        self._init_ui()

    def _init_ui(self):
        """Arayüz bileşenlerini kurar."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # 1. Başlık ve Açıklama
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        title = QLabel("DNS Araçları")
        title.setObjectName("PageHeaderTitle")
        header_layout.addWidget(title)

        subtitle = QLabel("Alan adı kayıtlarını ve DNS yanıtlarını sorgulayın.")
        subtitle.setObjectName("PageHeaderSubtitle")
        header_layout.addWidget(subtitle)

        notice_lbl = QLabel("ℹ️ Standart DNS çözümleme (A, AAAA, MX, NS, TXT, CNAME, SOA) desteklenir. Yalnızca oturum verisi görüntülenir.")
        notice_lbl.setObjectName("DiscoveryNoticeLabel")
        header_layout.addWidget(notice_lbl)

        layout.addLayout(header_layout)

        # 2. Kontrol Kartı (Domain, Kayıt Türü, DNS Sunucu Modu, Timeout ve Butonlar)
        control_card = QFrame()
        control_card.setObjectName("DnsControlCard")
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(18, 16, 18, 16)
        control_layout.setSpacing(12)

        # Satır 1: Alan Adı ve Kayıt Türü
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        lbl_domain = QLabel("Alan Adı:")
        lbl_domain.setObjectName("FieldLabel")
        row1.addWidget(lbl_domain)

        self.input_domain = QLineEdit()
        self.input_domain.setObjectName("DnsInput")
        self.input_domain.setPlaceholderText("Örn: example.com, google.com")
        self.input_domain.returnPressed.connect(self.start_query)
        row1.addWidget(self.input_domain, 3)

        lbl_type = QLabel("Kayıt Türü:")
        lbl_type.setObjectName("FieldLabel")
        row1.addWidget(lbl_type)

        self.combo_type = QComboBox()
        self.combo_type.setObjectName("DnsCombo")
        self.combo_type.addItem("Tümü (All)", "ALL")
        for rt in SUPPORTED_RECORD_TYPES:
            self.combo_type.addItem(rt, rt)
        row1.addWidget(self.combo_type, 1)

        control_layout.addLayout(row1)

        # Satır 2: DNS Sunucusu Seçimi ve Timeout
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        lbl_server_mode = QLabel("DNS Sunucusu:")
        lbl_server_mode.setObjectName("FieldLabel")
        row2.addWidget(lbl_server_mode)

        self.combo_server_mode = QComboBox()
        self.combo_server_mode.setObjectName("DnsCombo")
        self.combo_server_mode.addItem("Sistem Varsayılanı", "SYSTEM")
        self.combo_server_mode.addItem("Özel DNS Sunucusu", "CUSTOM")
        self.combo_server_mode.currentIndexChanged.connect(self._on_server_mode_changed)
        row2.addWidget(self.combo_server_mode, 2)

        self.input_custom_server = QLineEdit()
        self.input_custom_server.setObjectName("DnsInput")
        self.input_custom_server.setPlaceholderText("DNS IP (Örn: 8.8.8.8, 1.1.1.1)")
        self.input_custom_server.setEnabled(False)
        self.input_custom_server.returnPressed.connect(self.start_query)
        row2.addWidget(self.input_custom_server, 2)

        lbl_timeout = QLabel("Zaman Aşımı (sn):")
        lbl_timeout.setObjectName("FieldLabel")
        row2.addWidget(lbl_timeout)

        self.spin_timeout = QDoubleSpinBox()
        self.spin_timeout.setObjectName("PortTimeoutSpin")
        self.spin_timeout.setRange(0.5, 10.0)
        self.spin_timeout.setSingleStep(0.5)
        self.spin_timeout.setValue(2.0)
        self.spin_timeout.setDecimals(1)
        row2.addWidget(self.spin_timeout, 1)

        control_layout.addLayout(row2)

        # Satır 3: Butonlar ve Durum Özeti
        row3 = QHBoxLayout()
        row3.setSpacing(10)

        self.btn_query = QPushButton("Sorgula")
        self.btn_query.setObjectName("DnsQueryBtn")
        self.btn_query.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_query.clicked.connect(self.start_query)
        row3.addWidget(self.btn_query)

        self.btn_stop = QPushButton("Durdur")
        self.btn_stop.setObjectName("DnsStopBtn")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_query)
        row3.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("Temizle")
        self.btn_clear.setObjectName("DnsClearBtn")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_table)
        row3.addWidget(self.btn_clear)

        row3.addStretch()

        self.lbl_record_count = QLabel("Toplam Kayıt: 0")
        self.lbl_record_count.setObjectName("PortSummaryLabel")
        row3.addWidget(self.lbl_record_count)

        control_layout.addLayout(row3)

        # Durum bildirim etiketi
        self.lbl_status = QLabel("Hazır. Bir alan adı girip 'Sorgula' butonuna basın.")
        self.lbl_status.setObjectName("DnsStatusLabel")
        control_layout.addWidget(self.lbl_status)

        layout.addWidget(control_card)

        # 3. Sonuç Tablosu
        self.table = QTableWidget(0, 4)
        self.table.setObjectName("DiscoveryTable")
        self.table.setHorizontalHeaderLabels([
            "Kayıt Türü",
            "Değer",
            "TTL (sn)",
            "Ek Bilgi (Öncelik vb.)",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

    def _on_server_mode_changed(self):
        """DNS sunucu modu değiştiğinde IP kutusunu etkinleştirir/devre dışı bırakır."""
        is_custom = (self.combo_server_mode.currentData() == "CUSTOM")
        self.input_custom_server.setEnabled(is_custom)
        if is_custom:
            self.input_custom_server.setFocus()

    def start_query(self):
        """Alan adı ve sunucu parametrelerini doğrular; sorguyu başlatır."""
        raw_domain = self.input_domain.text()
        is_valid, err_msg, clean_domain = validate_domain(raw_domain)

        if not is_valid:
            self.lbl_status.setText(f"⚠️ {err_msg}")
            return

        # Özel sunucu kontrolü
        custom_server = None
        if self.combo_server_mode.currentData() == "CUSTOM":
            raw_server = self.input_custom_server.text()
            valid_srv, srv_msg, srv_ip = validate_dns_server(raw_server)
            if not valid_srv:
                self.lbl_status.setText(f"⚠️ {srv_msg}")
                return
            custom_server = srv_ip

        self.clear_table()

        selected_type = self.combo_type.currentData()
        timeout_val = float(self.spin_timeout.value())

        # Kontrolleri kilitle
        self.btn_query.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_clear.setEnabled(False)
        self.input_domain.setEnabled(False)
        self.combo_type.setEnabled(False)
        self.combo_server_mode.setEnabled(False)
        self.input_custom_server.setEnabled(False)
        self.spin_timeout.setEnabled(False)

        srv_desc = custom_server if custom_server else "Sistem Varsayılanı"
        self.lbl_status.setText(f"⏳ {clean_domain} için {selected_type} kayıtları sorgulanıyor ({srv_desc})...")

        # İş parçacığını başlat
        self._thread = QThread()
        self._worker = DnsQueryWorker(
            domain=clean_domain,
            query_type=selected_type,
            custom_server=custom_server,
            timeout_sec=timeout_val,
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.record_received.connect(self._on_record_received)
        self._worker.status_changed.connect(self._on_status_changed)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_query_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def stop_query(self):
        """Devam eden DNS sorgu dizisini güvenle durdurur."""
        if self._worker:
            self._worker.stop()
            self.lbl_status.setText("⏹️ DNS sorgusu durduruluyor...")

    def _on_record_received(self, item: DnsRecordItem):
        """Her yeni DNS kaydı geldiğinde tabloya ekler."""
        self._all_records.append(item)
        self.lbl_record_count.setText(f"Toplam Kayıt: {len(self._all_records)}")
        self._insert_table_row(item)

    def _insert_table_row(self, item: DnsRecordItem):
        """Tabloya yeni sonuç satırı ekler."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Tür
        item_type = QTableWidgetItem(item.record_type)
        item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, item_type)

        # Değer
        item_val = QTableWidgetItem(item.value)
        item_val.setToolTip(item.value)
        self.table.setItem(row, 1, item_val)

        # TTL
        ttl_str = str(item.ttl) if item.ttl is not None else "-"
        item_ttl = QTableWidgetItem(ttl_str)
        item_ttl.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, item_ttl)

        # Ek Bilgi
        item_extra = QTableWidgetItem(item.extra_info)
        self.table.setItem(row, 3, item_extra)

    def _on_status_changed(self, msg: str):
        """Durum bildirimini günceller."""
        self.lbl_status.setText(msg)

    def _on_error(self, err: str):
        """Hata mesajı gösterir."""
        self.lbl_status.setText(f"⚠️ {err}")

    def _on_query_finished(self):
        """Sorgu tamamlandığında kontrolleri eski durumuna getirir."""
        self.btn_query.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_clear.setEnabled(True)
        self.input_domain.setEnabled(True)
        self.combo_type.setEnabled(True)
        self.combo_server_mode.setEnabled(True)
        self.input_custom_server.setEnabled(self.combo_server_mode.currentData() == "CUSTOM")
        self.spin_timeout.setEnabled(True)

        count = len(self._all_records)
        self.lbl_record_count.setText(f"Toplam Kayıt: {count}")

        if not self.lbl_status.text().startswith("⚠️") and not self.lbl_status.text().startswith("⏹️"):
            if count == 0:
                self.lbl_status.setText("ℹ️ Sorgu tamamlandı, ancak yanıt kaydı bulunamadı (NoAnswer / NXDOMAIN).")
            else:
                self.lbl_status.setText(f"✅ DNS sorguları tamamlandı. {count} kayıt listelendi.")

    def clear_table(self):
        """Tabloyu ve RAM listesini temizler."""
        self.table.setRowCount(0)
        self._all_records.clear()
        self.lbl_record_count.setText("Toplam Kayıt: 0")
        self.lbl_status.setText("Ekran temizlendi.")

    def cleanup(self):
        """Pencere kapanırken aktif worker'ı sonlandırır."""
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
