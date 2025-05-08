#!/usr/bin/env python3
import pandas as pd
from sqlalchemy import create_engine
from prophet import Prophet
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging
import time

# --- Cấu hình Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Cấu hình kết nối MySQL ---
DB_CONFIG = {
    'user': 'admin',
    'password': 'admin',
    'host': 'localhost',
    'database': 'sensor_data',
}

# --- Cấu hình các node ---
NODES_CONFIG = {
    'node1': {
        'data_table': 'sensor_datanode1',
        'forecast_table': 'forecast_results_node1'
    },
    'node2': {
        'data_table': 'sensor_datanode2',
        'forecast_table': 'forecast_results_node2'
    }
}
COLUMNS_TO_FORECAST = ['temperature', 'humidity', 'dust_density', 'aqi']

def fetch_data_from_mysql(table_name, limit=None):
    """Kết nối MySQL và lấy dữ liệu lịch sử."""
    start_time = time.time()
    try:
        connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        engine = create_engine(connection_string)
        query = f"SELECT timestamp, {', '.join(COLUMNS_TO_FORECAST)} FROM {table_name} ORDER BY timestamp ASC"
        if limit:
            query += f" LIMIT {limit}"

        df = pd.read_sql_query(query, engine)
        logging.info(f"Đã lấy {len(df)} bản ghi từ MySQL (bảng {table_name}).")

        # Chuyển đổi timestamp sang datetime với múi giờ UTC
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

        # Suy ra tần suất dữ liệu
        inferred_freq = pd.infer_freq(df['timestamp'])
        if inferred_freq is None:
            logging.warning("Không thể suy ra tần suất dữ liệu. Sử dụng tần suất mặc định 'h'.")
        logging.info(f"Tần suất dữ liệu suy ra: {inferred_freq}")

        # Ép kiểu số, xử lý lỗi thành NaN
        for col in COLUMNS_TO_FORECAST:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Kiểm tra và nội suy giá trị thiếu nếu cần
        missing_ratio = df[COLUMNS_TO_FORECAST].isnull().mean()
        for col, ratio in missing_ratio.items():
            if ratio > 0.1:  # Ngưỡng 10%
                df[col] = df[col].interpolate(method='linear')
                logging.info(f"Đã nội suy giá trị thiếu cho cột {col} (bảng {table_name}).")
        logging.info(f"Kiểm tra dữ liệu thiếu (NaN) cho bảng {table_name}:")
        logging.info(df.isnull().sum())

        logging.info(f"Lấy dữ liệu từ bảng {table_name} mất {time.time() - start_time:.2f} giây")
        return df

    except Exception as err:
        logging.error(f"Lỗi khi lấy dữ liệu từ bảng {table_name}: {err}")
        return None
    finally:
        if 'engine' in locals():
            engine.dispose()
            logging.info("Đã đóng kết nối MySQL.")

def preprocess_for_prophet(df, value_column, node_name):
    """Chuẩn bị DataFrame cho mô hình Prophet."""
    start_time = time.time()
    df_prophet = df[['timestamp', value_column]].copy()
    df_prophet.rename(columns={'timestamp': 'ds', value_column: 'y'}, inplace=True)

    # Loại bỏ múi giờ trong cột ds
    df_prophet['ds'] = df_prophet['ds'].dt.tz_localize(None)

    # Kiểm tra giá trị vô cực
    if df_prophet['y'].isin([float('inf'), -float('inf')]).any():
        logging.error(f"Dữ liệu chứa giá trị vô cực trong cột {value_column} (node {node_name}).")
        return None

    # Loại bỏ các dòng có 'ds' trùng lặp
    duplicates = df_prophet.duplicated(subset=['ds']).sum()
    if duplicates > 0:
        logging.info(f"Đã loại bỏ {duplicates} bản ghi trùng lặp trong cột {value_column} (node {node_name}).")
    df_prophet = df_prophet.drop_duplicates(subset=['ds'], keep='last')

    # Sắp xếp theo 'ds'
    df_prophet = df_prophet.sort_values('ds')

    logging.info(f"Dữ liệu đã chuẩn bị cho Prophet ({value_column}, node {node_name}): {len(df_prophet)} bản ghi.")
    logging.info(f"Phạm vi thời gian: {df_prophet['ds'].min()} đến {df_prophet['ds'].max()}")
    logging.info(f"Tiền xử lý cho node {node_name} mất {time.time() - start_time:.2f} giây")
    return df_prophet

