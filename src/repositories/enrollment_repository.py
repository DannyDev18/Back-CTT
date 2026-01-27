from sqlmodel import Session, select
from typing import List, Optional
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func
from src.models.category import Category
from src.models.enrollment import Enrollment, EnrollmentStatus
from src.models.user_platform import UserPlatform
from src.models.course import Course

class EnrollmentRepository:
    """Maneja las operaciones de base de datos para inscripciones"""
    
    @staticmethod
    def get_enrollment_by_id(enrollment_id: int, db: Session) -> Optional[Enrollment]:
        """Obtiene una inscripción por ID"""
        statement = select(Enrollment).where(Enrollment.id == enrollment_id)
        return db.exec(statement).first()
    
    @staticmethod
    def get_enrollment_with_details(enrollment_id: int, db: Session):
        """Obtiene una inscripción con detalles del usuario y curso"""
        statement = (
            select(
                Enrollment,
                UserPlatform.first_name,
                UserPlatform.first_last_name,
                UserPlatform.email,
                Course.title,
                Course.category_id,
                Category.id,
                Category.name
            )
            .join(UserPlatform, Enrollment.id_user_platform == UserPlatform.id)
            .join(Course, Enrollment.id_course == Course.id)
            .join(Course, Category.id == Course.category_id)
            .where(Enrollment.id == enrollment_id)
        )
        return db.exec(statement).first()
    
    @staticmethod
    def check_existing_enrollment(
        user_id: int,
        course_id: int,
        db: Session
    ) -> Optional[Enrollment]:
        """Verifica si ya existe una inscripción activa"""
        statement = select(Enrollment).where(
            and_(
                Enrollment.id_user_platform == user_id,
                Enrollment.id_course == course_id,
                Enrollment.status != EnrollmentStatus.ANULADO
            )
        )
        return db.exec(statement).first()
    
    @staticmethod
    def get_enrollments_by_user(
        user_id: int,
        db: Session,
        status: Optional[EnrollmentStatus] = None
    ) -> List[Enrollment]:
        """Obtiene todas las inscripciones de un usuario"""
        conditions = [Enrollment.id_user_platform == user_id]
        
        if status:
            conditions.append(Enrollment.status == status)
        
        statement = select(Enrollment).where(and_(*conditions)).order_by(Enrollment.enrollment_date.desc())
        return list(db.exec(statement).all())
    
    @staticmethod
    def get_enrollments_by_course(
        course_id: int,
        db: Session,
        status: Optional[EnrollmentStatus] = None
    ) -> List[Enrollment]:
        """Obtiene todas las inscripciones de un curso"""
        conditions = [Enrollment.id_course == course_id]
        
        if status:
            conditions.append(Enrollment.status == status)
        
        statement = select(Enrollment).where(and_(*conditions)).order_by(Enrollment.enrollment_date.desc())
        return list(db.exec(statement).all())
    
    @staticmethod
    def get_enrollments_with_details_by_user(user_id: int, db: Session):
        """Obtiene inscripciones de un usuario con detalles del curso"""
        statement = (
            select(
                Enrollment,
                Course.title,
                Course.category_id,
                Category.name,
                Category.description,
                Category.svgurl,
                Course.course_image
            )
            .join(Course, Enrollment.id_course == Course.id)
            .join(Category, Course.category_id == Category.id)
            .where(Enrollment.id_user_platform == user_id)
            .order_by(Enrollment.enrollment_date.desc())
        )
        return db.exec(statement).all()
    
    @staticmethod
    def get_enrollments_with_details_by_course_paginated(
        db: Session,
        course_id: int,
        page: int,
        page_size: int,
        status: Optional[EnrollmentStatus] = None,
        search_term: Optional[str] = None
    ):
        """Obtiene inscripciones de un curso con detalles del usuario, paginadas"""
        # Filtros
        conditions = []
        conditions.append(Enrollment.id_course == course_id)
        if status:
            conditions.append(Enrollment.status == status)
        if search_term:
            search = f"%{search_term}%"
            # Filtro de búsqueda en nombre, apellido o email
            conditions.append(or_(
                UserPlatform.first_name.ilike(search),
                UserPlatform.first_last_name.ilike(search),
                UserPlatform.email.ilike(search),
                UserPlatform.cellphone.ilike(search)
            ))
        # Query base
        base_statement = (
            select(
            Enrollment,
            UserPlatform.first_name,
            UserPlatform.first_last_name,
            UserPlatform.email,
            UserPlatform.cellphone)
            .join(UserPlatform, Enrollment.id_user_platform == UserPlatform.id)
            .where(and_(*conditions)))
        # Contar total
        count_statement = (
            select(func.count())
            .select_from(Enrollment))
        # condiciones para el conteo
        if conditions:
            count_statement = count_statement.where(and_(*conditions))
        total = db.exec(count_statement).one()
        # Query paginada
        offset = (page - 1) * page_size
        statement = base_statement.offset(offset).limit(page_size).order_by(Enrollment.enrollment_date.desc())
        enrollments= db.exec(statement).all()

        # Retornar resultados y total
        return enrollments, total
    
    @staticmethod
    def get_enrollments_paginated(
        db: Session,
        page: int,
        page_size: int,
        status: Optional[EnrollmentStatus] = None,
        user_id: Optional[int] = None,
        course_id: Optional[int] = None
    ):
        """Obtiene inscripciones paginadas con filtros opcionales"""
        conditions = []
        
        if status:
            conditions.append(Enrollment.status == status)
        if user_id:
            conditions.append(Enrollment.id_user_platform == user_id)
        if course_id:
            conditions.append(Enrollment.id_course == course_id)
        
        # Query base
        base_statement = select(Enrollment)
        if conditions:
            base_statement = base_statement.where(and_(*conditions))
        
        # Contar total
        count_statement = select(func.count()).select_from(Enrollment)
        if conditions:
            count_statement = count_statement.where(and_(*conditions))
        total = db.exec(count_statement).one()
        
        # Query paginada
        offset = (page - 1) * page_size
        statement = base_statement.offset(offset).limit(page_size).order_by(Enrollment.enrollment_date.desc())
        enrollments = db.exec(statement).all()
        
        return enrollments, total
    
    @staticmethod
    def count_enrollments_by_course_and_status(
        course_id: int,
        status: EnrollmentStatus,
        db: Session
    ) -> int:
        """Cuenta inscripciones de un curso por estado"""
        statement = select(func.count()).select_from(Enrollment).where(
            and_(
                Enrollment.id_course == course_id,
                Enrollment.status == status
            )
        )
        return db.exec(statement).one()
    
    @staticmethod
    def get_all_enrollments(db: Session) -> List[Enrollment]:
        """Obtiene todas las inscripciones"""
        statement = select(Enrollment).order_by(Enrollment.enrollment_date.desc())
        return list(db.exec(statement).all())
