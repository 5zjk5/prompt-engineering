"""Excel 预览 API — 返回文件所有 sheet 的原始数据

用于前端右侧收缩栏预览，像浏览 Excel 一样查看所有 sheet 和数据。
数据过大时返回提示信息而不返回全量数据。
"""

import os
import json
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core import config

router = APIRouter()


def _display_file_name(file_path: str) -> str:
    file_name = os.path.basename(file_path)
    parts = file_name.split("_", 1)
    if len(parts) == 2 and len(parts[0]) == 12 and all(c in "0123456789abcdef" for c in parts[0].lower()):
        return parts[1]
    return file_name


# 预览行数上限（单 sheet）
MAX_PREVIEW_ROWS = 5000
# 预览列数上限（单 sheet）
MAX_PREVIEW_COLS = 100


def _json_serial(obj):
    """JSON 序列化：处理 date/datetime 类型"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode('utf-8', errors='replace')
    raise TypeError(f"Type {type(obj)} not serializable")


@router.get("/excel-preview")
async def excel_preview(file_path: str = Query(..., description="Excel 文件绝对路径")):
    """读取 Excel 文件，返回所有 sheet 的原始数据"""
    # 安全校验：文件必须在 UPLOAD_DIR 内
    upload_dir = os.path.abspath(config.UPLOAD_DIR)
    abs_path = os.path.abspath(file_path)
    if not abs_path.startswith(upload_dir):
        raise HTTPException(status_code=403, detail="文件路径不在允许范围内")

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 判断扩展名
    _, ext = os.path.splitext(abs_path)
    ext = ext.lower()

    try:
        if ext == ".csv":
            # CSV 按 pandas 读取
            import pandas as pd
            df = pd.read_csv(abs_path)
            total_rows = len(df)
            total_cols = len(df.columns)

            if total_rows > MAX_PREVIEW_ROWS:
                return {
                    "file_name": _display_file_name(abs_path),
                    "sheets": [{
                        "name": "CSV",
                        "total_rows": total_rows,
                        "total_cols": total_cols,
                        "too_large": True,
                        "message": f"数据量过大（{total_rows} 行），不支持预览",
                    }],
                }

            columns = list(df.columns)
            rows = df.values.tolist()
            return {
                "file_name": _display_file_name(abs_path),
                "sheets": [{
                    "name": "CSV",
                    "total_rows": total_rows,
                    "total_cols": total_cols,
                    "too_large": False,
                    "columns": columns,
                    "rows": json.loads(json.dumps(rows, default=_json_serial)),
                }],
            }
        else:
            # xlsx/xls 用 openpyxl 或 pandas 读取所有 sheet
            import pandas as pd
            xls = pd.ExcelFile(abs_path)
            sheets = []
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                df = df.dropna(how="all").dropna(axis=1, how="all")
                if df.empty:
                    continue
                total_rows = len(df)
                total_cols = len(df.columns)

                if total_rows > MAX_PREVIEW_ROWS or total_cols > MAX_PREVIEW_COLS:
                    sheets.append({
                        "name": sheet_name,
                        "total_rows": total_rows,
                        "total_cols": total_cols,
                        "too_large": True,
                        "message": f"数据量过大（{total_rows} 行 x {total_cols} 列），不支持预览",
                    })
                    continue

                columns = list(df.columns)
                rows = df.values.tolist()
                sheets.append({
                    "name": sheet_name,
                    "total_rows": total_rows,
                    "total_cols": total_cols,
                    "too_large": False,
                    "columns": columns,
                    "rows": json.loads(json.dumps(rows, default=_json_serial)),
                })

            return {
                "file_name": _display_file_name(abs_path),
                "sheets": sheets,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")
