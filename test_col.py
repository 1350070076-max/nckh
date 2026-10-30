import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "nckh_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    cur = conn.cursor()
    
    # Truy vấn thẳng danh sách cột của bảng spatial_indicators
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'spatial_indicators';
    """)
    rows = cur.fetchall()
    
    print("\n========================================")
    print(" KẾT QUẢ QUÉT CỘT TRONG BẢNG spatial_indicators:")
    print("========================================")
    for r in rows:
        print(f"-> Tên cột: {r[0]} | Kiểu dữ liệu: {r[1]}")
    print("========================================\n")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Lỗi kết nối hoặc truy vấn: {e}")