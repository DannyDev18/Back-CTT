from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import StreamingResponse
from typing import List, Optional, Union
from src.models.user import User
from src.controllers.enrollment_controller import EnrollmentController
from src.dependencies.db_session import SessionDep
from src.models.enrollment import (
    Enrollment,
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
    EnrollmentStatus,
)
from src.utils.platform_jwt_utils import decode_platform_token
from src.models.user_platform import UserPlatform
from src.models.congress_model import Congress
from src.models.course import Course
from src.utils.jwt_utils import decode_token
from src.utils.ride_generator import generate_ride_pdf
from src.utils.uta_order_generator import generate_uta_payment_order_pdf
import os
import json
from src.utils.email_service import (
    send_order_created_notification,
    send_payment_approved_notification,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

enrollments_router = APIRouter(prefix="/api/v1/enrollments", tags=["enrollments"])

# ============= Dependencies de autenticación =============

async def get_current_platform_user(token: str = Depends(decode_platform_token)) -> UserPlatform:
    return token


async def get_current_admin_user(token: str = Depends(decode_token)) -> User:
    return token


security = HTTPBearer()


async def get_current_user_any_type(
    db: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> tuple[Union[User, UserPlatform], str]:
    """
    Autentica como admin (User) o usuario de plataforma (UserPlatform).
    Retorna (usuario, tipo) donde tipo es 'admin' o 'platform'.
    """
    token = credentials.credentials

    try:
        from jose import jwt
        from src.utils.jwt_utils import JWT_SECRET_KEY
        from src.controllers.user_controller import UserController

        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = data.get("email")
        if email:
            user = UserController.get_user_by_email(email, db)
            if user:
                return user, "admin"
    except Exception:
        pass

    try:
        from jose import jwt
        from src.utils.platform_jwt_utils import JWT_SECRET_KEY
        from src.controllers.user_platform_controller import UserPlatformController

        data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        email = data.get("email")
        if email:
            user = UserPlatformController.get_user_by_email(email, db)
            if user:
                return user, "platform"
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
    )


# ============= Endpoints =============

@enrollments_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Crear inscripción",
    description=(
        "Inscribe a un usuario en un **curso** o en un **congreso**. "
        "Se debe enviar exactamente uno de `id_course` o `id_congress`."
    ),
)
def create_enrollment(
    enrollment_data: EnrollmentCreate,
    db: SessionDep,
    current_user: UserPlatform = Depends(get_current_platform_user),
):
    if enrollment_data.id_user_platform != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para inscribir a otro usuario.",
        )
    try:
        return EnrollmentController.create_enrollment(enrollment_data, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la inscripción: {str(e)}",
        )


@enrollments_router.get(
    "/",
    summary="Listar inscripciones paginadas",
    description=(
        "Admins ven todas; usuarios de plataforma solo las propias. "
        "Filtros opcionales: estado, usuario, curso, congreso."
    ),
)
def list_enrollments(
    db: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    enrollment_status: Optional[EnrollmentStatus] = Query(None, description="Filtrar por estado"),
    filter_user_id: Optional[int] = Query(None, description="Filtrar por usuario (solo admin)"),
    course_id: Optional[int] = Query(None, description="Filtrar por curso"),
    congress_id: Optional[int] = Query(None, description="Filtrar por congreso"),
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    try:
        current_user, user_type = user_data
        actual_user_id = current_user.id if user_type == "platform" else filter_user_id
        return EnrollmentController.get_enrollments_paginated(
            db, page, page_size, enrollment_status, actual_user_id, course_id, congress_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inscripciones: {str(e)}",
        )


@enrollments_router.get(
    "/user/{user_id}",
    summary="Inscripciones de un usuario",
    description="Admin puede consultar cualquier usuario; usuario de plataforma solo las propias.",
)
def get_user_enrollments(
    user_id: int,
    db: SessionDep,
    enrollment_status: Optional[EnrollmentStatus] = Query(None),
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    current_user, user_type = user_data
    if user_type == "platform" and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver inscripciones de otro usuario.",
        )
    try:
        enrollments = EnrollmentController.get_enrollments_by_user(user_id, db, enrollment_status)
        return {"user_id": user_id, "total": len(enrollments), "enrollments": enrollments}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inscripciones del usuario: {str(e)}",
        )


# ---- Estadísticas ----

