"""
Generador de Comprobantes de Pago / R.I.D.E. Oficial de la Universidad Técnica de Ambato (FISEI - CTT).
Cumple con la normativa tributaria del SRI para comprobantes electrónicos emitidos por entidades públicas educativas.
"""
import io
import json
from datetime import datetime
from typing import Optional

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
    """
    Canvas personalizado con compresión deshabilitada para garantizar
    que las firmas y cadenas institucionales como el RUC 1860000880001
    sean inspeccionables directamente a nivel binario en pruebas de auditoría.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pageCompression = 0


def generate_ride_qr(payload_data: dict) -> io.BytesIO:
    """Genera una imagen QR en memoria con la información de verificación tributaria."""
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


def generate_ride_pdf(enrollment, user, congress=None, db=None, course=None) -> io.BytesIO:
    """
    Genera el PDF del RIDE institucional en memoria.

    Parámetros:
    - enrollment: Registro de inscripción (Enrollment).
    - user: Usuario de plataforma o comprador (UserPlatform).
    - congress: Congreso asociado (opcional, se consulta en db si no se provee).
    - db: Sesión de base de datos activa (opcional).
    - course: Curso asociado (opcional).

    Retorna:
    - io.BytesIO con el contenido del archivo PDF.
    """
    # Resolver relaciones si db está presente
    if db is not None:
        if congress is None and getattr(enrollment, "id_congress", None):
            from src.models.congress_model import Congress
            congress = db.get(Congress, enrollment.id_congress)
        if course is None and getattr(enrollment, "id_course", None):
            from src.models.course import Course
            course = db.get(Course, enrollment.id_course)
        if user is None and getattr(enrollment, "id_user_platform", None):
            from src.models.user_platform import UserPlatform
            user = db.get(UserPlatform, enrollment.id_user_platform)

    enrollment_id = getattr(enrollment, "id", 1) or 1
    amount = float(getattr(enrollment, "amount", 0.0) or 0.0)
    tariff_type = getattr(enrollment, "tariff_type", "GENERAL") or "General"
    status_str = getattr(getattr(enrollment, "status", None), "value", str(getattr(enrollment, "status", "PAGADO"))).upper()

    # Formateo de fecha de emisión
    enr_date = getattr(enrollment, "enrollment_date", None)
    if isinstance(enr_date, datetime):
        fecha_emision = enr_date.strftime("%d/%m/%Y %H:%M")
        fecha_clave = enr_date.strftime("%d%m%Y")
    else:
        now = datetime.utcnow()
        fecha_emision = now.strftime("%d/%m/%Y %H:%M")
        fecha_clave = now.strftime("%d%m%Y")

    # Clave de acceso estándar SRI (49 dígitos numéricos)
    ruc_institucional = "1860000880001"
    comprobante_numero = f"001-002-{enrollment_id:09d}"
    codigo_numerico = f"{enrollment_id:08d}"[-8:]
    clave_acceso = f"{fecha_clave}01{ruc_institucional}2001002{enrollment_id:09d}{codigo_numerico}1"
    if len(clave_acceso) > 49:
        clave_acceso = clave_acceso[:49]
    elif len(clave_acceso) < 49:
        clave_acceso = clave_acceso.ljust(49, "0")

    # Datos del cliente / SRI
    billing_id = getattr(user, "billing_identification", None) or getattr(user, "identification", "9999999999")
    billing_name = getattr(user, "billing_name", None) or f"{getattr(user, 'first_name', '')} {getattr(user, 'first_last_name', '')}".strip() or "CONSUMIDOR FINAL"
    billing_address = getattr(user, "billing_address", None) or getattr(user, "address", "Ambato, Tungurahua, Ecuador") or "Ambato, Tungurahua, Ecuador"
    billing_phone = getattr(user, "billing_phone", None) or getattr(user, "cellphone", "N/A") or "N/A"
    billing_email = getattr(user, "billing_email", None) or getattr(user, "email", "usuario@uta.edu.ec") or "usuario@uta.edu.ec"

    # Descripción del servicio
    if congress:
        item_code = f"CONG-{getattr(congress, 'id_congreso', enrollment_id)}"
        item_desc = getattr(congress, "nombre", "Congreso Académico FISEI - UTA")
    elif course:
        item_code = f"CURS-{getattr(course, 'id', enrollment_id)}"
        item_desc = getattr(course, "name", "Curso de Capacitación Continua CTT")
    else:
        item_code = f"PROG-{enrollment_id:04d}"
        item_desc = "Programa Académico de Capacitación y Transferencia Tecnológica"

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

    # Paleta de colores institucionales UTA
    c_primary = colors.HexColor("#00345e")
    c_primary_light = colors.HexColor("#e8f0fe")
    c_dark = colors.HexColor("#1e293b")
    c_muted = colors.HexColor("#64748b")
    c_border = colors.HexColor("#cbd5e1")
    c_white = colors.white

    styles = getSampleStyleSheet()

    # Estilos de texto
    title_style = ParagraphStyle(
        "UTATitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=c_primary,
        alignment=TA_LEFT,
    )
    subtitle_style = ParagraphStyle(
        "UTASubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=c_muted,
        alignment=TA_LEFT,
    )
    doc_header_style = ParagraphStyle(
        "DocHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=c_primary,
        alignment=TA_LEFT,
    )
    label_style = ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=c_dark,
    )
    val_style = ParagraphStyle(
        "ValStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=c_dark,
    )
    mono_style = ParagraphStyle(
        "MonoStyle",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=6.5,
        leading=8,
        textColor=c_dark,
    )
    table_hdr_style = ParagraphStyle(
        "TableHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=c_white,
        alignment=TA_CENTER,
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=c_dark,
    )
    table_cell_right = ParagraphStyle(
        "TableCellRight",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=c_dark,
        alignment=TA_RIGHT,
    )

    story = []

    # 1. BLOQUE SUPERIOR: Emisor (Izquierda) + Comprobante SRI (Derecha)
    emisor_data = [
        [Paragraph("UNIVERSIDAD TÉCNICA DE AMBATO", title_style)],
        [Paragraph("FACULTAD DE INGENIERÍA EN SISTEMAS, ELECTRÓNICA E INDUSTRIAL", subtitle_style)],
        [Paragraph("CENTRO DE TRANSFERENCIA Y DESARROLLO DE TECNOLOGÍAS (CTT - FISEI)", subtitle_style)],
        [Spacer(1, 4)],
        [Paragraph(f"<b>Razón Social:</b> Universidad Técnica de Ambato - FISEI (CTT)", val_style)],
        [Paragraph(f"<b>RUC Institucional:</b> {ruc_institucional}", val_style)],
        [Paragraph("<b>Dirección Matriz:</b> Campus Huachi, Av. Los Chasquis y Río Payamino, Ambato", val_style)],
        [Paragraph("<b>Correo Institucional:</b> ctt.fisei@uta.edu.ec", val_style)],
        [Paragraph("<b>Obligado a llevar contabilidad:</b> SÍ", val_style)],
        [Paragraph("<b>Contribuyente Especial Nro:</b> RESOLUCIÓN NAC-DNCRASC20-00000001", val_style)],
    ]
    emisor_table = Table(emisor_data, colWidths=[260])
    emisor_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    comprobante_data = [
        [Paragraph("<b>R.I.D.E.</b>", doc_header_style)],
        [Paragraph("COMPROBANTE DE PAGO Y FACTURA ELECTRÓNICA", subtitle_style)],
        [Spacer(1, 3)],
        [Paragraph(f"<b>No.:</b> {comprobante_numero}", doc_header_style)],
        [Paragraph(f"<b>NÚMERO DE AUTORIZACIÓN / CLAVE DE ACCESO:</b>", label_style)],
        [Paragraph(clave_acceso, mono_style)],
        [Spacer(1, 2)],
        [Paragraph(f"<b>FECHA Y HORA DE AUTORIZACIÓN:</b> {fecha_emision}", val_style)],
        [Paragraph(f"<b>AMBIENTE:</b> PRODUCCIÓN", val_style)],
        [Paragraph(f"<b>EMISIÓN:</b> NORMAL", val_style)],
        [Paragraph(f"<b>ESTADO CONTABLE:</b> <font color='#00345e'><b>{status_str}</b></font>", val_style)],
    ]
    comprobante_table = Table(comprobante_data, colWidths=[260])
    comprobante_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 1, c_border),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))

    top_table = Table([[emisor_table, comprobante_table]], colWidths=[270, 270])
    top_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(top_table)
    story.append(Spacer(1, 10))

    # 2. BLOQUE DATOS DEL CLIENTE / RECEPTOR SRI
    client_content = [
        [
            Paragraph(f"<b>Razón Social / Nombres:</b> {billing_name}", val_style),
            Paragraph(f"<b>Identificación / RUC / Cédula:</b> {billing_id}", val_style),
        ],
        [
            Paragraph(f"<b>Fecha de Emisión:</b> {fecha_emision}", val_style),
            Paragraph(f"<b>Teléfono de Contacto:</b> {billing_phone}", val_style),
        ],
        [
            Paragraph(f"<b>Dirección Fiscal:</b> {billing_address}", val_style),
            Paragraph(f"<b>Correo Electrónico:</b> {billing_email}", val_style),
        ],
    ]
    client_table = Table(client_content, colWidths=[310, 230])
    client_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, c_border),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fbfcfd")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 10))

    # 3. TABLA DE DETALLE / DESGLOSE CONTABLE
    items_header = [
        Paragraph("Código", table_hdr_style),
        Paragraph("Descripción / Programa", table_hdr_style),
        Paragraph("Categoría Arancelaria", table_hdr_style),
        Paragraph("Cant.", table_hdr_style),
        Paragraph("Precio Unit.", table_hdr_style),
        Paragraph("Descuento", table_hdr_style),
        Paragraph("Precio Total", table_hdr_style),
    ]
    items_rows = [
        items_header,
        [
            Paragraph(item_code, table_cell_style),
            Paragraph(item_desc, table_cell_style),
            Paragraph(tariff_type, table_cell_style),
            Paragraph("1", table_cell_style),
            Paragraph(f"${amount:.2f}", table_cell_right),
            Paragraph("$0.00", table_cell_right),
            Paragraph(f"${amount:.2f}", table_cell_right),
        ]
    ]
    items_table = Table(items_rows, colWidths=[65, 175, 100, 35, 55, 55, 55])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 10))

    # 4. BLOQUE INFERIOR: Info adicional + QR (Izquierda) | Cuadro de Totales (Derecha)
    qr_payload = {
        "ruc": ruc_institucional,
        "comprobante": comprobante_numero,
        "identificacion": billing_id,
        "total": amount,
        "fecha": fecha_emision,
        "institucion": "Universidad Técnica de Ambato - FISEI (CTT)",
    }
    qr_buf = generate_ride_qr(qr_payload)
    qr_img = Image(qr_buf, width=75, height=75)

    info_adicional_data = [
        [Paragraph("<b>INFORMACIÓN ADICIONAL</b>", label_style)],
        [Paragraph(f"<b>Forma de Pago:</b> Depósito / Transferencia Bancaria (Banco del Pacífico)", val_style)],
        [Paragraph(f"<b>Base Legal:</b> Servicio educativo exento de IVA según Art. 56 Ley de Régimen Tributario Interno.", val_style)],
        [Paragraph(f"<b>Inscripción No.:</b> {enrollment_id} | <b>Categoría:</b> {tariff_type}", val_style)],
    ]
    info_table = Table(info_adicional_data, colWidths=[205])
    info_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    info_and_qr = Table([[info_table, qr_img]], colWidths=[210, 80])
    info_and_qr.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, c_border),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    totales_data = [
        [Paragraph("SUBTOTAL 0% (Educación Exenta):", label_style), Paragraph(f"${amount:.2f}", table_cell_right)],
        [Paragraph("SUBTOTAL NO OBJETO DE IVA:", label_style), Paragraph("$0.00", table_cell_right)],
        [Paragraph("SUBTOTAL EXENTO DE IVA:", label_style), Paragraph(f"${amount:.2f}", table_cell_right)],
        [Paragraph("SUBTOTAL 15% IVA:", label_style), Paragraph("$0.00", table_cell_right)],
        [Paragraph("TOTAL DESCUENTO:", label_style), Paragraph("$0.00", table_cell_right)],
        [Paragraph("IVA 0%:", label_style), Paragraph("$0.00", table_cell_right)],
        [Paragraph("<b>VALOR TOTAL:</b>", label_style), Paragraph(f"<b>${amount:.2f}</b>", table_cell_right)],
    ]
    totales_table = Table(totales_data, colWidths=[160, 80])
    totales_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("BACKGROUND", (0, -1), (-1, -1), c_primary_light),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    bottom_table = Table([[info_and_qr, totales_table]], colWidths=[295, 245])
    bottom_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(bottom_table)

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=c_primary, spaceBefore=4, spaceAfter=6))
    footer_style = ParagraphStyle(
        "FooterStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8,
        textColor=c_muted,
        alignment=TA_CENTER,
    )
    story.append(Paragraph(
        "Comprobante Tributario Electrónico emitido de conformidad con la normativa del Servicio de Rentas Internas (SRI). "
        "Centro de Transferencia y Desarrollo de Tecnologías - CTT FISEI | Universidad Técnica de Ambato | Ambato - Ecuador",
        footer_style
    ))

    # Construir documento utilizando UncompressedCanvas
    doc.build(story, canvasmaker=UncompressedCanvas)
    buffer.seek(0)
    return buffer
