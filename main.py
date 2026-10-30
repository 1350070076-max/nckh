from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Bản đồ Quan sát Môi trường",
    description="Trang xem vị trí và các thông số đo đạc thực tế."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "nckh_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

@app.get("/", summary="Lời chào mở đầu")
def trang_chu():
    return {"thong_bao": "Ứng dụng đang chạy rất tốt nhé!"}

@app.get("/api/spatial-data", summary="Lấy danh sách các điểm trên bản đồ")
def lay_diem_ban_do():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(
                    json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'geometry', ST_AsGeoJSON(geom)::json,
                            'properties', json_build_object(
                                'id', id,
                                'name', name,
                                'lst_value', lst_value,
                                'ndvi_value', ndvi_value,
                                'recorded_at', recorded_at::text
                            )
                        )
                    ),
                    json_build_array()
                )
            ) FROM spatial_indicators;
        """
        cur.execute(query)
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if row and len(row) > 0 and row[0] is not None:
            return row[0]
            
        return {"type": "FeatureCollection", "features": []}
        
    except Exception as e:
        if cur: cur.close()
        if conn: conn.close()
        return {"thong_bao_loi": f"Không lấy được dữ liệu: {str(e)}"}

# 1. API Đăng nhập & Phân quyền (Chuẩn biến tai_khoan / mat_khau)
class ThongTinDangNhap(BaseModel):
    tai_khoan: str
    mat_khau: str

@app.post("/api/dang-nhap", summary="Đăng nhập hệ thống phân quyền")
def xu_ly_dang_nhap(data: ThongTinDangNhap):
    if data.tai_khoan == "admin" and data.mat_khau == "admin123":
        return {
            "trang_thai": "thanh_cong", 
            "quyen": "admin", 
            "thong_bao": "Đăng nhập thành công quyền Quản trị viên (Hiển thị GEE/AI)"
        }
    elif data.tai_khoan == "user" and data.mat_khau == "123456":
        return {
            "trang_thai": "thanh_cong", 
            "quyen": "user", 
            "thong_bao": "Đăng nhập thành công quyền Người dùng thường"
        }
    else:
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu!")

# 2. API Lọc dữ liệu theo ngưỡng (Cho Mai dùng)
@app.get("/api/spatial-data/filter", summary="Lọc danh sách theo ngưỡng chỉ số")
def loc_du_lieu_theo_nguong(
    min_lst: Optional[float] = None,
    max_lst: Optional[float] = None,
    min_ndvi: Optional[float] = None
):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        sql = """
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(
                    json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'geometry', ST_AsGeoJSON(geom)::json,
                            'properties', json_build_object(
                                'id', id,
                                'name', name,
                                'lst_value', lst_value,
                                'ndvi_value', ndvi_value,
                                'recorded_at', recorded_at::text
                            )
                        )
                    ),
                    json_build_array()
                )
            ) FROM spatial_indicators WHERE 1=1
        """
        
        params = []
        if min_lst is not None:
            sql += " AND lst_value >= %s"
            params.append(min_lst)
        if max_lst is not None:
            sql += " AND lst_value <= %s"
            params.append(max_lst)
        if min_ndvi is not None:
            sql += " AND ndvi_value >= %s"
            params.append(min_ndvi)

        cur.execute(sql, tuple(params) if params else None)
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        if row and len(row) > 0 and row[0] is not None:
            return row[0]
            
        return {"type": "FeatureCollection", "features": []}
        
    except Exception as e:
        if cur: cur.close()
        if conn: conn.close()
        return {"thong_bao_loi": f"Lỗi lọc dữ liệu: {str(e)}"}

# 3. API Lấy danh sách 167 phường
@app.get("/api/spatial-data/wards", summary="Lấy danh sách 167 phường")
def lay_danh_sach_phuong(limit: int = 167):
    return {
        "type": "FeatureCollection",
        "total_wards": limit,
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[106.6, 10.7], [106.7, 10.7], [106.7, 10.8], [106.6, 10.8], [106.6, 10.7]]]
                },
                "properties": {
                    "ward_id": 1,
                    "ward_name": "Phường mẫu số 1",
                    "environmental_index": 85.5
                }
            }
        ]
    }