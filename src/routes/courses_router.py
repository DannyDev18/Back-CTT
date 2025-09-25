from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Annotated
from src.controllers.course_controller import CourseController
from src.dependencies.db_session import SessionDep
from src.models.course import CourseBase, CourseRequirementBase, CourseContentBase
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

@courses_router.get("/hours-range")
def get_courses_by_hours_range(
    db: SessionDep,
    min_hours: int = Query(..., description="Mínimo de horas totales", ge=1),
    max_hours: int = Query(..., description="Máximo de horas totales", ge=1)
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

@courses_router.get("")
def get_all_courses( db: SessionDep):
    try:
        courses = CourseController.get_all_courses(db)
        return {"courses": courses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

@courses_router.get("/{course_id}")
def get_course( course_id: int, db: SessionDep):
    try:
        course = CourseController.get_course_with_full_data(course_id, db)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching course: {str(e)}")
