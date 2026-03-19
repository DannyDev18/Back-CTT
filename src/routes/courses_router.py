from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Annotated, Optional
from pydantic import BaseModel, Field
from src.controllers.course_controller import CourseController
from src.dependencies.db_session import SessionDep
from src.models.course import (
    CourseCreate,
    CourseRequirementCreate,
    CourseContentCreate,
    CourseUpdate,
    CourseRequirementUpdate,
    CourseContentCreate as CourseContentUpdate,
    CourseStatus
)
from src.utils.jwt_utils import decode_token
from src.models.user import User
from src.utils.platform_jwt_utils import decode_platform_token
from src.models.user_platform import UserPlatform

courses_router = APIRouter(prefix="/api/v1/courses", tags=["courses"])


# ============= Modelos de Request ============= 

class CourseCreateRequest(BaseModel):
    """Modelo para crear un curso completo"""
    course: CourseCreate
    requirements: CourseRequirementCreate
    contents: List[CourseContentCreate] = Field(default_factory=list)


class CourseUpdateRequest(BaseModel):
    """Modelo para actualizar un curso completo"""
    course: Optional[CourseUpdate] = None
    requirements: Optional[CourseRequirementUpdate] = None
    contents: Optional[List[CourseContentUpdate]] = None


class CourseResponse(BaseModel):
    """Respuesta estándar para operaciones de cursos"""
    message: str
    course_id: Optional[int] = None
    data: Optional[dict] = None


# ============= Manejadores de Errores ============= 

def handle_controller_error(e: Exception, operation: str) -> HTTPException:
    """Maneja errores del controlador de forma consistente"""
    if isinstance(e, ValueError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error {operation}: {str(e)}"
    )


# ============= Rutas CRUD ============= 

@courses_router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo curso",
    description="Crea un curso completo con requisitos y contenidos"
)
def create_course(
    request: CourseCreateRequest,
    db: SessionDep,
    current_user: Annotated[User, Depends(decode_token)]
) -> CourseResponse:
    """
    Crea un nuevo curso con todos sus datos relacionados.
    
    - **course**: Información básica del curso
    - **requirements**: Requisitos y detalles del curso
    - **contents**: Lista de contenidos del curso
    """
    try:
        result = CourseController.create_course_with_requirements(
            request.course,
            request.requirements,
            request.contents,
            db,
            current_user.id
        )
        return CourseResponse(
            message="Course created successfully",
            course_id=result.get("id"),
            data=result
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "creating course")


