"""DuckDB Excel 读取器 — 支持同一会话多文件、多 sheet、多表分析。"""

import io
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

import chardet
import duckdb
import numpy as np
import pandas as pd
import sqlparse

from app.core import config

logger = logging.getLogger(__name__)

# 常见中文编码，chardet 检测失败或读取报错时依次尝试
_FALLBACK_ENCODINGS = ["gbk", "gb2312", "gb18030", "utf-8-sig", "latin-1"]


def _detect_encoding(raw: bytes) -> str:
    """检测文件编码，chardet 失败时回退到常见中文编码"""
    result = chardet.detect(raw)
    encoding = result.get("encoding")
    if encoding:
        # 用检测到的编码试读，失败则继续尝试其他编码
        try:
            raw.decode(encoding)
            return encoding
        except (UnicodeDecodeError, LookupError):
            pass
    # chardet 检测失败或解码报错，依次尝试常见编码
    for enc in _FALLBACK_ENCODINGS:
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


def excel_colunm_format(old_name: str) -> str:
    """空格替换为下划线"""
    return old_name.strip().replace(" ", "_")


def is_chinese(text: str) -> bool:
    for char in text:
        if "\u4e00" <= char <= "\u9fa5":
            return True
    return False


def get_new_value(value: str) -> str:
    return f""""{value.replace('`', '').replace("'", '').replace('"', '')}"  """


def add_quotes_to_chinese_columns(sql: str, column_names: list = None) -> str:
    """给中文列名加双引号"""
    parsed = sqlparse.parse(sql)
    for stmt in parsed:
        _process_statement(stmt, column_names or [])
    return str(parsed[0])


def _process_statement(statement, column_names: list):
    if isinstance(statement, sqlparse.sql.IdentifierList):
        for identifier in statement.get_identifiers():
            _process_identifier(identifier, column_names)
    elif isinstance(statement, sqlparse.sql.Identifier):
        _process_identifier(statement, column_names)
    elif isinstance(statement, sqlparse.sql.TokenList):
        for item in statement.tokens:
            _process_statement(item, column_names)


def _process_identifier(identifier, column_names: list):
    if hasattr(identifier, "tokens") and identifier.value in column_names:
        if is_chinese(identifier.value):
            new_value = get_new_value(identifier.value)
            identifier.value = new_value
            identifier.normalized = new_value
            identifier.tokens = [sqlparse.sql.Token(sqlparse.tokens.Name, new_value)]
    else:
        if hasattr(identifier, "tokens"):
            for token in identifier.tokens:
                if isinstance(token, sqlparse.sql.Function):
                    _process_function(token)
                elif token.ttype in sqlparse.tokens.Name and is_chinese(token.value):
                    new_value = get_new_value(token.value)
                    token.value = new_value
                    token.normalized = new_value


def _process_function(function):
    params = list(function.get_parameters())
    for i in range(len(params)):
        param = params[i]
        if isinstance(param, sqlparse.sql.Identifier) and is_chinese(param.value):
            new_value = get_new_value(param.value)
            params[i].tokens = [sqlparse.sql.Token(sqlparse.tokens.Name, new_value)]


def csv_colunm_format(x):
    """统一转为字符串，避免类型推断错误"""
    return str(x)


def _safe_identifier(value: str, default: str = "table") -> str:
    value = re.sub(r"[^0-9a-zA-Z_]+", "_", value or "")
    value = re.sub(r"_+", "_", value).strip("_").lower()
    if not value:
        value = default
    if value[0].isdigit():
        value = f"t_{value}"
    return value[:48]


