from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from utils import fmt_euro, fmt_pct

def make_ceo_pdf(source_summary, totals):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("Allianz 002 - Executive Report CEO", styles["Title"]))
    story.append(Spacer(1, 12))
    data = [
        ["KPI", "Valore"],
        ["Totale Allianz → Allianz 002", fmt_euro(totals.get("totale", 0))],
        ["Accordo Economico", fmt_euro(totals.get("accordo", 0))],
        ["Rappel/Incentivi Allianz", fmt_euro(totals.get("rappel", 0))],
        ["Protection", fmt_euro(totals.get("protection", 0))],
        ["MidCo aggregato", fmt_euro(totals.get("midco", 0))],
    ]
    t = Table(data, colWidths=[260, 180])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#003781")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                           ("GRID",(0,0),(-1,-1),0.5,colors.grey),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold")]))
    story.append(t)
    story.append(Spacer(1, 18))
    story.append(Paragraph("Top Fonti", styles["Heading2"]))
    if source_summary is not None and not source_summary.empty:
        top = source_summary.head(15)
        rows = [["Fonte", "Totale Allianz → 002"]] + [[r["FONTE"], fmt_euro(r["TOTALE_ALLIANZ_002"])] for _, r in top.iterrows()]
        tt = Table(rows, colWidths=[240, 180])
        tt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#003781")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                                ("GRID",(0,0),(-1,-1),0.5,colors.grey),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold")]))
        story.append(tt)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def make_source_pdf(source_code, source_summary, accordo_calc, retail_calc, protection_calc):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"Scheda Fonte - {source_code}", styles["Title"]))
    story.append(Spacer(1, 12))

    if source_summary is not None and not source_summary.empty:
        row = source_summary[source_summary["FONTE"] == source_code]
        if not row.empty:
            r = row.iloc[0]
            data = [["Voce", "Valore"]]
            for c in source_summary.columns:
                if c != "FONTE":
                    data.append([c, fmt_euro(r[c])])
            t = Table(data, colWidths=[220, 180])
            t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#003781")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                                   ("GRID",(0,0),(-1,-1),0.5,colors.grey)]))
            story.append(t)
    story.append(Spacer(1, 12))
    story.append(Paragraph("Dettaglio e piano recupero", styles["Heading2"]))
    story.append(Paragraph("La scheda fonte mostra il valore generato da Accordo Economico e Incentivazioni Allianz, senza detrarre il rappel pagato alla rete.", styles["Normal"]))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
