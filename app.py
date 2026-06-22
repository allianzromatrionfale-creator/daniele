# V4 Finale - specifica fedele Allianz 002
import streamlit as st
import pandas as pd
from io import BytesIO

from importers import import_accordo_file, import_retail_file, import_protection_file
from engine import calc_accordo, calc_retail_incentives, calc_protection, build_source_summary, recovery_board
from rules import midco_incentive
from utils import pretty_dataframe, fmt_euro, fmt_pct
from pdf_reports import make_ceo_pdf, make_source_pdf

st.set_page_config(page_title="Allianz 002 BI", layout="wide")

st.title("Allianz 002 BI")
st.caption("Accordo Economico + Rappel/Incentivazioni Allianz → Allianz 002 | Sezione rete separata")

st.sidebar.header("Input periodo")
quarter = st.sidebar.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4", "YTD"], index=1)

st.sidebar.header("Obiettivi Allianz")
rv_obj = st.sidebar.number_input("RV obiettivo %", value=6.0, step=0.1) / 100
rv_par = st.sidebar.number_input("RV paracadute %", value=4.8, step=0.1) / 100
motor_obj = st.sidebar.number_input("Motor obiettivo %", value=3.5, step=0.1) / 100
motor_par = st.sidebar.number_input("Motor paracadute %", value=3.5, step=0.1) / 100
health_obj = st.sidebar.number_input("Health obiettivo %", value=7.0, step=0.1) / 100
health_par = st.sidebar.number_input("Health paracadute %", value=5.6, step=0.1) / 100
ard_obj = st.sidebar.number_input("ARD obiettivo %", value=6.6, step=0.1) / 100
ard_par = st.sidebar.number_input("ARD paracadute %", value=5.3, step=0.1) / 100

objectives = {
    "RV_OBJECTIVE": rv_obj, "RV_PARACHUTE": rv_par,
    "MOTOR_OBJECTIVE": motor_obj, "MOTOR_PARACHUTE": motor_par,
    "HEALTH_OBJECTIVE": health_obj, "HEALTH_PARACHUTE": health_par,
    "ARD_OBJECTIVE": ard_obj, "ARD_PARACHUTE": ard_par,
}

st.sidebar.header("Upload file")
acc_motor_files = st.sidebar.file_uploader("Accordo Economico Motor", type=["xlsx","xls","ods"], accept_multiple_files=True)
acc_rv_files = st.sidebar.file_uploader("Accordo Economico RV", type=["xlsx","xls","ods"], accept_multiple_files=True)

rv_files = st.sidebar.file_uploader("Rappel Allianz RV Retail", type=["xlsx","xls","ods"], accept_multiple_files=True)
health_files = st.sidebar.file_uploader("Rappel Allianz Health Retail", type=["xlsx","xls","ods"], accept_multiple_files=True)
ard_files = st.sidebar.file_uploader("Rappel Allianz ARD Retail", type=["xlsx","xls","ods"], accept_multiple_files=True)

prot_q1_files = st.sidebar.file_uploader("Protection Q1", type=["xlsx","xls","ods"], accept_multiple_files=True)
prot_q2_files = st.sidebar.file_uploader("Protection Q2", type=["xlsx","xls","ods"], accept_multiple_files=True)

st.sidebar.header("MidCo aggregato")
midco_inc26 = st.sidebar.number_input("MidCo incassi 2026", value=0.0, step=1000.0)
midco_inc25 = st.sidebar.number_input("MidCo incassi 2025", value=0.0, step=1000.0)
midco_sp = st.sidebar.number_input("MidCo S/P", value=0.0, step=0.01)
midco_base = st.sidebar.number_input("MidCo base calcolo", value=0.0, step=1000.0)

# IMPORT
accordo_frames = []
for f in acc_motor_files or []:
    accordo_frames.append(import_accordo_file(f, "MOTOR"))
for f in acc_rv_files or []:
    accordo_frames.append(import_accordo_file(f, "RV"))
accordo_raw = pd.concat(accordo_frames, ignore_index=True) if accordo_frames else pd.DataFrame()

retail_frames = []
for f in rv_files or []:
    retail_frames.append(import_retail_file(f, "RV"))
for f in health_files or []:
    retail_frames.append(import_retail_file(f, "HEALTH"))
for f in ard_files or []:
    retail_frames.append(import_retail_file(f, "ARD"))
retail_raw = pd.concat(retail_frames, ignore_index=True) if retail_frames else pd.DataFrame()

prot_frames = []
for f in prot_q1_files or []:
    prot_frames.append(import_protection_file(f, "Q1"))
for f in prot_q2_files or []:
    prot_frames.append(import_protection_file(f, "Q2"))
protection_raw = pd.concat(prot_frames, ignore_index=True) if prot_frames else pd.DataFrame()

accordo_calc = calc_accordo(accordo_raw, objectives)
retail_calc = calc_retail_incentives(retail_raw, objectives)
protection_calc = calc_protection(protection_raw)