@enrollments_router.get(
    "/stats/course/{course_id}",
    summary="Estadísticas de inscripciones por curso (admin)",
)
def get_course_stats(
    course_id: int,
    db: SessionDep,
    current_user: User = Depends(get_current_admin_user),
):
    try:
        return EnrollmentController.get_course_enrollment_stats(course_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}",
        )


@enrollments_router.get(
    "/stats/congress/{congress_id}",
    summary="Estadísticas de inscripciones por congreso (admin)",
)
def get_congress_stats(
    congress_id: int,
    db: SessionDep,
    current_user: User = Depends(get_current_admin_user),
):
    try:
        return EnrollmentController.get_congress_enrollment_stats(congress_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}",
        )


# ---- Listados por recurso ----

@enrollments_router.get(
    "/course/{course_id}",
    summary="Inscripciones de un curso (admin)",
    description="Lista paginada de usuarios inscritos en un curso.",
)
def get_course_enrollments(
    course_id: int,
    db: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    enrollment_status: Optional[EnrollmentStatus] = Query(None),
    search_term: Optional[str] = Query(None),
    current_user: User = Depends(get_current_admin_user),
):
    try:
        return EnrollmentController.get_enrollments_by_course(
            course_id, db, page, page_size, enrollment_status, search_term
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inscripciones del curso: {str(e)}",
        )


@enrollments_router.get(
    "/congress/{congress_id}",
    summary="Inscripciones de un congreso (admin)",
    description="Lista paginada de usuarios inscritos en un congreso.",
)
def get_congress_enrollments(
    congress_id: int,
    db: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    enrollment_status: Optional[EnrollmentStatus] = Query(None),
    search_term: Optional[str] = Query(None),
    current_user: User = Depends(get_current_admin_user),
):
    try:
        return EnrollmentController.get_enrollments_by_congress(
            congress_id, db, page, page_size, enrollment_status, search_term
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener inscripciones del congreso: {str(e)}",
        )


# ---- CRUD individual ----