def train_and_forecast(df_prophet, periods=24, freq='h', node_name=''):
    """Huấn luyện mô hình Prophet và dự báo tương lai."""
    start_time = time.time()
    if df_prophet is None or df_prophet.empty or len(df_prophet) < 2:
        logging.warning(f"Không đủ dữ liệu hợp lệ để huấn luyện mô hình (node {node_name}).")
        return None, None

    # Kiểm tra độ dài dữ liệu
    time_range = df_prophet['ds'].max() - df_prophet['ds'].min()
    if time_range < timedelta(days=7):
        logging.warning(f"Dữ liệu chỉ kéo dài {time_range} (node {node_name}), quá ngắn để mô hình hóa mùa vụ.")

    # Khởi tạo mô hình Prophet với mùa vụ
    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=False,  # Tắt mùa vụ hàng tuần do dữ liệu ngắn
        yearly_seasonality=False,
        n_changepoints=10  # Tối ưu hiệu suất
    )

    # Huấn luyện mô hình
    logging.info(f"Bắt đầu huấn luyện mô hình Prophet cho cột '{df_prophet.columns[1]}' (node {node_name})...")
    try:
        model.fit(df_prophet)
        logging.info("Huấn luyện hoàn tất.")
    except Exception as e:
        logging.error(f"Lỗi trong quá trình huấn luyện Prophet (node {node_name}): {e}")
        logging.error(f"Dữ liệu đầu vào cho Prophet ('y'):\n{df_prophet['y'].describe()}")
        return None, None

    # Suy ra tần suất hoặc dùng mặc định
    inferred_freq = pd.infer_freq(df_prophet['ds'])
    freq = inferred_freq if inferred_freq else 'h'
    future = model.make_future_dataframe(periods=periods, freq=freq)
    logging.info(f"Tạo future dataframe đến: {future['ds'].iloc[-1]} với tần suất: {freq} (node {node_name})")

    # Dự báo
    logging.info(f"Bắt đầu dự báo (node {node_name})...")
    forecast = model.predict(future)
    logging.info("Dự báo hoàn tất.")
    logging.info(f"Huấn luyện và dự báo mất {time.time() - start_time:.2f} giây (node {node_name})")

    return model, forecast

