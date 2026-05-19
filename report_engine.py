from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generar_pdf_consolidado(datos, nombre_archivo):
    doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    style_titulo = ParagraphStyle('TxtTitle', parent=styles['Heading1'], fontSize=13, textColor=colors.HexColor('#002d5e'), alignment=1, spaceAfter=8)
    style_sub = ParagraphStyle('TxtSub', parent=styles['Normal'], fontSize=10, textColor=colors.black, spaceAfter=4)
    style_cell = ParagraphStyle('TxtCell', parent=styles['Normal'], fontSize=8, leading=10)
    style_cell_bold = ParagraphStyle('TxtCellB', parent=style_cell, fontName='Helvetica-Bold')
    style_header_cell = ParagraphStyle('TxtHead', parent=style_cell, fontName='Helvetica-Bold', textColor=colors.white, alignment=1)

    story = []

    # Encabezados de la Institución
    story.append(Paragraph("<b>UNIDAD EDUCATIVA SANTA SOFÍA</b>", style_titulo))
    story.append(Paragraph("<b>ACTA E INSTRUMENTO CONSOLIDADO DE EVALUACIÓN</b>", ParagraphStyle('S', parent=style_titulo, fontSize=11, spaceAfter=12)))
    story.append(Paragraph(f"<b>PROYECTO:</b> {datos['proyecto'].upper()}", style_sub))
    story.append(Spacer(1, 8))

    # ==========================================
    # SECCIÓN 1: EVALUACIÓN GRUPAL (COMPARTIDA)
    # ==========================================
    story.append(Paragraph("<b>I. EVALUACIÓN GENERAL DEL EQUIPO (CRITERIOS GRUPALES)</b>", style_cell_bold))
    story.append(Spacer(1, 4))
    
    criterios_t = ['1. Tema', '2. Objetivos', '3. Problema', '4. Conclusiones', '5. Presentación del Trabajo']
    criterios_d = ['1. Distribución de Espacio', '2. Imágenes', '3. Armonía Cromática', '4. Diseño y Ortografía', '5. Relación']
    criterios_e = ['1. Sincronización', '2. Conocimiento del Tema', '3. Orden y Pulcritud', '4. Manejo de Herramienta Digital', '5. Interacción con la Audiencia']
    
    base_detalles = datos['estudiantes'][0]['detalles']
    tabla_grupal_data = [[Paragraph("<b>BLOQUES Y CRITERIOS GRUPALES COMPARTIDOS</b>", style_header_cell), Paragraph("<b>PUNTOS</b>", style_header_cell)]]
    
    tabla_grupal_data.append([Paragraph("<b>TRABAJO</b>", style_cell_bold), ""])
    for idx, crit in enumerate(criterios_t):
        tabla_grupal_data.append([Paragraph(crit, style_cell), Paragraph(str(int(base_detalles['items_t'][idx])), style_cell_bold)])
        
    tabla_grupal_data.append([Paragraph("<b> DIAPOSITIVAS</b>", style_cell_bold), ""])
    for idx, crit in enumerate(criterios_d):
        tabla_grupal_data.append([Paragraph(crit, style_cell), Paragraph(str(int(base_detalles['items_d'][idx])), style_cell_bold)])
        
    tabla_grupal_data.append([Paragraph("<b>Equipo</b>", style_cell_bold), ""])
    for idx, crit in enumerate(criterios_e):
        tabla_grupal_data.append([Paragraph(crit, style_cell), Paragraph(str(int(base_detalles['items_e'][idx])), style_cell_bold)])

    t_grupal = Table(tabla_grupal_data, colWidths=[6.2*inch, 1.3*inch])
    t_grupal.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002d5e')),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ffd700')),
        ('BACKGROUND', (0,1), (1,1), colors.HexColor('#f2f2f2')),
        ('BACKGROUND', (0,7), (1,7), colors.HexColor('#f2f2f2')),
        ('BACKGROUND', (0,13), (1,13), colors.HexColor('#f2f2f2')),
        ('PADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_grupal)
    story.append(Spacer(1, 15))

    # ==========================================
    # SECCIÓN 2: CALIFICACIÓN INDIVIDUAL POR ALUMNO
    # ==========================================
    story.append(Paragraph("<b>EXPOSITOR</b>", style_cell_bold))
    story.append(Spacer(1, 5))
    
    criterios_i = [
        '1. Vocabulario y Expresión',
        '2. Coherencia y Fluidez',
        '3. Dominio de la Información Suministrada',
        '4. Uso Adecuado de Recursos',
        '5. Manejo de Respuestas ante el Jurado'
    ]

    # Generamos un bloque/tabla independiente para cada estudiante
    for est in datos['estudiantes']:
        d = est['detalles']
        nota_sea = d['p_trabajo'] + d['p_diapo'] + d['p_equipo'] + d['p_defensa']
        
        ext_list = est['jurados_externos']
        txt_externos = ", ".join([f"{x:.1f}" for x in ext_list]) if ext_list else "Ninguno"
        
        # Cabecera de la tabla del estudiante
        tabla_est_data = [
            [Paragraph(f"<b>EXPOSITOR: {est['nombre'].upper()}</b>", style_header_cell), Paragraph("<b>PUNTOS</b>", style_header_cell)]
        ]
        
        # Insertamos los 5 criterios individuales desglosados
        for idx, crit in enumerate(criterios_i):
            puntos_crit = str(int(d['items_i'][idx]))
            tabla_est_data.append([Paragraph(crit, style_cell), Paragraph(puntos_crit, style_cell_bold)])
            
        # Filas de consolidación de promedios
        tabla_est_data.append([Paragraph("<b>NOTA BASE CALCULADA (SEA)</b>", style_cell_bold), Paragraph(f"{nota_sea:.2f}", style_cell_bold)])
        tabla_est_data.append([Paragraph(f"<b>CALIFICACIONES JURADOS EXTERNOS</b>", style_cell), Paragraph(txt_externos, style_cell)])
        tabla_est_data.append([Paragraph("<b>NOTA FINAL DEFINITIVA CONSOLIDADA</b>", style_cell_bold), Paragraph(f"{est['nota_principal']:.2f}", style_cell_bold)])
        
        # Construcción estética de la tabla del alumno
        t_est = Table(tabla_est_data, colWidths=[5.5*inch, 2.0*inch])
        t_est.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002d5e')),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#002d5e')),
            ('BACKGROUND', (0,6), (1,6), colors.HexColor('#f2f2f2')),
            ('BACKGROUND', (0,8), (1,8), colors.HexColor('#ffeaa7')),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        
        story.append(t_est)
        story.append(Spacer(1, 12)) # Espacio de separación entre estudiantes

    doc.build(story)