midco_amount, midco_rate, midco_growth, midco_status = midco_incentive(midco_inc26, midco_inc25, midco_sp, midco_base)

source_summary = build_source_summary(accordo_calc, retail_calc, protection_calc, midco_amount)
recovery = recovery_board(source_summary)

tot_accordo = accordo_calc["VALORE_ACCORDO"].sum() if not accordo_calc.empty else 0
tot_retail = retail_calc["VALORE_RAPPEL_ALLIANZ"].sum() if not retail_calc.empty else 0
tot_protection = protection_calc["VALORE_PROTECTION"].sum() if not protection_calc.empty else 0
totale = tot_accordo + tot_retail + tot_protection + midco_amount
totals = {"accordo": tot_accordo, "rappel": tot_retail, "protection": tot_protection, "midco": midco_amount, "totale": totale}

k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("Totale Allianz → Allianz 002", fmt_euro(totale))
k2.metric("Accordo Economico", fmt_euro(tot_accordo))
k3.metric("Rappel/Incentivi Danni", fmt_euro(tot_retail))
k4.metric("Protection", fmt_euro(tot_protection))
k5.metric("MidCo aggregato", fmt_euro(midco_amount))

tabs = st.tabs([
    "CEO Dashboard",
    "Accordo Economico",
    "Rappel Allianz → 002",
    "Protection",
    "MidCo",
    "Monitoraggio Fonti",
    "Scheda Fonte",
    "PDF / Export",
    "Allianz 002 → Rete"
])

with tabs[0]:
    st.subheader("CEO Dashboard")
    st.write("Vista complessiva di quanto Allianz riconosce ad Allianz 002. Il rappel pagato alla rete NON viene detratto.")
    if source_summary.empty:
        st.info("Carica almeno un file per popolare la dashboard.")
    else:
        show = pretty_dataframe(source_summary, euro_cols=[c for c in source_summary.columns if c!="FONTE"])
        st.dataframe(show, use_container_width=True)
        st.subheader("Recovery / priorità")
        st.dataframe(pretty_dataframe(recovery, euro_cols=[c for c in recovery.columns if c not in ["FONTE","STATO"]]), use_container_width=True)

with tabs[1]:
    st.subheader("Accordo Economico fonte per fonte")
    if accordo_calc.empty:
        st.info("Carica file Accordo Economico Motor/RV.")
    else:
        cols = ["FONTE","LINEA","STATUS","INCASSI_2026","INCASSI_2025","CRESCITA_INCASSI","NB_PREMI_2026","BEST_OF_NB","SP","ALIQUOTA","VALORE_ACCORDO","GAP_OBIETTIVO_PERC","GAP_OBIETTIVO_EURO"]
        st.dataframe(pretty_dataframe(accordo_calc[cols], euro_cols=["INCASSI_2026","INCASSI_2025","NB_PREMI_2026","VALORE_ACCORDO","GAP_OBIETTIVO_EURO"], pct_cols=["CRESCITA_INCASSI","BEST_OF_NB","SP","ALIQUOTA","GAP_OBIETTIVO_PERC"]), use_container_width=True)

with tabs[2]:
    st.subheader("Rappel / Incentivazioni Danni Retail Allianz → Allianz 002")
    if retail_calc.empty:
        st.info("Carica file RV / Health / ARD.")
    else:
        cols = ["FONTE","LINEA","STATO","INCASSI_2026","CRESCITA_INCASSI","NB_2026","CRESCITA_NB","SP","CRESCITA_CLIENTI","ALIQUOTA_FINALE","MOLTIPLICATORE_CLIENTI","VALORE_RAPPEL_ALLIANZ","GAP_OBIETTIVO_PERC","GAP_OBIETTIVO_EURO"]
        st.dataframe(pretty_dataframe(retail_calc[cols], euro_cols=["INCASSI_2026","NB_2026","VALORE_RAPPEL_ALLIANZ","GAP_OBIETTIVO_EURO"], pct_cols=["CRESCITA_INCASSI","CRESCITA_NB","SP","CRESCITA_CLIENTI","ALIQUOTA_FINALE","GAP_OBIETTIVO_PERC"]), use_container_width=True)

with tabs[3]:
    st.subheader("Protection")
    if protection_calc.empty:
        st.info("Carica file Protection Q1/Q2.")
    else:
        cols = ["FONTE","QUARTER","NB_2026","NB_2025","PERFORMANCE_NB","RETENTION_CALC","ALIQUOTA_TEO","MOLTIPLICATORE_RETENTION","VALORE_PROTECTION","GAP_NB_MINIMO","GAP_RETENTION_X1"]
        st.dataframe(pretty_dataframe(protection_calc[cols], euro_cols=["NB_2026","NB_2025","VALORE_PROTECTION","GAP_NB_MINIMO"], pct_cols=["PERFORMANCE_NB","RETENTION_CALC","ALIQUOTA_TEO","GAP_RETENTION_X1"]), use_container_width=True)

