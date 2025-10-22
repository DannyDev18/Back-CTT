from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Annotated, Optional
from src.controllers.course_controller import CourseController
from src.dependencies.db_session import SessionDep
from src.models.course import (
    CourseBase, 
    CourseRequirementBase, 
    CourseContentBase,
    CourseUpdate,
    CourseRequirementUpdate,
    CourseContentUpdate, 
    CourseStatus
)
from src.utils.jwt_utils import decode_token
from src.models.user import User

courses_router = APIRouter(prefix="/api/v1/courses", tags=["courses"])

@courses_router.post("")
def create_course(
    current_user: Annotated[User, Depends(decode_token)],
    course_data: CourseBase,
    requirements_data: CourseRequirementBase,
    contents_data: List[CourseContentBase],
    db: SessionDep
):
    try:
        course = CourseController.create_course_with_requirements(
            course_data, requirements_data, contents_data, db
        )
        return {
            "message": "Course created successfully",
            "course_id": course.id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating course: {str(e)}")

@courses_router.patch("/{course_id}")
def update_course(
    current_user: Annotated[User, Depends(decode_token)],
    course_id: int,
    db: SessionDep,
    course_data: Optional[CourseUpdate] = None,
    requirements_data: Optional[CourseRequirementUpdate] = None,
    contents_data: Optional[List[CourseContentUpdate]] = None
):
    """
    Actualiza un curso existente. Puedes actualizar uno o varios campos.
    Los campos no proporcionados no se modificarán.
    
    - **course_id**: ID del curso a actualizar
    - **course_data**: Datos del curso a actualizar (opcionales)
    - **requirements_data**: Requisitos del curso a actualizar (opcionales)
    - **contents_data**: Contenidos del curso a actualizar (opcionales)
    """
    try:
        # Si no se proporciona ningún dato, crear objetos vacíos
        if course_data is None:
            course_data = CourseUpdate()
        if requirements_data is None:
            requirements_data = CourseRequirementUpdate()
        if contents_data is None:
            contents_data = []
        
        course = CourseController.update_course_with_requirements(
            course_id, course_data, requirements_data, contents_data, db
        )
        return {
            "message": "Course updated successfully",
            "course_id": course.id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating course: {str(e)}")

@courses_router.delete("/{course_id}")
def delete_course(
    current_user: Annotated[User, Depends(decode_token)],
    course_id: int,
    db: SessionDep
):
    try:
        CourseController.delete_course(course_id, db)
        return {"message": "Course deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting course: {str(e)}")
    
@courses_router.get("/hours-range")
def get_courses_by_hours_range(
    db: SessionDep,
    min_hours: int = Query(..., description="Mínimo de horas totales", ge=0),
    max_hours: int = Query(..., description="Máximo de horas totales", ge=0)
):
    """Obtiene cursos filtrados por un rango de horas totales (min_hours a max_hours)"""
    try:
        if min_hours > max_hours:
            raise HTTPException(status_code=400, detail="min_hours cannot be greater than max_hours")

        courses = CourseController.get_courses_by_hours_range(min_hours, max_hours, db)
        return {"courses": courses}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

@courses_router.get("/hours/{total_hours}")
def get_courses_by_total_hours(total_hours: int, db: SessionDep):
    """Obtiene cursos filtrados por el total de horas exacto"""
    try:
        courses = CourseController.get_courses_by_total_hours(total_hours, db)
        return {"courses": courses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

@courses_router.get("/category/{category}")
def get_courses_by_category(category: str, db: SessionDep):
    try:
        courses = CourseController.get_courses_by_category(category, db)
        return {"courses": courses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

@courses_router.get("/search")
def search_courses_by_title(
    db: SessionDep,
    title: str = Query(..., description="Término de búsqueda para el título del curso", min_length=1)
):
    """Busca cursos por título utilizando coincidencia parcial (case-insensitive)"""
    try:
        courses = CourseController.search_courses_by_title(title, db)
        return {"courses": courses, "count": len(courses)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching courses: {str(e)}")

@courses_router.get("")
def get_all_courses(
    db: SessionDep,
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    status: str = Query(CourseStatus.activo, description="Estado del curso (activo/inactivo)"),
    category: Optional[str] = Query(None, description="Categoría del curso (opcional)")
):
    """
    Obtiene todos los cursos con paginación.
    - **page**: número de página (por defecto 1)
    - **page_size**: cantidad de cursos por página (por defecto 10, máximo 100)
    - **status**: estado del curso (activo/inactivo)
    - **category**: categoría del curso (opcional)
    """
    try:
        result = CourseController.get_all_courses(
            db, page=page, page_size=page_size, status=status, category=category
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

@courses_router.get("/{course_id}")
def get_course_by_id(course_id: int, db: SessionDep):
    """
    Obtiene un curso por su ID.
    - **course_id**: ID del curso
    """
    try:
        course = CourseController.get_course_with_full_data(course_id, db)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching course: {str(e)}")