@enrollments_router.get(
    "/{enrollment_id}",
    summary="Obtener inscripción por ID",
    description="Admin puede ver cualquiera; usuario de plataforma solo las propias.",
)
def get_enrollment(
    enrollment_id: int,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    try:
        result = EnrollmentController.get_enrollment_by_id(enrollment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la inscripción: {str(e)}",
        )

    current_user, user_type = user_data
    if user_type == "platform" and result["id_user_platform"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta inscripción.",
        )
    return result


@enrollments_router.get(
    "/{enrollment_id}/ride/download",
    summary="Descargar Comprobante Oficial RIDE en PDF (SRI / UTA)",
    description=(
        "Genera y descarga en memoria el comprobante de pago oficial RIDE en formato PDF con "
        "RUC institucional 1860000880001, desglose tributario e IVA 0% (educación exenta). "
        "Requiere que la inscripción esté en estado PAGADO o FACTURADO."
    ),
)
def download_ride_pdf(
    enrollment_id: int,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    enrollment = db.get(Enrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inscripción con ID {enrollment_id} no encontrada.",
        )

    current_user, user_type = user_data
    if user_type == "platform" and enrollment.id_user_platform != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para descargar el comprobante de esta inscripción.",
        )

    # Validar estado: solo PAGADO o FACTURADO
    status_str = getattr(enrollment.status, "value", str(enrollment.status)).strip()
    valid_paid_statuses = {
        EnrollmentStatus.PAGADO,
        EnrollmentStatus.FACTURADO,
        EnrollmentStatus.PAGADO.value,
        EnrollmentStatus.FACTURADO.value,
        "Pagado",
        "Facturado",
        "PAGADO",
        "FACTURADO",
    }
    if enrollment.status not in valid_paid_statuses and status_str not in valid_paid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El comprobante RIDE solo está disponible para inscripciones en estado Pagado o Facturado (estado actual: {status_str}).",
        )

    user = db.get(UserPlatform, enrollment.id_user_platform)
    congress = db.get(Congress, enrollment.id_congress) if enrollment.id_congress else None
    course = db.get(Course, enrollment.id_course) if enrollment.id_course else None

    pdf_buffer = generate_ride_pdf(enrollment, user, congress=congress, db=db, course=course)
    pdf_buffer.seek(0)

    filename = f"RIDE_UTA_{enrollment_id:09d}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@enrollments_router.post(
    "/{enrollment_id}/uta/generate-order",
    summary="Generar Orden de Pago Institucional UTA (Conexión / Simulación API Dirección Financiera)",
    description=(
        "Simula la integración oficial con la API de Pagos y Dirección Financiera de la Universidad Técnica de Ambato. "
        "Asigna la tarifa correspondiente al rol del participante (Estudiante UTA, Docente/Graduado, Público General), "
        "actualiza el estado a ORDEN_GENERADA, genera el documento PDF oficial y lo almacena localmente en el servidor."
    ),
)
def generate_uta_payment_order(
    enrollment_id: int,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    enrollment = db.get(Enrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inscripción con ID {enrollment_id} no encontrada.",
        )

    current_user, user_type = user_data
    if user_type == "platform" and enrollment.id_user_platform != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para generar la orden de pago de esta inscripción.",
        )

    user = db.get(UserPlatform, enrollment.id_user_platform)
    congress = db.get(Congress, enrollment.id_congress) if enrollment.id_congress else None
    course = None
    if enrollment.id_course:
        from src.repositories.course_repository import CourseRepository
        course = CourseRepository.get_course_with_relations(enrollment.id_course, db)

    # Calcular tarifa si no estaba definida o era 0.0
    if not enrollment.amount or enrollment.amount == 0.0 or not enrollment.tariff_type or enrollment.tariff_type == "GENERAL":
        user_type_str = str(getattr(user, "type", "Estudiante")).replace("UserPlatformType.", "")
        if congress:
            if user_type_str.lower() in ["estudiante", "estudiante uta"]:
                enrollment.tariff_type = "Estudiante UTA"
                enrollment.amount = float(getattr(congress, "costo_estudiante_uta", 20.0) or 20.0)
            elif user_type_str.lower() in ["administrativo", "docente", "graduado"]:
                enrollment.tariff_type = "Graduado / Docente UTA"
                enrollment.amount = float(getattr(congress, "costo_profesional", 50.0) or 50.0)
            else:
                enrollment.tariff_type = "Público General"
                enrollment.amount = float(getattr(congress, "costo_ponente", 80.0) or 80.0)
        elif course:
            prices = []
            if getattr(course, "requirement", None) and getattr(course.requirement, "prices", None):
                raw_prices = course.requirement.prices
                if isinstance(raw_prices, str):
                    try:
                        prices = json.loads(raw_prices)
                    except Exception:
                        prices = []
                elif isinstance(raw_prices, list):
                    prices = raw_prices

            if user_type_str.lower() in ["estudiante", "estudiante uta"]:
                enrollment.tariff_type = "Estudiante UTA"
                match = next((p for p in prices if "estudiante" in str(p.get("category", "")).lower()), None)
                enrollment.amount = float(match["amount"]) if match else (float(prices[0]["amount"]) if prices else 40.0)
            elif user_type_str.lower() in ["administrativo", "docente", "graduado"]:
                enrollment.tariff_type = "Graduados y Docentes UTA"
                match = next((p for p in prices if any(k in str(p.get("category", "")).lower() for k in ["graduado", "docente", "administrativo"])), None)
                enrollment.amount = float(match["amount"]) if match else (float(prices[1]["amount"]) if len(prices) > 1 else 50.0)
            else:
                enrollment.tariff_type = "Público en general"
                match = next((p for p in prices if "general" in str(p.get("category", "")).lower()), None)
                enrollment.amount = float(match["amount"]) if match else (float(prices[-1]["amount"]) if prices else 60.0)

    # Actualizar estado a ORDEN_GENERADA y registrar la URL de descarga
    order_download_url = f"/api/v1/enrollments/{enrollment_id}/payment-order/download"
    enrollment.status = EnrollmentStatus.ORDEN_GENERADA
    enrollment.payment_order_url = order_download_url

    # Generar el PDF y guardarlo en el almacenamiento local del servidor
    pdf_buffer = generate_uta_payment_order_pdf(
        enrollment, user, congress=congress, course=course, db=db
    )
    storage_dir = "/app/static/orders"
    os.makedirs(storage_dir, exist_ok=True)
    pdf_filename = f"Orden_Pago_UTA_{enrollment_id:06d}.pdf"
    file_path = os.path.join(storage_dir, pdf_filename)
    try:
        with open(file_path, "wb") as f:
            f.write(pdf_buffer.getvalue())
    except Exception as e:
        print(f"Advertencia al almacenar PDF en disco: {e}")

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    # Disparar notificación por correo
    try:
        send_order_created_notification(enrollment, user, congress=congress, course=course)
    except Exception:
        pass

    return {
        "status": "success",
        "api_origin": "UTA-DIRECCION-FINANCIERA-API",
        "message": "Orden de pago institucional generada y registrada en el sistema financiero de la UTA.",
        "order_data": {
            "order_code": f"UTA-FISEI-2026-{enrollment_id:06d}",
            "enrollment_id": enrollment.id,
            "student_name": f"{getattr(user, 'first_name', '')} {getattr(user, 'first_last_name', '')}".strip(),
            "identification": getattr(user, "identification", ""),
            "amount": float(enrollment.amount or 0.0),
            "tariff_type": enrollment.tariff_type,
            "status": "Generada la orden",
            "pdf_order_url": order_download_url,
            "due_days": 5,
            "payment_methods": {
                "ventanilla": {
                    "name": "Dirección Financiera UTA · Ventanillas de Recaudación",
                    "location": "Campus Huachi · Edificio de Administración Central UTA",
                    "schedule": "Lunes a Viernes 08:00 - 16:30 ininterrumpido"
                },
                "transferencia": {
                    "bank": "Banco del Pacífico",
                    "account_type": "Cuenta Corriente",
                    "account_number": "07358245",
                    "beneficiary": "Universidad Técnica de Ambato",
                    "ruc": "1860000880001"
                }
            }
        }
    }


