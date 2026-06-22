import pandas as pd
from utils import read_any_excel, find_col, clean_number, clean_text, pct

def import_accordo_file(uploaded_file, line):
    df = read_any_excel(uploaded_file)
    aliases = {
        "FONTE": ["Fonte", "Codice agenzia", "Codice fonte", "Intermediario"],
        "INCASSI_2026": ["Incassi 2026", "2026 daily Incassi", "2026 Incassi"],
        "INCASSI_2025": ["Incassi 2025", "2025 daily Incassi", "2025 Incassi", "Media daily incassi"],
        "CONTRATTI_2026": ["Contratti 2026", "2026 Contratti"],
        "CONTRATTI_2025": ["Contratti 2025", "2025 Contratti"],
        "NB_PREMI_2026": ["NB Premi 2026", "2026 daily NB", "New Business 2026", "NB 2026"],
        "NB_PREMI_2025": ["NB Premi 2025", "Media daily NB", "NB Premi 2025", "New Business 2025", "NB 2025"],
        "NB_PEZZI_2026": ["NB pezzi 2026", "2026 Pezzi", "NB Pezzi 2026"],
        "NB_PEZZI_2025": ["NB pezzi 2025", "2025 Pezzi", "NB Pezzi 2025"],
        "SP": ["S/P", "S P", "SP", "S/P inc"],
    }
    out = pd.DataFrame()
    for target, candidates in aliases.items():
        col = find_col(df, candidates)
        if col:
            out[target] = df[col]
        else:
            out[target] = "" if target == "FONTE" else 0
    out["FONTE"] = out["FONTE"].apply(clean_text)
    out["LINEA"] = line
    for c in out.columns:
        if c not in ["FONTE", "LINEA"]:
            out[c] = out[c].apply(clean_number)
    out["CRESCITA_INCASSI"] = out.apply(lambda r: pct(r["INCASSI_2026"], r["INCASSI_2025"]), axis=1)
    out["CRESCITA_CONTRATTI"] = out.apply(lambda r: pct(r["CONTRATTI_2026"], r["CONTRATTI_2025"]), axis=1)
    out["CRESCITA_NB_PREMI"] = out.apply(lambda r: pct(r["NB_PREMI_2026"], r["NB_PREMI_2025"]), axis=1)
    out["CRESCITA_NB_PEZZI"] = out.apply(lambda r: pct(r["NB_PEZZI_2026"], r["NB_PEZZI_2025"]), axis=1)
    out["BEST_OF_NB"] = out[["CRESCITA_NB_PREMI", "CRESCITA_NB_PEZZI"]].max(axis=1)
    out = out[out["FONTE"] != ""].copy()
    return out

def import_retail_file(uploaded_file, line):
    df = read_any_excel(uploaded_file)
    aliases = {
        "FONTE": ["Fonte", "Codice agenzia", "Codice fonte", "Intermediario"],
        "INCASSI_2026": ["2026 daily Incassi", "Incassi 2026", "2026 Incassi"],
        "INCASSI_2025": ["2025 daily Incassi", "Incassi 2025", "2025 Incassi"],
        "NB_2026": ["2026 daily NB", "NB 2026", "New Business 2026"],
        "NB_2025": ["Media daily NB", "NB 2025", "New Business 2025"],
        "SINISTRI": ["Sinistri"],
        "PREMI": ["Premi"],
        "SP": ["S/P inc", "S/P", "SP"],
        "CLIENTI_2026": ["2026 Clienti", "Clienti 2026"],
        "CLIENTI_2025": ["2025 Clienti", "Clienti 2025"],
        "PEZZI_2026": ["2026 Pezzi", "Pezzi 2026"],
        "PEZZI_2025": ["2025 Pezzi", "Pezzi 2025"],
    }
    out = pd.DataFrame()
    for target, candidates in aliases.items():
        col = find_col(df, candidates)
        if col:
            out[target] = df[col]
        else:
            out[target] = "" if target == "FONTE" else 0
    out["FONTE"] = out["FONTE"].apply(clean_text)
    out["LINEA"] = line
    for c in out.columns:
        if c not in ["FONTE", "LINEA"]:
            out[c] = out[c].apply(clean_number)
    out["CRESCITA_INCASSI"] = out.apply(lambda r: pct(r["INCASSI_2026"], r["INCASSI_2025"]), axis=1)
    out["CRESCITA_NB"] = out.apply(lambda r: pct(r["NB_2026"], r["NB_2025"]), axis=1)
    out["CRESCITA_CLIENTI"] = out.apply(lambda r: pct(r["CLIENTI_2026"], r["CLIENTI_2025"]), axis=1)
    out["CRESCITA_PEZZI"] = out.apply(lambda r: pct(r["PEZZI_2026"], r["PEZZI_2025"]), axis=1)
    out = out[out["FONTE"] != ""].copy()
    return out

def import_protection_file(uploaded_file, quarter):
    df = read_any_excel(uploaded_file)
    aliases = {
        "FONTE": ["Fonte", "Codice agenzia", "Codice fonte", "Intermediario"],
        "NB_2026": ["NB Daily 2026", "New Business 2026", "NB 2026", "Premi 2026", "2026 daily", "Premi"],
        "NB_2025": ["NB Daily 2025", "New Business 2025", "NB 2025", "Premi 2025", "2025 daily"],
        "PEZZI_CONSERVATI": ["Pezzi conservati", "Pezzi in PTF", "Pezzi conserv"],
        "PEZZI_SCADENZA": ["Pezzi a scadenza", "Pezzi scadenza"],
        "RETENTION": ["Retention", "Retention %"],
    }
    out = pd.DataFrame()
    for target, candidates in aliases.items():
        col = find_col(df, candidates)
        if col:
            out[target] = df[col]
        else:
            out[target] = "" if target == "FONTE" else 0
    out["FONTE"] = out["FONTE"].apply(clean_text)
    out["QUARTER"] = quarter
    for c in out.columns:
        if c not in ["FONTE", "QUARTER"]:
            out[c] = out[c].apply(clean_number)
    out["PERFORMANCE_NB"] = out.apply(lambda r: pct(r["NB_2026"], r["NB_2025"]), axis=1)
    out["RETENTION_CALC"] = out.apply(lambda r: (r["PEZZI_CONSERVATI"] / r["PEZZI_SCADENZA"]) if r["PEZZI_SCADENZA"] else r["RETENTION"], axis=1)
    out = out[out["FONTE"] != ""].copy()
    return out
