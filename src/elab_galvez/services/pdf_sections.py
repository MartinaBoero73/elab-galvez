import math
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors

from elab_galvez.domain.models import ReciboSueldo, TipoConcepto
from elab_galvez.services.pdf_utils import obtener_imagen_servidor, formatear_moneda, generar_grafico_torta

def generar_cabecera(recibo: ReciboSueldo, estilo_normal, estilo_negrita, estilo_titulo, estilo_tabla, logo_filename=None) -> list:
    """Builds the document header, including employer data and legal metadata."""
    elementos = []

    periodo_str = recibo.periodo.formato_estandar
    periodo_imputado_str = recibo.periodo_imputado.formato_estandar if recibo.periodo_imputado else ""

    up_periodo_str = recibo.periodo_ultimo_aporte.formato_estandar if recibo.periodo_ultimo_aporte else ""
    
    fecha_aportes_str = f'{recibo.fecha_ultimo_aporte.strftime("%d/%m/%Y")}  PERIODO {up_periodo_str}' if recibo.fecha_ultimo_aporte else ""
    basico_str = formatear_moneda(recibo.sueldo_basico)
    
    logo_img = obtener_imagen_servidor("logos", logo_filename, max_width=120, max_height=45)
    
    info_empleador = []
    if logo_img:
        info_empleador.append(logo_img)
        info_empleador.append(Spacer(1, 5))
        
    info_empleador.extend([
        Paragraph(f"<b>{recibo.empleador.nombre}</b>", estilo_negrita),
        Paragraph(recibo.empleador.domicilio, estilo_normal),
        Paragraph(f"CUIT: {recibo.empleador.cuit}", estilo_normal),
    ])
    
    info_ley = [
        Paragraph("<b>RECIBO DE SUELDOS LEY 20.744</b>", estilo_titulo),
        Paragraph("<b>SEGÚN ANEXO III DECRETO 407/26</b>", estilo_titulo),
        Spacer(1, 4), 
        Paragraph(f"<b>Período:</b> {periodo_str}", estilo_normal),
        Paragraph(f"<b>Período Imputado:</b> {periodo_imputado_str}", estilo_normal),
        Spacer(1, 4), 
        Paragraph(f"<b>Fecha Aportes:</b> {fecha_aportes_str}", estilo_normal),
        Paragraph(f"<b>Banco:</b> {recibo.empleado.banco_deposito or ''}", estilo_normal),
        Paragraph(f"<b>Básico:</b> {basico_str}", estilo_negrita),
    ]
    
    tabla_superior = Table([[info_empleador, info_ley]], colWidths=[270, 270])
    tabla_superior.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
    elementos.append(tabla_superior)
    elementos.append(Spacer(1, 6)) 
    
    fecha_ingreso_str = recibo.empleado.fecha_ingreso.strftime("%d/%m/%Y") if recibo.empleado.fecha_ingreso else ""
    fecha_ingreso_rec_str = recibo.empleado.fecha_ingreso_reconocida.strftime("%d/%m/%Y") if recibo.empleado.fecha_ingreso_reconocida else ""
    
    datos_emp_superior = [
        ["Apellido y Nombre", "Legajo", "Conv./Categoría", "Calificación Profesional"],
        [
            Paragraph(f"<b>{recibo.empleado.nombre}</b>", estilo_negrita), 
            Paragraph(f"<b>{recibo.empleado.legajo}</b>", estilo_negrita), 
            Paragraph(f'<b>"{recibo.empleado.categoria}"</b>', estilo_negrita),
            Paragraph(f'<b>"{recibo.empleado.calificacion_profesional}"</b>', estilo_negrita)
        ]
    ]
    
    datos_emp_inferior = [
        ["Documento", "C.U.I.L.", "Fecha Ingreso", "FEC.ING.REC."],
        [f"{recibo.empleado.documento or ''}", recibo.empleado.cuil or "", fecha_ingreso_str, fecha_ingreso_rec_str]
    ]
    
    t_sup = Table(datos_emp_superior, colWidths=[180, 60, 150, 150])
    t_inf = Table(datos_emp_inferior, colWidths=[135, 135, 135, 135])
    
    estilo_grilla = TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica'),
        ('TEXTCOLOR', (0,0), (-1,0), colors.gray),
        ('FONTSIZE', (0,0), (-1,0), 6.5), 
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LINEBELOW', (0,1), (-1,1), 0.5, colors.lightgrey), 
    ])
    
    t_sup.setStyle(estilo_grilla)
    t_inf.setStyle(estilo_grilla)
    
    tabla_empleado = Table([[t_sup], [t_inf]], colWidths=[540])
    tabla_empleado.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    
    elementos.append(tabla_empleado)
    elementos.append(Spacer(1, 8)) 
    return elementos

