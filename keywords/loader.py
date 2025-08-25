# keywords/loader.py

import pandas as pd
from keywords.funcional_keywords_deduplicado import build_master_deduped

_master_cache = None  # cache local


def get_master_deduped(excel_data: pd.ExcelFile) -> pd.DataFrame:
    global _master_cache
    if _master_cache is None:
        _master_cache = build_master_deduped(excel_data)
    return _master_cache
