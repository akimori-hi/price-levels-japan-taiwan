"""台湾統計局「薪情平臺」データの整形ユーティリティ。"""
import re

import pandas as pd


def roc_to_western_year(roc_year: int) -> int:
    """民国暦（例：114年）を西暦（例：2025年）に変換する。"""
    return roc_year + 1911


def load_taiwan_industry_productivity(path) -> pd.DataFrame:
    """薪情平臺からダウンロードした「勞動生產力指數(產量)」の生データを整形する。

    ファイル構造（実際にダウンロードして確認済み）：
    - 行0: ('', None, '工業', '服務業', ...)
    - 行1: (None, None, '總計', '總計', ...)
    - 行2: (None, None, '統計值', '統計值', ...)
    - 行3以降: (指標名(行3のみ), '71年1月'のような民国暦日付, 工業の値, 服務業の値, ...)

    服務業（サービス業）は物量ベースの生産性指数が定義できず、全期間欠測。
    このため工業のみを返す。
    """
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    date_pattern = re.compile(r"^(\d+)年(\d+)月$")
    records = []
    for row in rows[3:]:
        date_text = row[1]
        if not date_text or not isinstance(date_text, str):
            continue
        m = date_pattern.match(date_text)
        if not m:
            continue
        roc_year, month = int(m.group(1)), int(m.group(2))
        value = row[2]
        if value in (None, "-"):
            continue
        records.append({
            "year": roc_to_western_year(roc_year),
            "month": month,
            "industry_productivity_index": float(value),
        })

    return pd.DataFrame(records).sort_values(["year", "month"]).reset_index(drop=True)


def annualize_productivity_index(monthly_df: pd.DataFrame, min_months: int = 6) -> pd.DataFrame:
    """月次の生産性指数を年平均に集約する（min_months未満のデータしかない年は除く）。"""
    grouped = monthly_df.groupby("year")["industry_productivity_index"]
    annual = grouped.mean().to_frame("industry_productivity_index_annual")
    annual["n_months"] = grouped.count()
    annual = annual[annual["n_months"] >= min_months].drop(columns="n_months")
    return annual.reset_index()