def generar_seccion_costo_empleador(recibo, estilo_tabla, estilo_tabla_negrita, estilo_tabla_der, estilo_tabla_negrita_der, estilo_tabla_negrita_blanco, estilo_tabla_negrita_der_blanco) -> list:
    """Builds the employer cost section, mapping contributions into a unified grid."""
    elementos = []
    
    datos_tabla = [
        [
            Paragraph("<b>COSTO TOTAL EMPLEADOR</b>", estilo_tabla_negrita_blanco), "", "", 
            Paragraph(f"<b>{formatear_moneda(recibo.costo_total_empleador)}</b>", estilo_tabla_negrita_der_blanco)
        ],
        [
            Paragraph("<b>CONCEPTO</b>", estilo_tabla_negrita), 
            Paragraph("<b>UNIDAD</b>", estilo_tabla_negrita_der), 
            Paragraph("<b>BASE</b>", estilo_tabla_negrita_der), 
            Paragraph("<b>MONTO</b>", estilo_tabla_negrita_der)
        ]
    ]
    
    for contrib in recibo.contribuciones_patronales:
        unidad_str = str(contrib.unidad_porcentaje) if contrib.unidad_porcentaje else ""
        base_str = formatear_moneda(contrib.base_calculo) if contrib.base_calculo else ""
        
        datos_tabla.append([
            Paragraph(contrib.descripcion, estilo_tabla),
            Paragraph(unidad_str, estilo_tabla_der),
            Paragraph(base_str, estilo_tabla_der),
            Paragraph(formatear_moneda(contrib.monto), estilo_tabla_der)
        ])
        
    datos_tabla.append([
        Paragraph("<b>SUBTOTAL CONTRIBUCIONES EMPLEADOR</b>", estilo_tabla_negrita), "", "",
        Paragraph(f"<b>{formatear_moneda(recibo.total_contribuciones_patronales)}</b>", estilo_tabla_negrita_der)
    ])
    
    datos_tabla.append([
        Paragraph("<b>SUELDO BRUTO</b>", estilo_tabla_negrita_blanco), "", "",
        Paragraph(f"<b>{formatear_moneda(recibo.sueldo_bruto)}</b>", estilo_tabla_negrita_der_blanco)
    ])
    
    num_filas = len(datos_tabla)
    
    estilos_tabla = [
        ('SPAN', (0, 0), (2, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#404040")),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#C0C0C0")), 
        ('ALIGN', (0, 1), (0, 1), 'CENTER'),
        ('ALIGN', (1, 1), (-1, 1), 'RIGHT'),
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 2), (0, -3), 'LEFT'),
        ('ALIGN', (1, 2), (-1, -3), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5), 
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
    ]
    
    # Dynamic zebra-striping
    for i in range(2, num_filas - 2):
        bg_color = colors.HexColor("#E5E5E5") if i % 2 == 0 else colors.HexColor("#F4F4F4")
        estilos_tabla.append(('BACKGROUND', (0, i), (-1, i), bg_color))
        
    estilos_tabla.extend([
        ('SPAN', (0, num_filas - 2), (2, num_filas - 2)),
        ('LINEABOVE', (0, num_filas - 2), (-1, num_filas - 2), 0.5, colors.black),
        ('BACKGROUND', (0, num_filas - 2), (-1, num_filas - 2), colors.white),
        ('ALIGN', (0, num_filas - 2), (0, num_filas - 2), 'RIGHT'),
        ('SPAN', (0, num_filas - 1), (2, num_filas - 1)),
        ('BACKGROUND', (0, num_filas - 1), (-1, num_filas - 1), colors.HexColor("#404040")),
        ('ALIGN', (0, num_filas - 1), (0, num_filas - 1), 'LEFT'),
    ])
    
    t_unificada = Table(datos_tabla, colWidths=[270, 70, 100, 100])
    t_unificada.setStyle(TableStyle(estilos_tabla))
    elementos.append(t_unificada)
    elementos.append(Spacer(1, 8))
    return elementos

