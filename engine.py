import pandas as pd
import numpy as np
from rules import retail_incentive, protection_incentive, danni_rate, protection_rate, retention_multiplier
from utils import clean_number

def calc_accordo(accordo_df, objectives):
    if accordo_df is None or accordo_df.empty:
        return pd.DataFrame()
    rows = []
    for _, r in accordo_df.iterrows():
        line = r["LINEA"]
        objective = objectives.get(f"{line}_OBJECTIVE", 0.0)
        parachute = objectives.get(f"{line}_PARACHUTE", objective)
        # Accordo economico Motor/RV: calcolo come mini-fonte su NB premi e best of.
        best = max(r.get("CRESCITA_NB_PREMI", 0), r.get("CRESCITA_NB_PEZZI", 0))
        sp = r.get("SP", 0)
        nb = r.get("NB_PREMI_2026", 0)
        inc_growth = r.get("CRESCITA_INCASSI", 0)
        # matrici da Accordo Economico storico: RV 21/23.5/26, Motor 5/5.5/6, con fasce S/P
        if line == "RV":
            if sp < 0.35:
                rates = [0.21, 0.235, 0.26]
            elif sp < 0.45:
                rates = [0.18, 0.21, 0.235]
            elif sp < 0.50:
                rates = [0.155, 0.18, 0.21]
            else:
                rates = [0,0,0]
        else:  # MOTOR
            if sp < 0.35:
                rates = [0.05, 0.055, 0.06]
            elif sp < 0.45:
                rates = [0.04, 0.05, 0.055]
            elif sp < 0.50:
                rates = [0.036, 0.042, 0.05]
            else:
                rates = [0,0,0]
        if best < 0:
            rate = rates[0]
        elif best <= 0.10:
            rate = rates[1]
        else:
            rate = rates[2]
        status = "OBIETTIVO" if inc_growth >= objective else ("PARACADUTE" if inc_growth >= parachute else "FUORI")
        final_rate = rate if status == "OBIETTIVO" else max(rate - 0.02, 0) if status == "PARACADUTE" else 0.0
        incentive = nb * final_rate
        rows.append({
            "FONTE": r["FONTE"], "LINEA": line,
            "INCASSI_2026": r.get("INCASSI_2026",0),
            "INCASSI_2025": r.get("INCASSI_2025",0),
            "CRESCITA_INCASSI": inc_growth,
            "NB_PREMI_2026": nb,
            "NB_PREMI_2025": r.get("NB_PREMI_2025",0),
            "CRESCITA_NB_PREMI": r.get("CRESCITA_NB_PREMI",0),
            "NB_PEZZI_2026": r.get("NB_PEZZI_2026",0),
            "NB_PEZZI_2025": r.get("NB_PEZZI_2025",0),
            "CRESCITA_NB_PEZZI": r.get("CRESCITA_NB_PEZZI",0),
            "BEST_OF_NB": best,
            "SP": sp,
            "ALIQUOTA": final_rate,
            "ALIQUOTA_BASE": rate,
            "STATUS": status,
            "VALORE_ACCORDO": incentive,
            "GAP_OBIETTIVO_PERC": max(objective - inc_growth, 0),
            "GAP_OBIETTIVO_EURO": max(r.get("INCASSI_2025",0)*(1+objective)-r.get("INCASSI_2026",0),0),
        })
    return pd.DataFrame(rows)

def calc_retail_incentives(retail_df, objectives):
    if retail_df is None or retail_df.empty:
        return pd.DataFrame()
    rows = []
    for _, r in retail_df.iterrows():
        line = r["LINEA"]
        objective = objectives.get(f"{line}_OBJECTIVE", 0.0)
        parachute = objectives.get(f"{line}_PARACHUTE", objective)
        d = retail_incentive(r, line, objective, parachute)
        row = r.to_dict()
        row.update(d)
        row["VALORE_RAPPEL_ALLIANZ"] = d["INCENTIVO"]
        row["GAP_OBIETTIVO_PERC"] = max(objective - r.get("CRESCITA_INCASSI", 0), 0)
        row["GAP_OBIETTIVO_EURO"] = max(r.get("INCASSI_2025",0)*(1+objective)-r.get("INCASSI_2026",0),0)
        rows.append(row)
    return pd.DataFrame(rows)

