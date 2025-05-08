# 🌡️ Hệ thống Giám sát và Dự báo Chất lượng Không khí 📊

![Logo Dự án]([https://via.placeholder.com/150](https://upload.wikimedia.org/wikipedia/vi/5/5a/Logo_tr%C6%B0%E1%BB%9Dng_%C4%90%E1%BA%A1i_h%E1%BB%8Dc_C%C3%B4ng_ngh%E1%BB%87_th%C3%B4ng_tin_v%C3%A0_Truy%E1%BB%81n_th%C3%B4ng_Vi%E1%BB%87t_-_H%C3%A0n%2C_%C4%90%E1%BA%A1i_h%E1%BB%8Dc_%C4%90%C3%A0_N%E1%BA%B5ng.svg)) <!-- Thay bằng logo thực tế nếu có -->

Hệ thống IoT này được phát triển để **giám sát và dự báo chất lượng không khí** trong phòng, đảm bảo môi trường an toàn và lành mạnh. Dự án sử dụng **ESP32** để thu thập dữ liệu cảm biến, **Raspberry Pi 4** làm node trung tâm với **MQTT Broker**, **web server** sử dụng Apache với PHP, và mô hình **Prophet** để dự báo, cùng **FreeRTOS** để quản lý đa nhiệm trên ESP32. 🎯

## 📋 Mục lục
- [Tổng quan](#-tổng-quan)
- [Tính năng](#-tính-năng)
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Yêu cầu](#-yêu-cầu)
- [Cài đặt](#-cài-đặt)
- [Sử dụng](#-sử-dụng)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Đóng góp](#-đóng-góp)
- [Giấy phép](#-giấy-phép)
- [Tài liệu tham khảo](#-tài-liệu-tham-khảo)

## 🌍 Tổng quan

Hệ thống giám sát các thông số môi trường như **nhiệt độ**, **độ ẩm**, **bụi mịn (PM2.5)**, **AQI** theo thời gian thực. Sử dụng mô hình **Prophet** để dự báo xu hướng chất lượng không khí (AQI, PM2.5), nhiệt độ, độ ẩm và tự động điều khiển các thiết bị như máy lọc không khí hoặc điều hòa qua relay. 💡

### 🎯 Mục tiêu
- Giám sát chất lượng không khí thời gian thực.
- Dự báo AQI và PM2.5 để ra quyết định chủ động.
- Tự động hóa điều khiển thiết bị.
- Cung cấp giao diện web bằng Apache/PHP để theo dõi và điều khiển từ xa.

## ✨ Tính năng

- **Giám sát thời gian thực**: Thu thập dữ liệu từ cảm biến (DHT11, GP2Y1010AU0F) qua ESP32. 📡
- **Dự báo chất lượng không khí**: Dự đoán AQI và PM2.5 trong 24 giờ tới bằng Prophet. 🔮
- **Điều khiển tự động**: Bật/tắt máy lọc không khí và điều hòa qua relay. ⚙️
- **Giao diện web**: Hiển thị dữ liệu và dự báo, hỗ trợ điều khiển từ xa bằng Apache và PHP. 🌐
- **Lưu trữ dữ liệu**: Lưu vào MySQL/SQLite. 💾
- **Đa nhiệm**: FreeRTOS trên ESP32 quản lý các tác vụ hiệu quả. 🛠️
- **Mở rộng**: Hỗ trợ thêm cảm biến và áp dụng cho nhiều môi trường. 🌱

## 🏗️ Kiến trúc hệ thống

Hệ thống bao gồm:
- **Node Slave (ESP32)**:
  - Thu thập dữ liệu cảm biến.
  - Gửi dữ liệu qua topic MQTT `sensors/data`.
  - Nhận lệnh điều khiển qua topic `control/relay`.
- **Node Trung tâm (Raspberry Pi 4)**:
  - Chạy **MQTT Broker** (Node-RED/Mosquitto).
  - Chạy **web server** với Apache và PHP để hiển thị dữ liệu và dự báo.
  - Chạy mô hình **Prophet** để dự báo.
  - Lưu trữ dữ liệu trong MySQL/SQLite.

![Sơ đồ Kiến trúc](https://via.placeholder.com/600x300) <!-- Thay bằng sơ đồ thực tế nếu có -->

## 📦 Yêu cầu

### Phần cứng
| Thành phần         | Yêu cầu                              |
|--------------------|--------------------------------------|
| **Node Slave**     | ESP32 DevKitC, cảm biến (DHT11 GP2Y1010AU0F), relay, OLED SSD1306 (tùy chọn) |
| **Node Trung tâm** | Raspberry Pi 4 (RAM 4GB/8GB), thẻ microSD (16GB+), nguồn 5V/3A |
| **Kết nối**        | Router WiFi ổn định                  |

### Phần mềm
| Thành phần         | Yêu cầu                              |
|--------------------|--------------------------------------|
| **Node Slave**     | Arduino IDE, thư viện FreeRTOS, PubSubClient, DHT, Adafruit_BMP280 |
| **Node Trung tâm** | Raspberry Pi OS (64-bit), Apache2, PHP, Node-RED/Mosquitto, Python 3 (Prophet, Pandas, NumPy, mysql-connector-python), VS Code |
| **Khác**           | Trình duyệt web                      |

## 🚀 Cài đặt

### 1. Chuẩn bị phần cứng
1. Kết nối cảm biến và relay với ESP32 theo sơ đồ chân.
2. Cấp nguồn cho ESP32 và Raspberry Pi 4.
3. Kết nối cả hai vào cùng mạng WiFi.

### 2. Cài đặt phần mềm
#### Node Slave (ESP32)
1. Cài [Arduino IDE](https://www.arduino.cc/en/software).
2. Thêm board ESP32:
   - `File > Preferences`, thêm URL: `https://dl.espressif.com/dl/package_esp32_index.json`.
   - `Tools > Board > Boards Manager`, cài `esp32`.
3. Cài thư viện:
   - FreeRTOS: Tích hợp trong ESP32 Arduino Core.
   - PubSubClient, DHT qua `Manage Libraries`.
4. Mở `src/esp32_node_slave/esp32_node_slave.ino`, cấu hình WiFi và MQTT Broker.
5. Biên dịch và tải code lên ESP32.

#### Node Trung tâm (Raspberry Pi 4)
1. Cài Raspberry Pi OS:
   - Tải [Raspberry Pi Imager](https://www.raspberrypi.com/software/), ghi OS vào thẻ microSD.
   - Khởi động và cấu hình WiFi.
2. Cài Apache và PHP:
   ```bash
   sudo apt update
   sudo apt install apache2 php libapache2-mod-php
   sudo systemctl restart apache2
   ```
3. Cài Node-RED:
   ```bash
   bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
   node-red-start
   ```
4. Cài Mosquitto (tùy chọn):
   ```bash
   sudo apt install mosquitto mosquitto-clients
   ```
5. Cài Python và thư viện:
   ```bash
   sudo apt install python3 python3-pip
   pip3 install prophet pandas numpy mysql-connector-python
   ```
6. Cài MySQL:
   ```bash
   sudo apt install mysql-server
   sudo mysql_secure_installation
   ```
7. Sao chép `src/raspberry_pi4` vào Raspberry Pi, cấu hình trong `config.php` (cho Apache/PHP) và `config.py` (cho Prophet).
8. Đặt tệp PHP (ví dụ: `index.php`) vào `/var/www/html/` và chỉnh sửa để hiển thị dữ liệu từ cơ sở dữ liệu.
9. Chạy script Prophet:
   ```bash
   cd src/raspberry_pi4/prophet
   python3 forecast.py
   ```

### 3. Kiểm tra
- Truy cập `http://<IP_Raspberry_Pi>` để xem giao diện web Apache/PHP.
- Kiểm tra dữ liệu cảm biến và dự báo.
- Thử điều khiển relay qua web.

## 🎮 Sử dụng

1. **Khởi động**:
   - Cấp nguồn cho ESP32 và Raspberry Pi 4.
   - Đảm bảo kết nối WiFi.
2. **Theo dõi**:
   - Truy cập `http://<IP_Raspberry_Pi>`.
   - Xem dữ liệu thời gian thực và dự báo.
3. **Điều khiển**:
   - Bật/tắt thiết bị qua giao diện web.
   - Hệ thống tự động điều chỉnh dựa trên ngưỡng (xem `config.php`).
4. **Báo cáo**:
   - Tải báo cáo từ cơ sở dữ liệu qua PHP.

## 📂 Cấu trúc dự án

```
air_quality_monitoring/
├── src/
│   ├── esp32_node_slave/
│   │   └── esp32_node_slave.ino
│   └── raspberry_pi4/
│       ├── web_server/
│       │   ├── index.php
│       │   └── config.php
│       ├── prophet/
│       │   └── forecast.py
│       └── config.py
├── README.md
└── LICENSE
```

## 🤝 Đóng góp

1. Fork repository.
2. Tạo branch: `git checkout -b feature/ten-chuc-nang`.
3. Commit: `git commit -m "Mô tả thay đổi"`.
4. Push: `git push origin feature/ten-chuc-nang`.
5. Tạo Pull Request.

Xem [CONTRIBUTING.md](CONTRIBUTING.md) để biết thêm chi tiết.

## 📜 Giấy phép

[MIT License](LICENSE).

## 📚 Tài liệu tham khảo

- [ESP32 Technical Reference Manual](https://www.espressif.com/en/support/documents/technical-documents)
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [MQTT Version 5.0](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html)
- [Prophet Documentation](https://facebook.github.io/prophet/docs/quick_start.html)
- [Apache Documentation](https://httpd.apache.org/docs/)
- [PHP Manual](https://www.php.net/manual/en/)