@enrollments_router.get(
    "/{enrollment_id}/payment-order/download",
    summary="Descargar Orden de Pago Oficial UTA en PDF",
    description="Descarga el PDF oficial de la Orden de Pago UTA para presentación en ventanillas o comprobación de transferencia.",
)
def download_payment_order_pdf(
    enrollment_id: int,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    enrollment = db.get(Enrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inscripción con ID {enrollment_id} no encontrada.",
        )

    current_user, user_type = user_data
    if user_type == "platform" and enrollment.id_user_platform != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para descargar la orden de pago de esta inscripción.",
        )

    user = db.get(UserPlatform, enrollment.id_user_platform)
    congress = db.get(Congress, enrollment.id_congress) if enrollment.id_congress else None
    course = None
    if enrollment.id_course:
        from src.repositories.course_repository import CourseRepository
        course = CourseRepository.get_course_with_relations(enrollment.id_course, db)

    # Verificar si ya existe en disco
    file_path = f"/app/static/orders/Orden_Pago_UTA_{enrollment_id:06d}.pdf"
    if os.path.exists(file_path):
        import io
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_buffer = io.BytesIO(pdf_bytes)
    else:
        pdf_buffer = generate_uta_payment_order_pdf(
            enrollment, user, congress=congress, course=course, db=db
        )

    pdf_buffer.seek(0)
    filename = f"Orden_Pago_UTA_{enrollment_id:06d}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )



@enrollments_router.put(
    "/{enrollment_id}",
    summary="Actualizar inscripción",
    description="Admin puede cambiar estado y URL de pago; usuario de plataforma solo URL de pago.",
)
def update_enrollment(
    enrollment_id: int,
    enrollment_data: EnrollmentUpdate,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    try:
        existing = EnrollmentController.get_enrollment_by_id(enrollment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la inscripción: {str(e)}",
        )

    current_user, user_type = user_data
    if user_type == "platform":
        if existing["id_user_platform"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar esta inscripción.",
            )
        if enrollment_data.status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los usuarios de plataforma no pueden cambiar el estado de la inscripción.",
            )

    try:
        return EnrollmentController.update_enrollment(enrollment_id, enrollment_data, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la inscripción: {str(e)}",
        )


@enrollments_router.delete(
    "/{enrollment_id}",
    summary="Anular inscripción (admin)",
    description="Soft delete — cambia el estado a ANULADO. Solo administradores.",
)
def delete_enrollment(
    enrollment_id: int,
    db: SessionDep,
    user_data: tuple[Union[User, UserPlatform], str] = Depends(get_current_user_any_type),
):
    try:
        existing = EnrollmentController.get_enrollment_by_id(enrollment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la inscripción: {str(e)}",
        )

    _, user_type = user_data
    if user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede anular inscripciones.",
        )

    try:
        return EnrollmentController.delete_enrollment(enrollment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al anular la inscripción: {str(e)}",
        )