def generar_seccion_detalle_haberes(recibo, estilo_tabla, estilo_tabla_negrita, estilo_tabla_der, estilo_tabla_negrita_der, estilo_tabla_negrita_blanco, estilo_tabla_negrita_der_blanco) -> list:
    """Builds the earnings and deductions detail grid across 3 monetary columns."""
    elementos = []
    
    datos_tabla = [
        [
            Paragraph("<b>CÓD.</b>", estilo_tabla_negrita), 
            Paragraph("<b>DETALLE</b>", estilo_tabla_negrita), 
            Paragraph("<b>CANTIDAD</b>", estilo_tabla_negrita_der), 
            Paragraph("<b>HABERES</b>", estilo_tabla_negrita_der), 
            Paragraph("<b>DEDUCCIONES</b>", estilo_tabla_negrita_der),
            Paragraph("<b>NO REMUNERAT.</b>", estilo_tabla_negrita_der)
        ]
    ]
    
    for concepto in recibo.conceptos:
        unidad_str = ""
        if concepto.unidad:
            try:
                # Math validation to bypass empty zero strings
                if float(str(concepto.unidad).replace(",", ".")) != 0:
                    unidad_str = str(concepto.unidad)
            except ValueError:
                # Renders plain text (e.g., "Mes", "Dias") if cast fails
                unidad_str = str(concepto.unidad)
        
        m_haber = formatear_moneda(concepto.monto) if concepto.tipo_concepto == TipoConcepto.REMUNERATIVO else ""
        m_deducc = formatear_moneda(concepto.monto) if concepto.tipo_concepto == TipoConcepto.DESCUENTO else ""
        m_norem = formatear_moneda(concepto.monto) if concepto.tipo_concepto == TipoConcepto.NO_REMUNERATIVO else ""
        
        datos_tabla.append([
            Paragraph(str(concepto.codigo or ""), estilo_tabla),
            Paragraph(concepto.descripcion, estilo_tabla),
            Paragraph(unidad_str, estilo_tabla_der),
            Paragraph(m_haber, estilo_tabla_der),
            Paragraph(m_deducc, estilo_tabla_der),
            Paragraph(m_norem, estilo_tabla_der)
        ])
        
    num_filas = len(datos_tabla)
    
    datos_tabla.append([
        "", Paragraph("<b>SUBTOTALES</b>", estilo_tabla_negrita_der), "",
        Paragraph(f"<b>{formatear_moneda(recibo.total_remunerativo)}</b>", estilo_tabla_negrita_der),
        Paragraph(f"<b>{formatear_moneda(recibo.total_descuentos)}</b>", estilo_tabla_negrita_der),
        Paragraph(f"<b>{formatear_moneda(recibo.total_no_remunerativo)}</b>", estilo_tabla_negrita_der)
    ])
    
    estilos_tabla = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#C0C0C0")), 
        ('ALIGN', (0,0), (1,0), 'CENTER'), ('ALIGN', (2,0), (-1,0), 'RIGHT'), 
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,1), (1,-1), 'LEFT'), ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 1.5), ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('RIGHTPADDING', (0,0), (-1,-1), 3), ('LEFTPADDING', (0,0), (-1,-1), 3),
    ]
    
    for i in range(1, num_filas):
        bg_color = colors.HexColor("#E5E5E5") if i % 2 == 0 else colors.HexColor("#F4F4F4")
        estilos_tabla.append(('BACKGROUND', (0, i), (-1, i), bg_color))
        
    estilos_tabla.extend([
        ('LINEABOVE', (0, num_filas), (-1, num_filas), 1, colors.black),
        ('BACKGROUND', (0, num_filas), (-1, num_filas), colors.white),
    ])
        
    t_conceptos = Table(datos_tabla, colWidths=[30, 175, 50, 95, 95, 95])
    t_conceptos.setStyle(TableStyle(estilos_tabla))
    elementos.append(t_conceptos)
    elementos.append(Spacer(1, 6))
    
    t_neto = Table([
        [
            Paragraph("<b>TOTAL NETO</b>", estilo_tabla_negrita_blanco), 
            Paragraph(f"<b>{formatear_moneda(recibo.sueldo_neto_bolsillo)}</b>", estilo_tabla_negrita_der_blanco)
        ]
    ], colWidths=[440, 100]) 
    
    t_neto.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#404040")), 
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('RIGHTPADDING', (0,0), (-1,-1), 3), ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elementos.append(t_neto)
    elementos.append(Spacer(1, 8))
    
    return elementos

