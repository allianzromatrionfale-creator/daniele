from config import DANNI_RV_HEALTH_RATES, DANNI_ARD_RATES, CLIENT_MULTIPLIERS, PROTECTION_RATES, RETENTION_MULTIPLIERS, MIDCO_RATE_BANDS
from utils import clean_number

def rate_from_bands(value, bands):
    for low, high, rate in bands:
        if value >= low and value < high:
            return rate
    return 0.0

def client_multiplier(client_growth):
    return rate_from_bands(client_growth, CLIENT_MULTIPLIERS)

def danni_rate(line, nb_perf):
    line = line.upper()
    if line in ["RV", "HEALTH"]:
        return rate_from_bands(nb_perf, DANNI_RV_HEALTH_RATES)
    if line == "ARD":
        return rate_from_bands(nb_perf, DANNI_ARD_RATES)
    return 0.0

def retail_incentive(row, line, objective, parachute):
    inc_growth = clean_number(row.get("CRESCITA_INCASSI", 0))
    nb = clean_number(row.get("NB_2026", 0))
    nb_perf = clean_number(row.get("CRESCITA_NB", 0))
    client_growth = clean_number(row.get("CRESCITA_CLIENTI", 0))
    sp = clean_number(row.get("SP", 0))
    base_rate = danni_rate(line, nb_perf)

    # S/P: soglia 50% per Danni Retail da schermate; se oltre, incentivo escluso
    sp_ok = sp < 0.50 if sp <= 1 else sp < 50
    access = False
    malus = 0.0
    status = "FUORI"

    if inc_growth >= objective and sp_ok:
        access = True
        status = "OBIETTIVO"
    elif inc_growth >= parachute and sp_ok:
        access = True
        malus = -0.02
        status = "PARACADUTE"

    final_rate = max(base_rate + malus, 0.0) if access else 0.0
    mult = client_multiplier(client_growth)
    incentive = nb * final_rate * mult
    return {
        "ALIQUOTA_BASE": base_rate,
        "MALUS": malus,
        "ALIQUOTA_FINALE": final_rate,
        "MOLTIPLICATORE_CLIENTI": mult,
        "INCENTIVO": incentive,
        "STATO": status,
        "SP_OK": sp_ok,
        "ACCESSO": access,
    }

def protection_rate(nb, perf):
    nb = clean_number(nb)
    perf = clean_number(perf)
    if nb < 10000:
        return 0.0
    if nb < 30000:
        col = 0
    elif nb < 75000:
        col = 1
    elif nb < 150000:
        col = 2
    else:
        col = 3
    for low, high, rates in PROTECTION_RATES["matrix"]:
        if perf >= low and perf < high:
            return rates[col]
    return 0.0

def retention_multiplier(ret):
    return rate_from_bands(ret, RETENTION_MULTIPLIERS)

def protection_incentive(row):
    nb = clean_number(row.get("NB_2026", 0))
    perf = clean_number(row.get("PERFORMANCE_NB", 0))
    ret = clean_number(row.get("RETENTION_CALC", 0))
    rate = protection_rate(nb, perf)
    mult = retention_multiplier(ret)
    incentive = nb * rate * mult
    return {
        "ALIQUOTA_TEO": rate,
        "MOLTIPLICATORE_RETENTION": mult,
        "INCENTIVO": incentive,
        "ACCESSO_NB": nb >= 10000,
        "ACCESSO_RETENTION": ret >= 0.50,
    }

def midco_incentive(inc26, inc25, sp, base_calcolo):
    inc26 = clean_number(inc26)
    inc25 = clean_number(inc25)
    sp = clean_number(sp)
    base_calcolo = clean_number(base_calcolo)
    growth = (inc26 - inc25) / inc25 if inc25 else 0.0
    rate = 0.0
    for low, high, r, min_inc in MIDCO_RATE_BANDS:
        if growth >= low and growth < high and inc26 >= min_inc:
            rate = r
    if sp >= 0.55:
        return 0.0, rate, growth, "NO INCENTIVAZIONE"
    bonus = 0.0
    if sp < 0.35:
        bonus = 0.05
    elif sp >= 0.45:
        bonus = -0.05
    incentive = base_calcolo * max(rate + bonus, 0)
    return incentive, rate, growth, "OK"