def process_forecast(forecast_data, num_forecast_periods=24):
    """Lấy ra các giá trị dự báo cho 24 giờ tới."""
    future_predictions = forecast_data[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(num_forecast_periods)
    return future_predictions

def save_forecast_to_db(final_forecast_df, forecast_table):
    """Ghi kết quả dự báo vào bảng MySQL."""
    try:
        connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        engine = create_engine(connection_string)
        connection = engine.raw_connection()
        cursor = connection.cursor()

        # Chuẩn bị câu lệnh SQL
        insert_sql = f"""
        INSERT INTO {forecast_table} (timestamp, temperature_forecast, humidity_forecast, dust_density_forecast, aqi_forecast)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            temperature_forecast = VALUES(temperature_forecast),
            humidity_forecast = VALUES(humidity_forecast),
            dust_density_forecast = VALUES(dust_density_forecast),
            aqi_forecast = VALUES(aqi_forecast)
        """

        # Chuẩn bị dữ liệu để insert
        records_to_insert = []
        for _, row in final_forecast_df.iterrows():
            records_to_insert.append((
                row['timestamp'],
                row['temperature_forecast'],
                row['humidity_forecast'],
                row['dust_density_forecast'],
                row['aqi_forecast']
            ))

        # Thực thi câu lệnh SQL
        cursor.executemany(insert_sql, records_to_insert)
        connection.commit()
        logging.info(f"Đã lưu {cursor.rowcount} bản ghi vào bảng {forecast_table} (bao gồm cả cập nhật).")

    except Exception as db_err:
        logging.error(f"Lỗi khi ghi dữ liệu vào MySQL (bảng {forecast_table}): {db_err}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
        engine.dispose()
        logging.info("Đã đóng kết nối MySQL.")

def main():
    logging.info("=== Bắt đầu quy trình dự báo ===")
    overall_start_time = time.time()

    # Lặp qua từng node
    for node_name, config in NODES_CONFIG.items():
        logging.info(f"\n=== Bắt đầu xử lý {node_name} ===")
        start_time = time.time()

        # Lấy dữ liệu
        df_history = fetch_data_from_mysql(config['data_table'])

        if df_history is None or df_history.empty:
            logging.error(f"Không lấy được dữ liệu từ MySQL cho {node_name}. Bỏ qua node này.")
            continue

        all_forecasts = {}
        forecast_start_time = df_history['timestamp'].iloc[-1] + timedelta(hours=1)

        # Lặp qua từng cột để dự báo
        for column in COLUMNS_TO_FORECAST:
            logging.info(f"--- Xử lý cột: {column} ({node_name}) ---")

            # Tiền xử lý
            df_train = preprocess_for_prophet(df_history, column, node_name)
            if df_train is None:
                logging.warning(f"Không thể tiền xử lý dữ liệu cho cột: {column} ({node_name})")
                continue

            # Huấn luyện và dự báo
            model, forecast_result = train_and_forecast(df_train, periods=24, freq='h', node_name=node_name)
            if model is None or forecast_result is None:
                logging.warning(f"Không thể tạo dự báo cho cột: {column} ({node_name})")
                continue

            # Lấy kết quả 24h tới
            future_preds = process_forecast(forecast_result, num_forecast_periods=24)
            all_forecasts[column] = future_preds
            logging.info(f"Dự báo cho {column} ({node_name}) hoàn tất.")

            # Vẽ và lưu đồ thị
            try:
                fig = model.plot(forecast_result)
                plt.title(f"Dự báo {column} ({node_name})")
                plt.xlabel("Thời gian")
                plt.ylabel(column)
                plt.savefig(f"{node_name}_{column}_forecast.png")
                logging.info(f"Đã lưu đồ thị dự báo: {node_name}_{column}_forecast.png")
            except Exception as plot_err:
                logging.error(f"Lỗi khi lưu đồ thị {node_name}_{column}_forecast.png: {plot_err}")
            finally:
                plt.close(fig)

        # Hiển thị và lưu kết quả tổng hợp
        if all_forecasts:
            logging.info(f"\n=== Kết quả dự báo 24 giờ tới cho {node_name} ===")
            final_forecast_df = pd.DataFrame()
            if all_forecasts and COLUMNS_TO_FORECAST[0] in all_forecasts:
                final_forecast_df['timestamp'] = all_forecasts[COLUMNS_TO_FORECAST[0]]['ds']
            else:
                logging.error(f"Không có dự báo nào để tạo DataFrame tổng hợp cho {node_name}.")
                continue

            for column, forecast_df in all_forecasts.items():
                final_forecast_df[f'{column}_forecast'] = forecast_df['yhat'].round(2)

            # Làm tròn timestamp về giờ (phút và giây về 00:00) trước khi in log
            final_forecast_df['timestamp'] = pd.to_datetime(final_forecast_df['timestamp']).dt.floor('h')

            # Sắp xếp theo timestamp để đảm bảo thứ tự
            final_forecast_df = final_forecast_df.sort_values(by='timestamp')

            # In log với timestamp đã làm tròn
            print(f"\nKết quả dự báo cho {node_name}:")
            print(final_forecast_df.to_string())

            # Lưu kết quả vào CSV
            try:
                csv_filename = f"{node_name}_forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                final_forecast_df.to_csv(csv_filename, index=False)
                logging.info(f"Đã lưu kết quả dự báo vào file: {csv_filename}")
            except Exception as save_err:
                logging.error(f"Lỗi khi lưu file CSV cho {node_name}: {save_err}")

            # Lưu kết quả vào bảng MySQL
            save_forecast_to_db(final_forecast_df, config['forecast_table'])

        else:
            logging.warning(f"Không có kết quả dự báo nào được tạo cho {node_name}.")

        logging.info(f"Xử lý {node_name} mất {time.time() - start_time:.2f} giây")

    logging.info(f"Toàn bộ quy trình mất {time.time() - overall_start_time:.2f} giây")
    logging.info("=== Kết thúc quy trình dự báo ===")

if __name__ == "__main__":
    main()