def generar_seccion_final(recibo, estilo_normal, estilo_negrita, estilo_titulo, firma_emp_filename=None, firma_trab_filename=None) -> list:
    """Builds the footer, appending the composition matrix, pie chart, and legal signatures."""
    elementos = []
    
    elementos.append(Paragraph("<b>DETALLE DE LA COMPOSICIÓN SALARIAL</b>", estilo_negrita))
    elementos.append(Spacer(1, 3))
    
    comp = recibo.composicion_salarial
    rubros_para_tabla = [
        ("Sindical", comp.sindical), ("Seguridad Social", comp.seguridad_social),
        ("Obra Social", comp.obra_social), ("INSSJP", comp.inssjp),
        ("ART", comp.art), ("SCVO", comp.scvo)
    ]
    
    datos_desglose = []
    for nombre, rubro in rubros_para_tabla:
        if rubro.total > 0:
            bloque_texto = [
                Paragraph(f"<b>Total {nombre}</b>", estilo_normal),
                Paragraph(f"<b>{formatear_moneda(rubro.total)}</b>", estilo_negrita),
                Spacer(1, 1),
                Paragraph(f"Empleador: {formatear_moneda(rubro.empleador)}", estilo_normal),
                Paragraph(f"Trabajador: {formatear_moneda(rubro.trabajador)}", estilo_normal),
                Spacer(1, 3) 
            ]
            datos_desglose.append(bloque_texto)
            
    mitad = math.ceil(len(datos_desglose) / 2)
    celda_izq_1 = datos_desglose[:mitad] 
    celda_izq_2 = datos_desglose[mitad:] 

    img_torta = Image(generar_grafico_torta(recibo), width=200, height=130, kind='proportional')

    t_detalle = Table([[celda_izq_1, celda_izq_2, img_torta]], colWidths=[180, 180, 180])
    t_detalle.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (2,0), (2,0), 'CENTER')]))
    elementos.append(t_detalle)
    elementos.append(Spacer(1, 5))
    
    monto_letras = recibo.importe_en_letras or ""
    elementos.append(Paragraph(f"<b>Son {monto_letras}</b>", estilo_normal))
    elementos.append(Spacer(1, 5))
    
    if recibo.cbu_acreditacion:
        elementos.append(Paragraph(f"<b>ACREDITADO EN CBU: {recibo.cbu_acreditacion}</b>", estilo_normal))
        elementos.append(Spacer(1, 5))
        
    elementos.append(Paragraph("Recibí conforme el importe neto de la presente liquidación y recibo y duplicado de los mismos.", estilo_normal))
    
    img_firma_trab = obtener_imagen_servidor("firmas", firma_trab_filename, max_width=120, max_height=50) or Spacer(1, 50)
    img_firma_emp = obtener_imagen_servidor("firmas", firma_emp_filename, max_width=120, max_height=50) or Spacer(1, 50)
    
    datos_firmas = [
        [img_firma_trab, img_firma_emp],
        [
            Paragraph(f"<b>{recibo.empleado.nombre}</b><br/>Empleado N° {recibo.empleado.legajo}", estilo_titulo),
            Paragraph(f"P/{recibo.empleador.nombre}", estilo_titulo)
        ]
    ]
    t_firmas = Table(datos_firmas, colWidths=[270, 270])
    t_firmas.setStyle(TableStyle([
        ('LINEABOVE', (0,1), (0,1), 0.5, colors.black), ('LINEABOVE', (1,1), (1,1), 0.5, colors.black), 
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'BOTTOM'), 
    ]))
    elementos.append(t_firmas)
    return elementos