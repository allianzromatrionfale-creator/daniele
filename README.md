# Allianz002 BI

BI per Allianz 002.

## Avvio

Apri il Prompt dei comandi nella cartella `allianz002_bi` e lancia:

```cmd
pip install -r requirements.txt
python -m streamlit run app.py
```

## Logica

Il BI è diviso in due mondi separati:

1. **Allianz → Allianz 002**
   - Accordo Economico
   - Rappel/Incentivazioni Allianz pagate ad Allianz 002
   - RV, Motor, Health, ARD, Protection, MidCo aggregato
   - Vita predisposto ma non attivo

2. **Allianz 002 → Rete**
   - sezione predisposta e separata
   - non viene sottratta dal valore Allianz → Allianz 002

## File caricabili

- Accordo Economico Motor
- Accordo Economico RV
- RV Rete
- Health Rete
- ARD Rete
- Protection Q1
- Protection Q2
- MidCo inserimento manuale / da screenshot

Sono supportati `.xlsx`, `.xls`, `.ods`.
