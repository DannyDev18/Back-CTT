"""
Servicio transaccional de notificaciones por correo electrónico institucional CTT-FISEI UTA.
Implementa plantillas HTML responsive y envío asíncrono seguro con fallback de desarrollo.
"""
import os
import smtplib
import logging
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Union, Any

logger = logging.getLogger("email_service")

# Constantes institucionales UTA
UTA_BLUE = "#00345e"
UTA_BLUE_LIGHT = "#e8f0fe"
UTA_TEXT_DARK = "#1e293b"
UTA_TEXT_MUTED = "#64748b"


def _get_smtp_config():
    """Obtiene la configuración SMTP del entorno."""
    return {
        "host": os.getenv("SMTP_HOST"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER"),
        "password": os.getenv("SMTP_PASSWORD"),
        "from_email": os.getenv("SMTP_FROM", "ctt.fisei@uta.edu.ec"),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes"),
        "use_ssl": os.getenv("SMTP_USE_SSL", "false").lower() in ("true", "1", "yes"),
    }


def _send_smtp_email_sync(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
    """
    Envía un correo mediante SMTP de forma síncrona.
    Si SMTP_HOST no está configurado o el envío falla, aplica fallback de desarrollo
    registrando el evento en logs sin lanzar excepciones.
    """
    config = _get_smtp_config()
    host = config["host"]

    # Modo fallback seguro de desarrollo
    if not host:
        logger.info(
            f"[EMAIL DEV FALLBACK] A: {to_email} | Asunto: '{subject}' | Host SMTP no configurado; notificación simulada con éxito."
        )
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"CTT FISEI - Universidad Técnica de Ambato <{config['from_email']}>"
        msg["To"] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
        else:
            msg.attach(MIMEText("Por favor visualice este correo con un cliente que soporte HTML.", "plain", "utf-8"))

        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if config["use_ssl"]:
            server = smtplib.SMTP_SSL(host, config["port"], timeout=10)
        else:
            server = smtplib.SMTP(host, config["port"], timeout=10)
            if config["use_tls"]:
                server.starttls()

        if config["user"] and config["password"]:
            server.login(config["user"], config["password"])

        server.send_message(msg)
        server.quit()
        logger.info(f"[EMAIL ENVIADO] A: {to_email} | Asunto: '{subject}'")
        return True
    except Exception as exc:
        logger.warning(
            f"[EMAIL ERROR FALLBACK] No se pudo enviar el correo a {to_email} ({subject}): {exc}. Continuando sin interrumpir la operación."
        )
        return False


def send_email_async(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None):
    """Lanza el envío de correo en un hilo en segundo plano para no bloquear el API."""
    thread = threading.Thread(
        target=_send_smtp_email_sync,
        args=(to_email, subject, html_body, text_body),
        daemon=True,
    )
    thread.start()


def _build_html_template(title: str, preheader: str, content_html: str, action_button: Optional[dict] = None) -> str:
    """Construye una plantilla HTML responsive compatible con clientes móviles de correo."""
    button_html = ""
    if action_button and action_button.get("url") and action_button.get("label"):
        button_html = f"""
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="margin: 24px 0;">
            <tr>
                <td align="center" style="border-radius: 8px; background: {UTA_BLUE};">
                    <a href="{action_button['url']}" target="_blank" style="display: inline-block; padding: 14px 28px; font-family: Helvetica, Arial, sans-serif; font-size: 15px; font-weight: bold; color: #ffffff; text-decoration: none; border-radius: 8px;">
                        {action_button['label']}
                    </a>
                </td>
            </tr>
        </table>
        """

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: {UTA_TEXT_DARK}; }}
        table {{ border-collapse: collapse; }}
        @media only screen and (max-width: 600px) {{
            .main-card {{ width: 100% !important; border-radius: 0 !important; }}
            .content-padding {{ padding: 20px !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 24px 0; background-color: #f1f5f9;">
    <div style="display: none; max-height: 0px; overflow: hidden;">{preheader}</div>
    <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
        <tr>
            <td align="center">
                <table role="presentation" class="main-card" width="580" border="0" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
                    <!-- Header Institucional -->
                    <tr>
                        <td style="background-color: {UTA_BLUE}; padding: 28px 32px; text-align: left;">
                            <div style="color: #ffffff; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase;">UNIVERSIDAD TÉCNICA DE AMBATO</div>
                            <div style="color: #93c5fd; font-size: 13px; font-weight: 500; margin-top: 4px;">Facultad de Ingeniería en Sistemas, Electrónica e Industrial</div>
                            <div style="color: #ffffff; font-size: 19px; font-weight: 700; margin-top: 12px;">{title}</div>
                        </td>
                    </tr>
                    <!-- Contenido Principal -->
                    <tr>
                        <td class="content-padding" style="padding: 32px; color: {UTA_TEXT_DARK}; font-size: 14px; line-height: 1.6;">
                            {content_html}
                            {button_html}
                        </td>
                    </tr>
                    <!-- Footer Institucional -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 32px; font-size: 11px; color: {UTA_TEXT_MUTED}; text-align: center;">
                            <div><b>Centro de Transferencia y Desarrollo de Tecnologías (CTT - FISEI)</b></div>
                            <div>Campus Huachi, Av. Los Chasquis y Río Payamino | Ambato, Ecuador</div>
                            <div style="margin-top: 6px;">Este es un mensaje institucional automático. Para consultas, contacte a ctt.fisei@uta.edu.ec</div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


# ==============================================================================
# NOTIFICACIONES TRANSACCIONALES DE NEGOCIO
# ==============================================================================

def send_order_created_notification(enrollment: Any, user: Any, congress: Optional[Any] = None, course: Optional[Any] = None) -> bool:
    """1. Orden Generada: Envía detalles de orden de pago e instrucciones de cuenta bancaria UTA."""
    to_email = getattr(user, "email", None) or getattr(user, "billing_email", None)
    if not to_email:
        return False

    student_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'first_last_name', '')}".strip() or "Estimado/a Participante"
    amount = float(getattr(enrollment, "amount", 0.0) or 0.0)
    program_name = getattr(congress, "nombre", None) or getattr(course, "name", None) or "Programa Académico FISEI"
    enr_id = getattr(enrollment, "id", "")

    content = f"""
    <p>Hola <b>{student_name}</b>,</p>
    <p>Se ha generado exitosamente tu orden de pago para <b>{program_name}</b>.</p>
    
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin: 20px 0;">
        <h4 style="margin: 0 0 10px 0; color: {UTA_BLUE}; font-size: 15px;">Detalles de la Orden #{enr_id}</h4>
        <p style="margin: 4px 0;"><b>Programa:</b> {program_name}</p>
        <p style="margin: 4px 0;"><b>Categoría:</b> {getattr(enrollment, 'tariff_type', 'General')}</p>
        <p style="margin: 4px 0;"><b>Valor a Pagar:</b> <span style="font-size: 16px; color: {UTA_BLUE}; font-weight: bold;">${amount:.2f} USD</span></p>
    </div>

    <h4 style="color: {UTA_TEXT_DARK}; margin: 20px 0 8px 0;">Instrucciones para Transferencia o Depósito:</h4>
    <ul style="padding-left: 20px; margin: 8px 0; color: {UTA_TEXT_MUTED};">
        <li><b>Institución Financiera:</b> Banco del Pacífico</li>
        <li><b>Tipo de Cuenta:</b> Cuenta Corriente</li>
        <li><b>Número de Cuenta:</b> 07310034</li>
        <li><b>Beneficiario:</b> Universidad Técnica de Ambato - FISEI (CTT)</li>
        <li><b>RUC:</b> 1860000880001</li>
    </ul>

    <p style="margin-top: 18px;">Una vez realizado el depósito o transferencia, ingresa a tu perfil en la plataforma para subir el comprobante.</p>
    """

    action = {
        "url": "https://fisei.uta.edu.ec/dashboard/ordenes",
        "label": "Subir Comprobante de Pago",
    }

    html = _build_html_template(
        title="Orden de Pago Generada",
        preheader=f"Detalles de pago para {program_name} - CTT FISEI",
        content_html=content,
        action_button=action,
    )
    send_email_async(to_email, f"Orden de Pago Generada #{enr_id} - CTT FISEI UTA", html)
    return True


def send_payment_approved_notification(enrollment: Any, user: Any, congress: Optional[Any] = None, course: Optional[Any] = None) -> bool:
    """2. Pago Aprobado: Confirma el pago y habilita el pase digital QR."""
    to_email = getattr(user, "email", None) or getattr(user, "billing_email", None)
    if not to_email:
        return False

    student_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'first_last_name', '')}".strip() or "Estimado/a Participante"
    program_name = getattr(congress, "nombre", None) or getattr(course, "name", None) or "Congreso / Evento FISEI"
    enr_id = getattr(enrollment, "id", "")

    content = f"""
    <p>Hola <b>{student_name}</b>,</p>
    <p>Nos complace informarte que tu pago para <b>{program_name}</b> ha sido <b>aprobado y verificado</b> por el equipo contable del CTT FISEI.</p>
    
    <div style="background-color: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 18px; margin: 20px 0;">
        <h4 style="margin: 0 0 6px 0; color: #065f46; font-size: 15px;">✓ Inscripción Confirmada</h4>
        <p style="margin: 4px 0; color: #047857;">Tu cupo oficial se encuentra garantizado. Tu pase digital QR para el registro de asistencia en puerta ya está disponible en tu panel personal.</p>
    </div>

    <p><b>Información de Asistencia:</b></p>
    <ul style="padding-left: 20px; color: {UTA_TEXT_MUTED};">
        <li>Presenta tu código QR en tu smartphone al ingresar a cada una de las sesiones magistrales.</li>
        <li>Puedes descargar tu comprobante oficial RIDE en PDF directamente desde la plataforma.</li>
    </ul>
    """

    action = {
        "url": "https://fisei.uta.edu.ec/dashboard/inscritos",
        "label": "Ver Pase Digital QR y RIDE PDF",
    }

    html = _build_html_template(
        title="¡Pago Confirmado y Pase Digital Listo!",
        preheader=f"Tu participación en {program_name} está confirmada",
        content_html=content,
        action_button=action,
    )
    send_email_async(to_email, f"Pago Aprobado y Pase Digital Confirmado - CTT FISEI UTA", html)
    return True


