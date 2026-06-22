import pandas as pd
import numpy as np
import re
import unicodedata

def clean_text(x):
    if pd.isna(x):
        return ""
    s = str(x).strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.upper()
    s = re.sub(r"\s+", " ", s)
    return s

def norm_col(x):
    s = clean_text(x)
    s = s.replace("%", " PERC ")
    s = s.replace("/", " ")
    s = re.sub(r"[^A-Z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s

def clean_number(x):
    if pd.isna(x):
        return 0.0
    if isinstance(x, (int, float, np.number)):
        return float(x)
    s = str(x).strip()
    if s.lower() in ["nd", "nan", "none", "-", ""]:
        return 0.0
    has_percent = "%" in s
    s = s.replace("€", "").replace("%", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        value = float(s)
        return value / 100 if has_percent else value
    except Exception:
        return 0.0

def pct(current, previous):
    current = clean_number(current)
    previous = clean_number(previous)
    if previous == 0:
        return 0.0
    return (current - previous) / previous

def fmt_euro(v):
    try:
        return f"€ {float(v):,.0f}".replace(",", ".")
    except Exception:
        return "€ 0"

def fmt_pct(v):
    try:
        return f"{float(v)*100:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,0%"

def fmt_num(v):
    try:
        return f"{float(v):,.0f}".replace(",", ".")
    except Exception:
        return "0"

def normalize_df(df):
    out = df.copy()
    out.columns = [norm_col(c) for c in out.columns]
    return out

def find_col(df, candidates):
    cols = list(df.columns)
    norm_candidates = [norm_col(c) for c in candidates]
    for c in norm_candidates:
        if c in cols:
            return c
    for col in cols:
        for cand in norm_candidates:
            parts = [p for p in cand.split("_") if p]
            if parts and all(p in col for p in parts):
                return col
    return None

def read_any_excel(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".ods"):
        df = pd.read_excel(uploaded_file, engine="odf")
    else:
        df = pd.read_excel(uploaded_file)
    return normalize_df(df)

def pretty_dataframe(df, euro_cols=None, pct_cols=None, int_cols=None):
    out = df.copy()
    for c in euro_cols or []:
        if c in out.columns:
            out[c] = out[c].apply(fmt_euro)
    for c in pct_cols or []:
        if c in out.columns:
            out[c] = out[c].apply(fmt_pct)
    for c in int_cols or []:
        if c in out.columns:
            out[c] = out[c].apply(fmt_num)
    return out
