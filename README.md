# MyIT - IT Destek & Sistem Yönetim Paneli

Bilişim uzmanları için geliştirilen; sistem donanımı, ağ kontrolleri, hızlı bakım araçları ve envanter yönetimini tek bir merkezde toplayan IT yönetim paneli.

## Özellikler
- 💻 **Sistem & Donanım:** Anlık CPU, RAM, Disk kullanımı ve detaylı sistem bilgileri.
- 🌐 **Ağ Teşhisi:** IP yapılandırması, ping testleri, DNS temizleme, port/cihaz tarama.
- 🛠️ **Hızlı IT Araçları:** Servis yönetimi (Spooler, Windows Update vb.), geçici dosya temizliği, hızlı komutlar.
- 📋 **Envanter & Notlar:** Cihaz ve destek kayıtlarının takibi.

## Çalıştırma
```powershell
python -m myit.main
```

## Sürüm Notları
- **v0.1.2:** Ağ Araçları modülüne **TCP Port Tarayıcı** eklendi. Standart connect() ile tek hedef üzerinde hazır (24 yaygın port) veya özel port listeleri/aralıkları (maks. 256 port) tarama, canlı durum ve gecikme tablosu, filtreleme ve Ağ Keşfi listesinden hedef aktarma desteği getirildi.
- **v0.1.1:** Ağ Araçları modülüne **Yerel Ağ Keşfi (Network Discovery)** eklendi. Aktif ağ bağdaştırıcısı tespiti, otomatik CIDR hesaplama, eşzamanlı ICMP ping taraması, canlı sonuç tablosu (IP, DNS Hostname, MAC adresi, durum, gecikme) ve bulunan cihaza doğrudan Ping gönderme desteği getirildi.
- **v0.1.0:** Ağ Araçları modülüne ilk işlevsel araç olarak **ICMP Ping Teşhis Aracı** eklendi (4 paketlik veya sürekli mod, canlı çıktı, paket kaybı ve ortalama gecikme hesaplaması).
- **v0.0.2:** Midnight Blue renk paletiyle geliştirilen modern, sade masaüstü arayüzü, koyu/açık dinamik tema ve daraltılabilir menü eklendi.