def send_receipt_rejected_notification(enrollment: Any, user: Any, congress: Optional[Any] = None, reason: str = "Comprobante no legible o datos inconsistentes", course: Optional[Any] = None) -> bool:
    """3. Comprobante Observado / Rechazado: Notifica observaciones para re-subida."""
    to_email = getattr(user, "email", None) or getattr(user, "billing_email", None)
    if not to_email:
        return False

    student_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'first_last_name', '')}".strip() or "Estimado/a Participante"
    program_name = getattr(congress, "nombre", None) or getattr(course, "name", None) or "Programa Académico FISEI"

    content = f"""
    <p>Hola <b>{student_name}</b>,</p>
    <p>El comprobante de pago subido para <b>{program_name}</b> fue revisado por el departamento financiero y presenta una observación que requiere tu atención:</p>
    
    <div style="background-color: #fff1f2; border: 1px solid #fecdd3; border-radius: 8px; padding: 18px; margin: 20px 0;">
        <h4 style="margin: 0 0 6px 0; color: #9f1239; font-size: 15px;">Motivo de la Observación:</h4>
        <p style="margin: 4px 0; color: #be123c; font-weight: 500;">{reason}</p>
    </div>

    <p>Por favor ingresa a la plataforma, revisa que el comprobante sea completamente legible y que el número de transacción coincida con el monto facturado, y sube un nuevo archivo.</p>
    """

    action = {
        "url": "https://fisei.uta.edu.ec/dashboard/ordenes",
        "label": "Corregir y Subir Nuevo Comprobante",
    }

    html = _build_html_template(
        title="Comprobante de Pago Observado",
        preheader=f"Acción requerida para tu inscripción en {program_name}",
        content_html=content,
        action_button=action,
    )
    send_email_async(to_email, f"Observación en Comprobante de Pago - CTT FISEI UTA", html)
    return True