@courses_router.get(
    "",
    summary="Listar todos los cursos",
    description="Obtiene una lista paginada de cursos con filtros opcionales"
)
def get_all_courses(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de cursos por página"),
    status_filter: CourseStatus = Query(CourseStatus.ACTIVO, alias="status", description="Estado del curso"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría")
):
    """
    Obtiene todos los cursos con paginación.
    
    **Parámetros de consulta:**
    - `page`: Número de página (mínimo 1)
    - `page_size`: Cursos por página (1-100)
    - `status`: Estado del curso (activo/inactivo)
    - `category`: Filtrar por categoría específica
    
    **Respuesta:**
    Incluye información de paginación y lista de cursos
    """
    try:
        return CourseController.get_all_courses(
            db,
            page=page,
            page_size=page_size,
            status=status_filter,
            category_id=category_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching courses")


@courses_router.get(
    "/search",
    summary="Buscar cursos por título",
    description="Busca cursos usando coincidencia parcial en el título (case-insensitive)"
)
def search_courses_by_title(
    db: SessionDep,
    q: str = Query(..., min_length=1, description="Término de búsqueda", alias="query"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de resultados")
):
    """
    Busca cursos por título.
    
    **Parámetros:**
    - `q`: Término de búsqueda (mínimo 1 carácter)
    - `page`: Número de página para resultados
    - `page_size`: Cantidad de resultados por página
    """
    try:
        courses = CourseController.search_courses_by_title(q, db)
        
        # Paginar resultados
        total = len(courses)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_courses = courses[start:end]
        
        return {
            "query": q,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "courses": paginated_courses
        }
    except Exception as e:
        raise handle_controller_error(e, "searching courses")


@courses_router.get(
    "/search/available",
    summary="Buscar cursos disponibles por título",
    description="Busca cursos por título excluyendo aquellos en los que el usuario ya está inscrito. Requiere autenticación de usuario de plataforma."
)
def search_available_courses(
    db: SessionDep,
    current_user: Annotated[UserPlatform, Depends(decode_platform_token)],
    q: str = Query(..., min_length=1, description="Término de búsqueda", alias="query"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de resultados"),
    status_filter: CourseStatus = Query(CourseStatus.ACTIVO, alias="status", description="Estado del curso")
):
    """
    Busca cursos disponibles por título (excluye cursos donde el usuario ya está inscrito).
    
    **Parámetros:**
    - `q`: Término de búsqueda (mínimo 1 carácter)
    - `page`: Número de página para resultados
    - `page_size`: Cantidad de resultados por página
    - `status`: Estado del curso (por defecto: ACTIVO)
    
    **Retorna:**
    - Lista de cursos que coinciden con la búsqueda y están disponibles para inscripción
    """
    try:
        courses = CourseController.search_available_courses_for_user(
            q, current_user.id, db, status_filter
        )
        
        # Paginar resultados
        total = len(courses)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_courses = courses[start:end]
        
        return {
            "query": q,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "courses": paginated_courses
        }
    except Exception as e:
        raise handle_controller_error(e, "searching available courses")


@courses_router.get(
    "/available",
    summary="Listar cursos disponibles para inscripción",
    description="Obtiene cursos en los que el usuario aún no está inscrito. Requiere autenticación de usuario de plataforma."
)
def get_available_courses(
    db: SessionDep,
    current_user: Annotated[UserPlatform, Depends(decode_platform_token)],
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de cursos por página"),
    status_filter: CourseStatus = Query(CourseStatus.ACTIVO, alias="status", description="Estado del curso"),
    category_id: Optional[int] = Query(None,alias="category_id", description="Filtrar por categoría")
):
    """
    Obtiene todos los cursos disponibles para que el usuario se inscriba.
    
    Excluye los cursos donde el usuario ya tiene una inscripción activa (no anulada).
    
    **Parámetros de consulta:**
    - `page`: Número de página (mínimo 1)
    - `page_size`: Cursos por página (1-100)
    - `status`: Estado del curso (activo/inactivo)
    - `category`: Filtrar por categoría específica
    
    **Respuesta:**
    Incluye información de paginación y lista de cursos disponibles
    """
    try:
        return CourseController.get_available_courses_for_user(
            db,
            user_id=current_user.id,
            category_id=category_id,
            page=page,
            page_size=page_size,
            status=status_filter
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching available courses")


@courses_router.get(
    "/hours",
    summary="Buscar cursos por rango de horas",
    description="Obtiene cursos cuyas horas totales estén dentro del rango especificado"
)
def get_courses_by_hours_range(
    db: SessionDep,
    min_hours: int = Query(0, ge=0, description="Horas mínimas"),
    max_hours: int = Query(1000, ge=0, description="Horas máximas")
):
    """
    Filtra cursos por rango de horas totales.
    
    **Parámetros:**
    - `min_hours`: Mínimo de horas (>=0)
    - `max_hours`: Máximo de horas (>=0)
    """
    if min_hours > max_hours:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_hours cannot be greater than max_hours"
        )
    
    try:
        courses = CourseController.get_courses_by_hours_range(min_hours, max_hours, db)
        return {
            "min_hours": min_hours,
            "max_hours": max_hours,
            "total": len(courses),
            "courses": courses
        }
    except Exception as e:
        raise handle_controller_error(e, "fetching courses by hours")


@courses_router.get(
    "/category/{category_id}",
    summary="Obtener cursos por categoría",
    description="Lista todos los cursos de una categoría específica"
)
def get_courses_by_category(
    category_id: int,
    db: SessionDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    Obtiene todos los cursos de una categoría.
    
    **Parámetros:**
    - `category`: Nombre de la categoría
    - `page`: Número de página
    - `page_size`: Cursos por página
    """
    try:
        courses = CourseController.get_courses_by_category(category_id, db)
        
        # Paginar resultados
        total = len(courses)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_courses = courses[start:end]
        
        return {
            "category_id": category_id,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "courses": paginated_courses
        }
    except Exception as e:
        raise handle_controller_error(e, "fetching courses by category")


@courses_router.get(
    "/{course_id}",
    summary="Obtener curso por ID",
    description="Obtiene los detalles completos de un curso específico"
)
def get_course_by_id(
    course_id: int,
    db: SessionDep
):
    """
    Obtiene un curso específico con todos sus datos relacionados.
    
    **Parámetros:**
    - `course_id`: ID único del curso
    
    **Respuesta:**
    Detalles completos del curso incluyendo requisitos y contenidos
    """
    try:
        course = CourseController.get_course_by_id(course_id, db)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with id {course_id} not found"
            )
        return course
    except HTTPException:
        raise
    except Exception as e:
        raise handle_controller_error(e, "fetching course")


@courses_router.patch(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Actualizar un curso",
    description="Actualiza parcialmente un curso existente. Solo se modifican los campos proporcionados."
)
def update_course(
    course_id: int,
    request: CourseUpdateRequest,
    db: SessionDep,
    current_user: Annotated[User, Depends(decode_token)]
) -> CourseResponse:
    """
    Actualiza un curso existente de forma parcial.
    
    **Parámetros:**
    - `course_id`: ID del curso a actualizar
    - `request`: Datos a actualizar (todos opcionales)
    
    **Nota:** Los campos no proporcionados permanecen sin cambios
    """
    try:
        result = CourseController.update_course_with_requirements(
            course_id,
            db,
            request.course,
            request.requirements,
            request.contents
        )
        return CourseResponse(
            message="Course updated successfully",
            course_id=course_id,
            data=result
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "updating course")


@courses_router.delete(
    "/{course_id}",
    status_code=status.HTTP_200_OK,
    response_model=CourseResponse,
    summary="Eliminar un curso",
    description="Realiza un soft delete marcando el curso como inactivo"
)
def delete_course(
    course_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(decode_token)]
) -> CourseResponse:
    """
    Elimina un curso (soft delete).
    
    **Parámetros:**
    - `course_id`: ID del curso a eliminar
    
    **Nota:** El curso se marca como inactivo, no se elimina físicamente
    """
    try:
        CourseController.delete_course(course_id, db)
        return CourseResponse(
            message="Course deleted successfully",
            course_id=course_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise handle_controller_error(e, "deleting course")