def _dedupe_columns(columns: List[str]) -> List[str]:
    seen = {}
    result = []
    for idx, column in enumerate(columns):
        name = str(column).strip() if str(column).strip() else f"column_{idx + 1}"
        if name.startswith("Unnamed"):
            name = f"column_{idx + 1}"
        base = name
        count = seen.get(base, 0)
        if count:
            name = f"{base}_{count + 1}"
        seen[base] = count + 1
        result.append(name)
    return result


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace("", np.nan)
    df = df.dropna(how="all").dropna(axis=1, how="all")
    if df.empty or len(df.columns) == 0:
        return pd.DataFrame()

    df.columns = _dedupe_columns([excel_colunm_format(str(col)) for col in df.columns])
    for column_name in df.columns:
        df[column_name] = df[column_name].astype(str)
        try:
            converted = pd.to_datetime(df[column_name], errors="raise").dt.strftime("%Y-%m-%d")
            df[column_name] = converted
            continue
        except (ValueError, TypeError):
            pass
        try:
            df[column_name] = pd.to_numeric(df[column_name])
        except (ValueError, TypeError):
            df[column_name] = df[column_name].astype(str)
    return df


def read_from_df(db, file_path: str, file_name: str, table_name: str):
    """通过 pandas DataFrame 读取文件写入 DuckDB（降级方案）"""
    with open(file_path, "rb") as f:
        raw = f.read()

    encoding = _detect_encoding(raw)

    if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        df_tmp = pd.read_excel(io.BytesIO(raw), index_col=False)
        df = pd.read_excel(
            io.BytesIO(raw), index_col=False,
            converters={i: csv_colunm_format for i in range(df_tmp.shape[1])},
        )
    elif file_name.endswith(".csv"):
        df_tmp = pd.read_csv(io.BytesIO(raw), index_col=False, encoding=encoding, on_bad_lines="skip")
        df = pd.read_csv(
            io.BytesIO(raw), index_col=False, encoding=encoding, on_bad_lines="skip",
            converters={i: csv_colunm_format for i in range(df_tmp.shape[1])},
        )
    else:
        raise ValueError(f"Unsupported file format: {file_name}")

    df = _clean_dataframe(df)
    db.register("temp_df_table", df)
    db.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_df_table")
    return table_name


def read_direct(db, file_path: str, file_name: str, table_name: str):
    """DuckDB 直接读取文件（优先方式）"""
    ext = os.path.splitext(file_path)[1].lower()

    # CSV 需要先检测编码，DuckDB 默认按 UTF-8 读取会导致非 UTF-8 文件乱码或报错
    if ext == ".csv":
        with open(file_path, "rb") as f:
            raw = f.read()
        encoding = _detect_encoding(raw)
        load_func = "read_csv"
        load_params = {}
        if encoding.lower() not in ("utf-8", "utf8"):
            load_params["encoding"] = f"'{encoding}'"
    elif ext == ".xlsx":
        load_func = "read_xlsx"
        load_params = {"empty_as_varchar": "true", "ignore_errors": "true"}
    elif ext == ".xls":
        return read_from_df(db, file_path, file_name, table_name)
    elif ext == ".json":
        load_func = "read_json_auto"
        load_params = {}
    elif ext == ".parquet":
        load_func = "read_parquet"
        load_params = {}
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    func_args = ", ".join([f"{k}={v}" for k, v in load_params.items()])
    from_exp = f"FROM {load_func}('{file_path}'{', ' + func_args if func_args else ''})"
    load_sql = f"CREATE TABLE {table_name} AS SELECT * {from_exp}"
    try:
        db.sql(load_sql)
    except Exception as e:
        logger.warning(f"DuckDB load failed, falling back to pandas: {e}")
        return read_from_df(db, file_path, file_name, table_name)


