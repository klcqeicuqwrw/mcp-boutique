import csv, io, json
from fastapi import APIRouter, Depends, HTTPException, Response
import securite as S
from boutique.dependencies import user_dep

router = APIRouter()

def _cell(v):
    """
    Sécurité contre l'injection CSV (formules Excel exécutant des macros malveillantes).
    Ajoute une apostrophe devant les symboles sensibles.
    """
    v = "" if v is None else v
    return "'" + v if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r") else v

@router.get("/api/export/{mid}")
def exporter(mid: int, format: str = "csv", u=Depends(user_dep)):
    """Génère un fichier téléchargeable contenant les résultats SQL."""
    m = S.q("""SELECT m.resultats, m.sql, m.access_scope FROM messages m JOIN conversations c ON c.id=m.conv_id
               WHERE m.id=? AND c.user_id=?""", (mid, u["id"]), one=True)
    if not m or not m["resultats"]:
        raise HTTPException(404, "Aucun tableau à exporter")
        
    if not S.message_accessible(m, u):
        raise HTTPException(403, "Vos droits actuels ne permettent pas de consulter ce résultat.")
    try:
        r = S.lire_resultats(m["resultats"])
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    cols, rows = r["columns"], [[row.get(c) for c in r["columns"]] for row in r["rows"]]
    nom = f"export_{mid}"
    
    # Logique de création des fichiers selon le format demandé (CSV, TSV, JSON, MD, PDF, XLSX)
    if format in ("csv", "tsv"):
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";" if format == "csv" else "\t")  # ";" pour être compatible Excel France
        w.writerow([_cell(c) for c in cols])
        w.writerows([_cell(v) for v in row] for row in rows)
        # L'ajout du "\ufeff" (BOM) force Excel à lire le fichier en UTF-8 (sinon accents cassés)
        data, mime = ("\ufeff" + buf.getvalue()).encode("utf-8"), "text/csv; charset=utf-8"
    elif format == "json":
        data = json.dumps([dict(zip(cols, x)) for x in rows], ensure_ascii=False, indent=2, default=str).encode()
        mime = "application/json"
    elif format == "md": # Markdown (pour documentation technique)
        esc = lambda v: str(v).replace("|", "\\|").replace("\n", " ")
        lignes = ["| " + " | ".join(map(esc, cols)) + " |", "|" + "---|" * len(cols)]
        lignes += ["| " + " | ".join(esc(v) for v in x) + " |" for x in rows]
        data, mime = "\n".join(lignes).encode(), "text/markdown; charset=utf-8"
    elif format == "pdf":
        try:
            # Reportlab est requis pour générer le PDF
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except ModuleNotFoundError:
            raise HTTPException(501, "Installez reportlab : pip install reportlab")
        from xml.sax.saxutils import escape
        styles = getSampleStyleSheet()
        st = styles["BodyText"]; st.fontSize, st.leading = 7, 9
        cell = lambda v: Paragraph(escape(str(v)), st)
        largeur = (landscape(A4)[0] - 48) / max(len(cols), 1)
        # Création et stylisation du tableau PDF
        t = Table([[cell(c) for c in cols]] + [[cell(v) for v in x] for x in rows],
                  colWidths=[largeur] * max(len(cols), 1), repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                               ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        buf = io.BytesIO()
        SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=24, rightMargin=24,
                          topMargin=24, bottomMargin=24).build(
            [Paragraph("Export des résultats", styles["Heading3"]), Spacer(1, 6), t])
        data, mime = buf.getvalue(), "application/pdf"
    elif format == "xlsx":
        try:
            # Openpyxl est requis pour générer le fichier Excel
            from openpyxl import Workbook
        except ModuleNotFoundError:
            raise HTTPException(501, "Installez openpyxl : pip install openpyxl")
        wb = Workbook(); ws = wb.active
        ws.append([_cell(c) for c in cols])
        for x in rows:
            ws.append([_cell(v) if v is None or isinstance(v, (int, float, str)) else str(v) for v in x])
        buf = io.BytesIO(); wb.save(buf)
        data, mime = buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        raise HTTPException(400, "Format inconnu (csv, tsv, json, md, xlsx, pdf)")
        
    ext = "md" if format == "md" else format
    return Response(data, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{nom}.{ext}"'})


# --- API : Administration (Droits "admin_dep" obligatoires) --------------------