with tabs[4]:
    st.subheader("MidCo aggregato")
    st.write("MidCo viene gestito da screenshot/inserimento manuale, non analitico per fonte.")
    df_mid = pd.DataFrame([{
        "Incassi 2026": midco_inc26,
        "Incassi 2025": midco_inc25,
        "Performance": midco_growth,
        "S/P": midco_sp,
        "Base calcolo": midco_base,
        "Aliquota": midco_rate,
        "Stato": midco_status,
        "Incentivo MidCo": midco_amount
    }])
    st.dataframe(pretty_dataframe(df_mid, euro_cols=["Incassi 2026","Incassi 2025","Base calcolo","Incentivo MidCo"], pct_cols=["Performance","S/P","Aliquota"]), use_container_width=True)

with tabs[5]:
    st.subheader("Monitoraggio Fonti")
    st.write("Sezione KPI che spiega il valore generato. Non sottrae quanto Allianz 002 riconoscerà alla rete.")
    if retail_raw.empty and accordo_raw.empty and protection_raw.empty:
        st.info("Carica file per visualizzare il monitoraggio.")
    else:
        if not accordo_raw.empty:
            st.markdown("### Raw Accordo Economico")
            st.dataframe(accordo_raw, use_container_width=True)
        if not retail_raw.empty:
            st.markdown("### Raw Retail")
            st.dataframe(retail_raw, use_container_width=True)
        if not protection_raw.empty:
            st.markdown("### Raw Protection")
            st.dataframe(protection_raw, use_container_width=True)

with tabs[6]:
    st.subheader("Scheda Fonte")
    if source_summary.empty:
        st.info("Carica i dati prima.")
    else:
        selected = st.selectbox("Seleziona fonte", source_summary["FONTE"].tolist())
        st.markdown(f"## {selected}")
        st.dataframe(pretty_dataframe(source_summary[source_summary["FONTE"]==selected], euro_cols=[c for c in source_summary.columns if c!="FONTE"]), use_container_width=True)
        st.markdown("### Dettaglio Accordo Economico")
        if not accordo_calc.empty:
            st.dataframe(pretty_dataframe(accordo_calc[accordo_calc["FONTE"]==selected], euro_cols=["INCASSI_2026","NB_PREMI_2026","VALORE_ACCORDO","GAP_OBIETTIVO_EURO"], pct_cols=["CRESCITA_INCASSI","BEST_OF_NB","SP","ALIQUOTA","GAP_OBIETTIVO_PERC"]), use_container_width=True)
        st.markdown("### Dettaglio Rappel/Incentivi Allianz")
        if not retail_calc.empty:
            st.dataframe(pretty_dataframe(retail_calc[retail_calc["FONTE"]==selected], euro_cols=["INCASSI_2026","NB_2026","VALORE_RAPPEL_ALLIANZ","GAP_OBIETTIVO_EURO"], pct_cols=["CRESCITA_INCASSI","CRESCITA_NB","SP","CRESCITA_CLIENTI","ALIQUOTA_FINALE","GAP_OBIETTIVO_PERC"]), use_container_width=True)
        st.markdown("### Dettaglio Protection")
        if not protection_calc.empty:
            st.dataframe(pretty_dataframe(protection_calc[protection_calc["FONTE"]==selected], euro_cols=["NB_2026","NB_2025","VALORE_PROTECTION"], pct_cols=["PERFORMANCE_NB","RETENTION_CALC","ALIQUOTA_TEO"]), use_container_width=True)
        st.markdown("### Azioni consigliate")
        st.write("Il motore segnala come priorità le linee con incentivo nullo, gap obiettivo positivo o S/P fuori soglia.")

with tabs[7]:
    st.subheader("PDF / Export")
    if not source_summary.empty:
        ceo_pdf = make_ceo_pdf(source_summary, totals)
        st.download_button("Scarica PDF CEO", data=ceo_pdf, file_name="Allianz002_Report_CEO.pdf", mime="application/pdf")
        selected_pdf = st.selectbox("Fonte per PDF", source_summary["FONTE"].tolist(), key="pdf_source")
        pdf = make_source_pdf(selected_pdf, source_summary, accordo_calc, retail_calc, protection_calc)
        st.download_button("Scarica Scheda Fonte PDF", data=pdf, file_name=f"Scheda_Fonte_{selected_pdf}.pdf", mime="application/pdf")

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        source_summary.to_excel(writer, sheet_name="CEO_Fonti", index=False)
        accordo_calc.to_excel(writer, sheet_name="Accordo_Economico", index=False)
        retail_calc.to_excel(writer, sheet_name="Rappel_Allianz_002", index=False)
        protection_calc.to_excel(writer, sheet_name="Protection", index=False)
    st.download_button("Scarica Excel completo", data=output.getvalue(), file_name="Allianz002_BI_Output.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tabs[8]:
    st.subheader("Allianz 002 → Rete")
    st.info("Sezione separata. Qui verranno gestite le regole interne Bronze/Silver/Gold e quanto Allianz 002 riconosce alla rete. Non viene detratto dal modulo Allianz → Allianz 002.")