class ExcelReader:
    """会话级 Excel 读取器：一个文件/Sheet 对应一张 DuckDB 表。"""

    _instances: Dict[str, "ExcelReader"] = {}

    @classmethod
    def get_or_create(cls, conv_uid: str, file_path: str = "", file_name: str = None) -> "ExcelReader":
        if conv_uid not in cls._instances:
            cls._instances[conv_uid] = cls(conv_uid)
        reader = cls._instances[conv_uid]
        if file_path:
            reader.add_file(file_path, file_name)
        return reader

    def __init__(self, conv_uid: str):
        self.conv_uid = conv_uid
        self.temp_table_name = "temp_table"
        self.table_name = "data_analysis_table"
        self.excel_file_name = ""
        self.table_infos: List[dict] = []
        self._transformed = False

        db_path = os.path.join(config.DUCKDB_DIR, f"_chat_excel_{conv_uid}.duckdb")
        self.db: duckdb.DuckDBPyConnection = duckdb.connect(database=db_path, read_only=False)
        self._load_existing_tables()

    def _load_existing_tables(self):
        try:
            _, rows = self._run_sql("SELECT table_name FROM duckdb_tables() WHERE schema_name = 'main'")
            table_names = [row[0] for row in rows]
            for table_name in table_names:
                if not table_name.startswith("data_analysis_"):
                    continue
                suffix = table_name.replace("data_analysis_", "", 1)
                temp_table_name = f"temp_{suffix}"
                self.table_infos.append({
                    "file_name": "历史文件",
                    "sheet_name": suffix,
                    "temp_table": temp_table_name if temp_table_name in table_names else table_name,
                    "table_name": table_name,
                    "transformed": True,
                })
            self._transformed = bool(self.table_infos) and all(info["transformed"] for info in self.table_infos)
        except Exception as e:
            logger.warning(f"Failed to load existing tables: {e}")

    def close(self):
        if self.db:
            self.db.close()
            self.db = None

    def __del__(self):
        self.close()

    @property
    def curr_table(self) -> str:
        if self.table_infos:
            return self.table_infos[0]["table_name"] if self.table_infos[0].get("transformed") else self.table_infos[0]["temp_table"]
        return self.table_name if self._transformed else self.temp_table_name

    @property
    def table_names(self) -> List[str]:
        return [info["table_name"] for info in self.table_infos if info.get("transformed")]

    @property
    def pending_table_infos(self) -> List[dict]:
        pending = []
        for info in self.table_infos:
            if info.get("transformed"):
                continue
            if self._table_exists(info["table_name"]):
                info["transformed"] = True
                continue
            pending.append(info)
        self._transformed = bool(self.table_infos) and all(info.get("transformed") for info in self.table_infos)
        return pending

    def _table_exists(self, table_name: str) -> bool:
        try:
            self.db.sql(f"SELECT 1 FROM {table_name} LIMIT 1")
            return True
        except Exception:
            return False

    def _unique_table_name(self, base: str) -> str:
        name = base
        idx = 2
        while self._table_exists(name) or any(info["temp_table"] == name or info["table_name"] == name for info in self.table_infos):
            name = f"{base}_{idx}"
            idx += 1
        return name

    def _register_dataframe(self, df: pd.DataFrame, table_name: str):
        self.db.register("temp_df_table", df)
        self.db.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_df_table")
        try:
            self.db.unregister("temp_df_table")
        except Exception:
            pass

    def add_file(self, file_path: str, file_name: Optional[str] = None) -> List[dict]:
        if not file_name:
            file_name = os.path.basename(file_path)
        file_path = os.path.abspath(file_path)
        self.excel_file_name = file_name

        if any(info.get("file_path") == file_path for info in self.table_infos):
            return []

        ext = os.path.splitext(file_path)[1].lower()
        file_key = _safe_identifier(os.path.splitext(file_name)[0], "excel")
        added = []

        if ext == ".csv":
            with open(file_path, "rb") as f:
                raw = f.read()
            encoding = _detect_encoding(raw)
            df = pd.read_csv(io.BytesIO(raw), index_col=False, encoding=encoding, on_bad_lines="skip")
            df = _clean_dataframe(df)
            if not df.empty:
                suffix = self._unique_table_name(f"{file_key}_csv").replace("temp_", "")
                temp_table = self._unique_table_name(f"temp_{suffix}")
                table_name = self._unique_table_name(f"data_analysis_{suffix}")
                self._register_dataframe(df, temp_table)
                added.append({"file_path": file_path, "file_name": file_name, "sheet_name": "CSV", "temp_table": temp_table, "table_name": table_name, "transformed": False})
        elif ext in (".xlsx", ".xls"):
            xls = pd.ExcelFile(file_path)
            for sheet_idx, sheet_name in enumerate(xls.sheet_names, 1):
                df = pd.read_excel(xls, sheet_name=sheet_name, index_col=False)
                df = _clean_dataframe(df)
                if df.empty:
                    continue
                sheet_key = _safe_identifier(sheet_name, f"sheet_{sheet_idx}")
                suffix = self._unique_table_name(f"{file_key}_{sheet_key}").replace("temp_", "")
                temp_table = self._unique_table_name(f"temp_{suffix}")
                table_name = self._unique_table_name(f"data_analysis_{suffix}")
                self._register_dataframe(df, temp_table)
                added.append({"file_path": file_path, "file_name": file_name, "sheet_name": sheet_name, "temp_table": temp_table, "table_name": table_name, "transformed": False})
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        self.table_infos.extend(added)
        self._transformed = bool(self.table_infos) and all(info.get("transformed") for info in self.table_infos)
        return added

    def transform_table(self, transform_data: dict, table_info: dict = None) -> str:
        table_info = table_info or (self.table_infos[0] if self.table_infos else None)
        if not table_info:
            return self._fallback_copy_table()

        columns = transform_data.get("column_analysis", [])
        table_comment = transform_data.get("data_analysis", "")
        old_table_name = table_info["temp_table"]
        new_table_name = table_info["table_name"]

        if not columns:
            logger.warning("column_analysis is empty, falling back to direct copy")
            return self._fallback_copy_table(table_info)

        try:
            _, cl_datas = self.get_columns(old_table_name)
            old_col_name_to_type = {cl_data[0]: cl_data[1] for cl_data in cl_datas}
            select_sql_list = []
            create_columns = []
            used_new_names = set()

            for col_transform in columns:
                old_column_name = col_transform.get("old_column_name", "")
                new_column_name = _safe_identifier(col_transform.get("new_column_name", ""), "column")
                if not old_column_name or old_column_name not in old_col_name_to_type:
                    logger.warning(f"Skipping invalid column transform: {col_transform}")
                    continue
                while new_column_name in used_new_names:
                    new_column_name = f"{new_column_name}_2"
                used_new_names.add(new_column_name)
                col_transform["new_column_name"] = new_column_name
                new_column_type = old_col_name_to_type.get(old_column_name, "VARCHAR")
                select_sql_list.append(f'"{old_column_name}" AS {new_column_name}')
                create_columns.append(f"{new_column_name} {new_column_type}")

            if not select_sql_list:
                return self._fallback_copy_table(table_info)

            create_table_str = f"CREATE TABLE {new_table_name}(\n{', '.join(create_columns)}\n);"
            sql = f"""
{create_table_str}
INSERT INTO {new_table_name} SELECT {', '.join(select_sql_list)} FROM {old_table_name};
"""
            logger.info(f"Begin to transform table, SQL:\n{sql}")
            self.db.sql(sql)

            escaped_table_comment = table_comment.replace("'", "''")
            try:
                self.db.sql(f"COMMENT ON TABLE {new_table_name} IS '{escaped_table_comment}';")
            except Exception as e:
                logger.warning(f"Error while adding table comment: {e}")

            for col_transform in columns:
                new_column_name = col_transform.get("new_column_name", "")
                column_description = col_transform.get("column_description", "")
                if not new_column_name or not column_description:
                    continue
                try:
                    escaped_description = column_description.replace("'", "''")
                    self.db.sql(f"COMMENT ON COLUMN {new_table_name}.{new_column_name} IS '{escaped_description}';")
                except Exception as e:
                    logger.warning(f"Error while adding comment to column {new_column_name}: {e}")

            table_info["transformed"] = True
            self._transformed = all(info.get("transformed") for info in self.table_infos)
            return new_table_name
        except Exception as e:
            logger.error(f"transform_table failed, falling back to direct copy: {e}", exc_info=True)
            return self._fallback_copy_table(table_info)

    def _fallback_copy_table(self, table_info: dict = None) -> str:
        table_info = table_info or (self.table_infos[0] if self.table_infos else None)
        if not table_info:
            try:
                self.db.sql(f"CREATE TABLE {self.table_name} AS SELECT * FROM {self.temp_table_name}")
                self._transformed = True
            except Exception as e:
                logger.error(f"Fallback copy failed: {e}")
            return self.table_name

        try:
            self.db.sql(f"CREATE TABLE {table_info['table_name']} AS SELECT * FROM {table_info['temp_table']}")
        except Exception as e:
            logger.warning(f"Fallback copy may already exist: {e}")
        table_info["transformed"] = True
        self._transformed = all(info.get("transformed") for info in self.table_infos)
        return table_info["table_name"]

    def run(self, sql: str, table_name: str = None, df_res: bool = False, transform: bool = True):
        table_name = table_name or self.curr_table
        try:
            if table_name and f'"{table_name}"' in sql:
                sql = sql.replace(f'"{table_name}"', table_name)
            if transform:
                sql = add_quotes_to_chinese_columns(sql)
            logger.info(f"Executing SQL: {sql}")
            if df_res:
                return self.db.sql(sql).df()
            return self._run_sql(sql)
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            raise ValueError(f"Data Query Exception!\nSQL[{sql}].\nError: {e}")

    def _run_sql(self, sql: str) -> Tuple[List[str], List]:
        results = self.db.sql(sql)
        columns = [desc[0] for desc in results.description]
        return columns, results.fetchall()

    def get_df_by_sql(self, sql: str, table_name: str = None):
        return self.run(sql, table_name, df_res=True)

    def get_sample_data(self, table_name: str = None, limit: int = 5) -> Tuple[List[str], List]:
        table_name = table_name or self.curr_table
        return self.run(f"SELECT * FROM {table_name} LIMIT {limit};", transform=False)

    def get_all_sample_data(self, limit: int = 5) -> str:
        samples = []
        for info in self.table_infos:
            if not info.get("transformed"):
                continue
            columns, datas = self.get_sample_data(table_name=info["table_name"], limit=limit)
            samples.append({
                "file_name": info.get("file_name"),
                "sheet_name": info.get("sheet_name"),
                "table_name": info["table_name"],
                "columns": columns,
                "rows": datas,
            })
        return samples

    def get_create_table_sql(self, table_name: str = None) -> str:
        """生成包含表注释和列注释的 CREATE TABLE DDL。"""
        table_name = table_name or self.curr_table
        sql = f"""SELECT comment, table_name, database_name FROM duckdb_tables()
                  WHERE table_name = '{table_name}'"""
        _, datas = self._run_sql(sql)
        table_comment = datas[0][0] if datas else ""

        _, cl_datas = self.get_columns(table_name)
        ddl_sql = f"CREATE TABLE {table_name} (\n"
        column_strs = []
        for cl_data in cl_datas:
            column_name, column_type, nullable = cl_data[0], cl_data[1], cl_data[2]
            column_comment = cl_data[3] if len(cl_data) > 3 else None
            curr_sql = f"    {column_name} {column_type}"
            if nullable and str(nullable).lower() == "no":
                curr_sql += " NOT NULL"
            if column_comment:
                escaped = str(column_comment).replace("'", "''")
                curr_sql += f" COMMENT '{escaped}'"
            column_strs.append(curr_sql)
        ddl_sql += ",\n".join(column_strs)
        if table_comment:
            escaped_table_comment = str(table_comment).replace("'", "''")
            ddl_sql += f"\n) COMMENT '{escaped_table_comment}';"
        else:
            ddl_sql += "\n);"
        return ddl_sql

    def get_all_create_table_sql(self) -> str:
        parts = []
        for info in self.table_infos:
            if not info.get("transformed"):
                continue
            parts.append(
                f"-- 文件: {info.get('file_name')} / Sheet: {info.get('sheet_name')}\n"
                f"{self.get_create_table_sql(info['table_name'])}"
            )
        return "\n\n".join(parts)

    def get_create_table_sql_for_tables(self, table_names: List[str]) -> str:
        """仅生成指定表的 DDL（含列注释），用于分析阶段按需注入。"""
        name_set = set(table_names)
        parts = []
        for info in self.table_infos:
            if not info.get("transformed"):
                continue
            if info["table_name"] not in name_set:
                continue
            parts.append(
                f"-- 文件: {info.get('file_name')} / Sheet: {info.get('sheet_name')}\n"
                f"{self.get_create_table_sql(info['table_name'])}"
            )
        return "\n\n".join(parts)

    def get_sample_data_for_tables(self, table_names: List[str], limit: int = 2) -> str:
        """仅获取指定表的采样数据，用于分析阶段按需注入。返回 JSON 字符串。"""
        import json
        from datetime import date, datetime

        def _default_serial(obj):
            """JSON 序列化兜底，处理 date/datetime/numpy 类型。"""
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            return str(obj)

        name_set = set(table_names)
        samples = []
        for info in self.table_infos:
            if not info.get("transformed"):
                continue
            if info["table_name"] not in name_set:
                continue
            columns, datas = self.get_sample_data(table_name=info["table_name"], limit=limit)
            samples.append({
                "file_name": info.get("file_name"),
                "sheet_name": info.get("sheet_name"),
                "table_name": info["table_name"],
                "columns": columns,
                "rows": datas,
            })
        return json.dumps(samples, ensure_ascii=False, default=_default_serial)

    def get_table_index(self) -> List[dict]:
        """生成轻量表索引，每张表包含表名、sheet名、表注释、列名与列注释列表。
        用于分析阶段的表筛选 LLM 调用，避免全量 DDL + 采样数据超出上下文。
        """
        index = []
        for info in self.table_infos:
            if not info.get("transformed"):
                continue
            table_name = info["table_name"]
            # 表注释
            sql = f"""SELECT comment FROM duckdb_tables() WHERE table_name = '{table_name}'"""
            _, t_datas = self._run_sql(sql)
            table_comment = t_datas[0][0] if t_datas else ""
            # 列名 + 列注释
            _, cl_datas = self.get_columns(table_name)
            columns = []
            for cl_data in cl_datas:
                col_name = cl_data[0]
                col_comment = cl_data[3] if len(cl_data) > 3 else None
                if col_comment:
                    columns.append(f"{col_name}({col_comment})")
                else:
                    columns.append(col_name)
            index.append({
                "table_name": table_name,
                "sheet_name": info.get("sheet_name", ""),
                "file_name": info.get("file_name", ""),
                "table_comment": table_comment or "",
                "columns": columns,
            })
        return index

    def get_columns(self, table_name: str = None):
        """获取表的列信息，包含列名、类型、是否可空、列注释。"""
        table_name = table_name or self.curr_table
        sql = f"""
        SELECT dc.column_name, dc.data_type AS column_type,
               CASE WHEN dc.is_nullable THEN 'YES' ELSE 'NO' END AS "null",
               dc.comment
        FROM duckdb_columns() dc
        WHERE dc.table_name = '{table_name}' AND dc.schema_name = 'main';
        """
        return self._run_sql(sql)

    def get_summary(self, table_name: str = None) -> str:
        table_name = table_name or self.curr_table
        return self.run(f"SUMMARIZE {table_name}", df_res=True, transform=False).to_json(force_ascii=False)

    def get_row_count(self, table_name: str = None) -> int:
        table_name = table_name or self.curr_table
        _, datas = self._run_sql(f"SELECT COUNT(*) FROM {table_name}")
        return datas[0][0] if datas else 0
