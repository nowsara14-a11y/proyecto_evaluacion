from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def generar_pdf_consolidado(datos, nombre_archivo):
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    for est in datos['estudiantes']:
        d = est['detalles']
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("<b>UNIDAD EDUCATIVA SANTA SOFÍA - INSTRUMENTO DE EVALUACIÓN</b>", styles['Title']))
        story.append(Paragraph(f"<b>Proyecto:</b> {datos['proyecto']} | <b>Estudiante:</b> {est['nombre']}", styles['Normal']))
        
        def v(lista, i): return lista[i] if lista and len(lista) > i else ""

        data = [
            ['CRITERIOS', '4', '3', '2', '1', 'Puntos'],
            ['I. TRABAJO', v(d['items_t'],0), v(d['items_t'],1), v(d['items_t'],2), v(d['items_t'],3), f"{d['p_trabajo']}/20"],
            ['II. DIAPOSITIVA', v(d['items_d'],0), v(d['items_d'],1), v(d['items_d'],2), v(d['items_d'],3), f"{d['p_diapo']}/20"],
            ['III. EQUIPO', v(d['items_e'],0), v(d['items_e'],1), v(d['items_e'],2), v(d['items_e'],3), f"{d['p_equipo']}/20"],
            ['IV. DEFENSA IND.', v(d['items_i'],0), v(d['items_i'],1), v(d['items_i'],2), v(d['items_i'],3), f"{d['p_defensa']}/20"],
            ['CALIFICACIÓN FINAL', '', '', '', '', f"<b>{est['nota_principal']}</b>"]
        ]

        t = Table(data, colWidths=[3*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 1*inch])
        t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
        story.append(t)
        story.append(PageBreak())

    doc.build(story)