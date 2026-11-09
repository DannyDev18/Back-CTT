"""
Generador de Órdenes de Pago Institucionales de la Universidad Técnica de Ambato (UTA).
Emite la Orden de Pago Oficial generada en el sistema para cancelación en:
1. Ventanillas de Dirección Financiera UTA (Campus Huachi).
2. Transferencia / Depósito en la Cuenta Corriente Institucional de la UTA.
"""
import io
import json
from datetime import datetime, timedelta
from typing import Optional, Any

import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas


class UncompressedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pageCompression = 0


def generate_uta_order_qr(payload_data: dict) -> io.BytesIO:
    """Genera imagen QR en memoria con la información de verificación de la orden institucional."""
    qr_str = json.dumps(payload_data, ensure_ascii=False)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(qr_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00345e", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def generate_uta_payment_order_pdf(
    enrollment: Any,
    user: Any,
    congress: Optional[Any] = None,
    course: Optional[Any] = None,
    db: Optional[Any] = None,
    due_days: int = 5,
) -> io.BytesIO:
    """
    Genera el PDF oficial de la Orden de Pago UTA para ventanilla o transferencia bancaria.
    """
    if user is None and db is not None:
        user_id = getattr(enrollment, "id_user_platform", None)
        if user_id:
            from src.models.user_platform import UserPlatform
            user = db.get(UserPlatform, user_id)

    enrollment_id = getattr(enrollment, "id", 1) or 1
    amount = float(getattr(enrollment, "amount", 0.0) or 0.0)
    tariff_type = getattr(enrollment, "tariff_type", "ESTUDIANTE UTA") or "Estudiante UTA"

    # Fecha de emisión y vencimiento
    enr_date = getattr(enrollment, "enrollment_date", None)
    if not isinstance(enr_date, datetime):
        enr_date = datetime.utcnow()

    fecha_emision = enr_date.strftime("%d/%m/%Y %H:%M")
    fecha_vencimiento = (enr_date + timedelta(days=due_days)).strftime("%d/%m/%Y 23:59")

    # Identificadores institucionales
    ruc_institucional = "1860000880001"
    order_code = f"UTA-FISEI-2026-{enrollment_id:06d}"

    # Datos del estudiante / participante
    student_id = getattr(user, "identification", "1800000000") or "1800000000"
    first_name = getattr(user, "first_name", "") or ""
    last_name = getattr(user, "first_last_name", "") or ""
    student_name = f"{first_name} {last_name}".strip() or "ESTUDIANTE UTA"
    student_email = getattr(user, "email", "usuario@uta.edu.ec") or "usuario@uta.edu.ec"
    student_phone = getattr(user, "cellphone", "N/A") or "N/A"
    user_role = str(getattr(user, "type", "Estudiante")).replace("UserPlatformType.", "")

    # Descripción del rubro académico
    if congress:
        item_code = f"CONG-{getattr(congress, 'id_congreso', enrollment_id)}"
        item_title = getattr(congress, "nombre", "Congreso Científico FISEI - UTA")
        item_type = "Congreso Internacional"
        item_sede = getattr(congress, "lugar_sede", "Campus Huachi - FISEI")
    elif course:
        item_code = f"CURS-{getattr(course, 'id', enrollment_id)}"
        item_title = getattr(course, "title", None) or getattr(course, "name", "Curso de Formación Continua CTT")
        item_type = "Curso de Capacitación"
        item_sede = getattr(course, "place", "Laboratorios FISEI - Campus Huachi")
    else:
        item_code = f"ACAD-{enrollment_id:04d}"
        item_title = "Programa Académico CTT - FISEI"
        item_type = "Capacitación Continua"
        item_sede = "Campus Huachi - Ambato"

    # Preparar buffer y documento
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    doc.pageCompression = 0

    c_primary = colors.HexColor("#00345e")
    c_primary_light = colors.HexColor("#e8f0fe")
    c_border = colors.HexColor("#cbd5e1")
    c_text_dark = colors.HexColor("#0f172a")
    c_text_muted = colors.HexColor("#475569")
    c_accent = colors.HexColor("#b45309")
    c_accent_bg = colors.HexColor("#fef3c7")

    styles = getSampleStyleSheet()

    title_inst_style = ParagraphStyle(
        "UTAOrderTitleInst",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=c_primary,
    )
    subtitle_inst_style = ParagraphStyle(
        "UTAOrderSubTitleInst",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=c_text_muted,
    )
    order_title_style = ParagraphStyle(
        "UTAOrderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        alignment=TA_CENTER,
    )
    lbl_style = ParagraphStyle(
        "UTALbl",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=c_text_muted,
    )
    val_style = ParagraphStyle(
        "UTAVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=c_text_dark,
    )
    val_bold = ParagraphStyle(
        "UTAValBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=c_primary,
    )
    box_header_style = ParagraphStyle(
        "UTABoxHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=c_primary,
    )
    instr_style = ParagraphStyle(
        "UTAInstr",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=c_text_dark,
    )

    story = []

    # 1. ENCABEZADO INSTITUCIONAL
    emisor_data = [
        [Paragraph("UNIVERSIDAD TÉCNICA DE AMBATO", title_inst_style)],
        [Paragraph("<b>DIRECCIÓN FINANCIERA</b> · DEPARTAMENTO DE RECAUDACIÓN Y TESORERÍA", subtitle_inst_style)],
        [Paragraph("<b>CENTRO DE TRANSFERENCIA Y DESARROLLO DE TECNOLOGÍAS (CTT)</b>", subtitle_inst_style)],
        [Paragraph("Facultad de Ingeniería en Sistemas, Electrónica e Industrial (FISEI)", subtitle_inst_style)],
        [Paragraph(f"<b>RUC:</b> {ruc_institucional} · Campus Huachi, Ambato - Ecuador", subtitle_inst_style)],
    ]
    emisor_table = Table(emisor_data, colWidths=[310])
    emisor_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))

    # Caja con Nº de Orden y Fechas
    caja_orden_data = [
        [Paragraph("ORDEN DE PAGO INSTITUCIONAL", order_title_style)],
        [Paragraph(f"<b>CÓDIGO DE TRÁMITE:</b><br/><font size=11 color='#00345e'><b>{order_code}</b></font>", ParagraphStyle("OCode", fontName="Helvetica", fontSize=8.5, alignment=TA_CENTER, leading=14))],
        [Paragraph(f"<b>Fecha de Emisión:</b> {fecha_emision}", val_style)],
        [Paragraph(f"<b>Vence:</b> <font color='#b45309'><b>{fecha_vencimiento}</b></font>", val_style)],
    ]
    caja_orden_table = Table(caja_orden_data, colWidths=[230])
    caja_orden_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, c_primary),
        ("BACKGROUND", (0, 0), (-1, 0), c_primary_light),
        ("ALIGN", (0, 0), (-1, 1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))

    header_table = Table([[emisor_table, caja_orden_table]], colWidths=[310, 230])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # 2. DATOS DEL PARTICIPANTE / ESTUDIANTE
    story.append(Paragraph("DATOS DEL PARTICIPANTE / SOLICITANTE", box_header_style))
    story.append(Spacer(1, 3))

    user_info_data = [
        [
            Paragraph("<b>Nombres y Apellidos:</b>", lbl_style),
            Paragraph(student_name, val_style),
            Paragraph("<b>Cédula / Identificación:</b>", lbl_style),
            Paragraph(student_id, val_bold),
        ],
        [
            Paragraph("<b>Correo Electrónico:</b>", lbl_style),
            Paragraph(student_email, val_style),
            Paragraph("<b>Tipo de Usuario / Rol:</b>", lbl_style),
            Paragraph(user_role, val_style),
        ],
        [
            Paragraph("<b>Teléfono / Contacto:</b>", lbl_style),
            Paragraph(student_phone, val_style),
            Paragraph("<b>Tarifa Institucional:</b>", lbl_style),
            Paragraph(f"<font color='#00345e'><b>{tariff_type}</b></font>", val_style),
        ],
    ]
    user_table = Table(user_info_data, colWidths=[110, 180, 120, 130])
    user_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(user_table)
    story.append(Spacer(1, 10))

    # 3. DETALLE ECONÓMICO Y CONCEPTO DE PAGO
    story.append(Paragraph("DETALLE DEL RUBRO ACADÉMICO A PAGAR", box_header_style))
    story.append(Spacer(1, 3))

    items_data = [
        [
            Paragraph("<b>Código</b>", lbl_style),
            Paragraph("<b>Descripción del Rubro Académico</b>", lbl_style),
            Paragraph("<b>Tipo / Modalidad</b>", lbl_style),
            Paragraph("<b>Tarifa</b>", lbl_style),
            Paragraph("<b>Total (USD)</b>", lbl_style),
        ],
        [
            Paragraph(item_code, val_style),
            Paragraph(f"<b>{item_title}</b><br/><font size=7 color='#64748b'>{item_sede}</font>", val_style),
            Paragraph(item_type, val_style),
            Paragraph(tariff_type, val_style),
            Paragraph(f"<b>${amount:.2f}</b>", val_bold),
        ],
    ]
    items_table = Table(items_data, colWidths=[65, 235, 100, 75, 65])
    items_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, c_primary),
        ("BACKGROUND", (0, 0), (-1, 0), c_primary_light),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (4, 0), (4, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 6))

    # Cuadro de Totales
    totals_data = [
        [Paragraph("<b>Subtotal Servicios Educativos:</b>", val_style), Paragraph(f"${amount:.2f}", val_style)],
        [Paragraph("<b>IVA 0% (Educación exenta Art. 56 LORTI):</b>", val_style), Paragraph("$0.00", val_style)],
        [Paragraph("<b>TOTAL A CANCELAR:</b>", ParagraphStyle("TotLbl", fontName="Helvetica-Bold", fontSize=10, textColor=c_primary)), Paragraph(f"<b>${amount:.2f} USD</b>", ParagraphStyle("TotVal", fontName="Helvetica-Bold", fontSize=11, textColor=c_primary, alignment=TA_RIGHT))],
    ]
    totals_table = Table(totals_data, colWidths=[380, 160])
    totals_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ("BACKGROUND", (0, 2), (-1, 2), c_primary_light),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 10))

    # 4. MODALIDADES DE PAGO AUTORIZADAS (VENTANILLA O TRANSFERENCIA)
    story.append(Paragraph("MODALIDADES DE PAGO AUTORIZADAS POR LA DIRECCIÓN FINANCIERA", box_header_style))
    story.append(Spacer(1, 3))

    qr_payload = {
        "orden": order_code,
        "ruc_institucion": ruc_institucional,
        "estudiante": student_name,
        "cedula": student_id,
        "monto": f"{amount:.2f}",
        "rubro": item_title,
        "vencimiento": fecha_vencimiento,
    }
    qr_buffer = generate_uta_order_qr(qr_payload)
    qr_image = Image(qr_buffer, width=80, height=80)

    instrucciones_data = [
        [
            Paragraph(
                "<b>CANAL 1 · PAGO EN VENTANILLAS DE DIRECCIÓN FINANCIERA:</b><br/>"
                "• Acérquese a las ventanillas de Recaudación en el <b>Edificio de Administración Central UTA</b> (Campus Huachi, Av. Los Chasquis y Río Guayllabamba).<br/>"
                f"• Presente esta orden de pago impresa o digital e indique el Código de Trámite: <b>{order_code}</b>.<br/>"
                "• Horario de atención: Lunes a Viernes de 08:00 a 16:30 ininterrumpidamente.<br/><br/>"
                "<b>CANAL 2 · TRANSFERENCIA O DEPÓSITO BANCARIO:</b><br/>"
                "• <b>Banco:</b> Banco del Pacífico<br/>"
                "• <b>Tipo de Cuenta:</b> Cuenta Corriente Nº <b>07358245</b><br/>"
                "• <b>Beneficiario:</b> Universidad Técnica de Ambato (RUC: 1860000880001)<br/>"
                f"• <b>Referencia obligatoria:</b> Cédula {student_id} / Orden {order_code}<br/>"
                "• <b>Subida del comprobante:</b> Ingrese a la plataforma web CTT y suba la foto o PDF del comprobante para validación financiera inmediata.",
                instr_style
            ),
            qr_image
        ]
    ]
    instrucciones_table = Table(instrucciones_data, colWidths=[440, 100])
    instrucciones_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(instrucciones_table)
    story.append(Spacer(1, 12))

    # 5. PIE DE PÁGINA Y LEGALIDAD
    footer_text = Paragraph(
        "<i>Documento oficial emitido por el sistema CTT-FISEI conectado con la Dirección Financiera de la Universidad Técnica de Ambato. "
        f"Esta orden garantiza el cupo hasta la fecha límite: {fecha_vencimiento}. Transcurrido este plazo, la orden caducará automáticamente.</i>",
        ParagraphStyle("UTAFooter", fontName="Helvetica", fontSize=7, leading=9, textColor=c_text_muted, alignment=TA_CENTER)
    )
    story.append(footer_text)

    doc.build(story, canvasmaker=UncompressedCanvas)
    buffer.seek(0)
    return buffer