def calc_protection(prot_df):
    if prot_df is None or prot_df.empty:
        return pd.DataFrame()
    rows = []
    for _, r in prot_df.iterrows():
        d = protection_incentive(r)
        row = r.to_dict()
        row.update(d)
        row["VALORE_PROTECTION_MINI_FONTE"] = d["INCENTIVO"]
        row["GAP_NB_MINIMO"] = max(10000 - r.get("NB_2026",0), 0)
        row["GAP_RETENTION_X1"] = max(0.90 - r.get("RETENTION_CALC",0), 0)
        rows.append(row)
    out = pd.DataFrame(rows)

    # Fedeltà Allianz: Protection è calcolato a livello agenzia aggregata.
    # Per la scheda fonte, l'incentivo ufficiale di quarter viene poi ripartito sulle fonti
    # in base al peso del New Business Protection 2026 positivo.
    out["VALORE_PROTECTION"] = 0.0
    out["PROTECTION_AGENCY_TOTAL_QUARTER"] = 0.0
    out["PROTECTION_ALLOCATION_WEIGHT"] = 0.0
    for q, part in out.groupby("QUARTER"):
        nb26 = part["NB_2026"].sum()
        nb25 = part["NB_2025"].sum()
        perf = (nb26 - nb25) / nb25 if nb25 else (9.999 if nb26 > 0 else 0.0)
        scad = part["PEZZI_SCADENZA"].sum()
        cons = part["PEZZI_CONSERVATI"].sum()
        retention = cons / scad if scad else 0.0
        agg = {"NB_2026": nb26, "PERFORMANCE_NB": perf, "RETENTION_CALC": retention}
        official = protection_incentive(agg)["INCENTIVO"]
        pos_nb = part["NB_2026"].clip(lower=0)
        denom = pos_nb.sum()
        if denom > 0:
            weights = pos_nb / denom
            out.loc[part.index, "PROTECTION_ALLOCATION_WEIGHT"] = weights
            out.loc[part.index, "VALORE_PROTECTION"] = weights * official
        out.loc[part.index, "PROTECTION_AGENCY_TOTAL_QUARTER"] = official
    return out

def build_source_summary(accordo_calc, retail_calc, protection_calc, midco_total=0):
    fonti = set()
    for df in [accordo_calc, retail_calc, protection_calc]:
        if df is not None and not df.empty and "FONTE" in df:
            fonti.update(df["FONTE"].dropna().unique())
    out = pd.DataFrame({"FONTE": sorted(fonti)})
    if out.empty:
        return out

    if accordo_calc is not None and not accordo_calc.empty:
        a = accordo_calc.pivot_table(index="FONTE", columns="LINEA", values="VALORE_ACCORDO", aggfunc="sum", fill_value=0).reset_index()
        a.columns = ["FONTE"] + [f"AE_{c}" for c in a.columns[1:]]
        out = out.merge(a, on="FONTE", how="left")
    if retail_calc is not None and not retail_calc.empty:
        r = retail_calc.pivot_table(index="FONTE", columns="LINEA", values="VALORE_RAPPEL_ALLIANZ", aggfunc="sum", fill_value=0).reset_index()
        r.columns = ["FONTE"] + [f"RAPPEL_{c}" for c in r.columns[1:]]
        out = out.merge(r, on="FONTE", how="left")
    if protection_calc is not None and not protection_calc.empty:
        p = protection_calc.groupby("FONTE", as_index=False)["VALORE_PROTECTION"].sum()
        p = p.rename(columns={"VALORE_PROTECTION":"RAPPEL_PROTECTION"})
        out = out.merge(p, on="FONTE", how="left")
    out = out.fillna(0)
    value_cols = [c for c in out.columns if c != "FONTE"]
    out["TOTALE_ALLIANZ_002"] = out[value_cols].sum(axis=1) if value_cols else 0
    return out.sort_values("TOTALE_ALLIANZ_002", ascending=False)

def recovery_board(source_summary):
    if source_summary is None or source_summary.empty:
        return source_summary
    out = source_summary.copy()
    # placeholder conservative: recuperabile is gap from zero? For positive report, leave actual potential to rule pages.
    out["STATO"] = np.where(out["TOTALE_ALLIANZ_002"] > 0, "CREA VALORE", "DA RECUPERARE")
    return out