def send_reminder_24h_notification(enrollment: Any, user: Any, congress: Optional[Any] = None, course: Optional[Any] = None) -> bool:
    """4. Recordatorio 24 Horas: Instrucciones de ingreso y cronograma del evento."""
    to_email = getattr(user, "email", None) or getattr(user, "billing_email", None)
    if not to_email:
        return False

    student_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'first_last_name', '')}".strip() or "Estimado/a Participante"
    program_name = getattr(congress, "nombre", None) or getattr(course, "name", None) or "Congreso FISEI"
    venue = getattr(congress, "lugar_sede", None) or "Auditorio Central FISEI, Campus Huachi"

    content = f"""
    <p>Hola <b>{student_name}</b>,</p>
    <p>Te recordamos que en <b>24 horas</b> dará inicio <b>{program_name}</b>.</p>
    
    <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 18px; margin: 20px 0;">
        <h4 style="margin: 0 0 8px 0; color: {UTA_BLUE}; font-size: 15px;">Información de Ingreso</h4>
        <p style="margin: 4px 0;"><b>Sede:</b> {venue}</p>
        <p style="margin: 4px 0;"><b>Apertura de Puertas y Registro:</b> 08:00 AM</p>
        <p style="margin: 4px 0;"><b>Requisito de Entrada:</b> Cédula de identidad física y Pase Digital con código QR en tu smartphone.</p>
    </div>

    <p>Te recomendamos llegar con 15 minutos de anticipación para evitar filas en el registro biométrico / escáner de entrada.</p>
    """

    action = {
        "url": "https://fisei.uta.edu.ec/dashboard/inscritos",
        "label": "Ver Pase QR y Cronograma",
    }

    html = _build_html_template(
        title="Recordatorio: Tu Evento Inicia en 24 Horas",
        preheader=f"Todo listo para {program_name} en FISEI",
        content_html=content,
        action_button=action,
    )
    send_email_async(to_email, f"Recordatorio 24h: {program_name} - FISEI UTA", html)
    return True
