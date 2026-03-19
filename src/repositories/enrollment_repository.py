from sqlmodel import Session, select
from typing import List, Optional
from sqlalchemy import and_, or_, func
from src.models.category import Category
from src.models.enrollment import Enrollment, EnrollmentStatus
from src.models.user_platform import UserPlatform
from src.models.course import Course
from src.models.congress import Congress


class EnrollmentRepository:
    """Maneja las operaciones de base de datos para inscripciones."""

    # ------------------------------------------------------------------
    # Lecturas simples
    # ------------------------------------------------------------------

    @staticmethod
    def get_enrollment_by_id(enrollment_id: int, db: Session) -> Optional[Enrollment]:
        """Obtiene una inscripción por ID."""
        return db.exec(select(Enrollment).where(Enrollment.id == enrollment_id)).first()

    @staticmethod
    def get_enrollment_with_details(enrollment_id: int, db: Session):
        """
        Obtiene una inscripción con datos del usuario y del recurso inscrito.

        Retorna tupla:
            (enrollment, first_name, first_last_name, email,
             course_title, course_category_id, congress_title)
        """
        statement = (
            select(
                Enrollment,
                UserPlatform.first_name,
                UserPlatform.first_last_name,
                UserPlatform.email,
                Course.title.label("course_title"),
                Course.category_id.label("course_category_id"),
                Congress.title.label("congress_title"),
            )
            .join(UserPlatform, Enrollment.id_user_platform == UserPlatform.id)
            .outerjoin(Course, Enrollment.id_course == Course.id)
            .outerjoin(Congress, Enrollment.id_congress == Congress.id)
            .where(Enrollment.id == enrollment_id)
        )
        return db.exec(statement).first()

    @staticmethod
    def get_all_enrollments(db: Session) -> List[Enrollment]:
        """Obtiene todas las inscripciones."""
        return list(
            db.exec(select(Enrollment).order_by(Enrollment.enrollment_date.desc())).all()
        )

    # ------------------------------------------------------------------
    # Verificación de duplicados
    # ------------------------------------------------------------------

    @staticmethod
    def check_existing_course_enrollment(
        user_id: int,
        course_id: int,
        db: Session,
    ) -> Optional[Enrollment]:
        """Devuelve la inscripción activa del usuario al curso, o None si no existe."""
        statement = select(Enrollment).where(
            and_(
                Enrollment.id_user_platform == user_id,
                Enrollment.id_course == course_id,
                Enrollment.status != EnrollmentStatus.ANULADO,
            )
        )
        return db.exec(statement).first()

    @staticmethod
    def check_existing_congress_enrollment(
        user_id: int,
        congress_id: int,
        db: Session,
    ) -> Optional[Enrollment]:
        """Devuelve la inscripción activa del usuario al congreso, o None si no existe."""
        statement = select(Enrollment).where(
            and_(
                Enrollment.id_user_platform == user_id,
                Enrollment.id_congress == congress_id,
                Enrollment.status != EnrollmentStatus.ANULADO,
            )
        )
        return db.exec(statement).first()

    # ------------------------------------------------------------------
    # Consultas por usuario
    # ------------------------------------------------------------------

    @staticmethod
    def get_enrollments_by_user(
        user_id: int,
        db: Session,
        status: Optional[EnrollmentStatus] = None,
    ) -> List[Enrollment]:
        """Obtiene todas las inscripciones de un usuario."""
        conditions = [Enrollment.id_user_platform == user_id]
        if status:
            conditions.append(Enrollment.status == status)
        statement = (
            select(Enrollment)
            .where(and_(*conditions))
            .order_by(Enrollment.enrollment_date.desc())
        )
        return list(db.exec(statement).all())

    @staticmethod
    def get_enrollments_with_details_by_user(user_id: int, db: Session):
        """
        Obtiene inscripciones de un usuario con detalles del curso o congreso.

        Retorna tuplas:
            (enrollment, course_title, course_category_id, category_name,
             category_description, category_svgurl, course_image, congress_title)

        Los campos de curso son None para inscripciones a congresos y viceversa.
        """
        statement = (
            select(
                Enrollment,
                Course.title.label("course_title"),
                Course.category_id.label("course_category_id"),
                Category.name.label("category_name"),
                Category.description.label("category_description"),
                Category.svgurl.label("category_svgurl"),
                Course.course_image.label("course_image"),
                Congress.title.label("congress_title"),
            )
            .outerjoin(Course, Enrollment.id_course == Course.id)
            .outerjoin(Category, Course.category_id == Category.id)
            .outerjoin(Congress, Enrollment.id_congress == Congress.id)
            .where(Enrollment.id_user_platform == user_id)
            .order_by(Enrollment.enrollment_date.desc())
        )
        return db.exec(statement).all()

    # ------------------------------------------------------------------
    # Consultas paginadas por curso
    # ------------------------------------------------------------------

    @staticmethod
    def get_enrollments_by_course(
        course_id: int,
        db: Session,
        status: Optional[EnrollmentStatus] = None,
    ) -> List[Enrollment]:
        """Obtiene todas las inscripciones de un curso."""
        conditions = [Enrollment.id_course == course_id]
        if status:
            conditions.append(Enrollment.status == status)
        statement = (
            select(Enrollment)
            .where(and_(*conditions))
            .order_by(Enrollment.enrollment_date.desc())
        )
        return list(db.exec(statement).all())

    @staticmethod
    def get_enrollments_with_details_by_course_paginated(
        db: Session,
        course_id: int,
        page: int,
        page_size: int,
        status: Optional[EnrollmentStatus] = None,
        search_term: Optional[str] = None,
    ):
        """
        Obtiene inscripciones de un curso con datos del usuario, paginadas.

        Retorna: (rows, total)
        Cada row: (enrollment, first_name, first_last_name, email, cellphone)
        """
        conditions = [Enrollment.id_course == course_id]
        if status:
            conditions.append(Enrollment.status == status)
        if search_term:
            search = f"%{search_term}%"
            conditions.append(
                or_(
                    UserPlatform.first_name.ilike(search),
                    UserPlatform.first_last_name.ilike(search),
                    UserPlatform.email.ilike(search),
                    UserPlatform.cellphone.ilike(search),
                )
            )

        base_q = (
            select(
                Enrollment,
                UserPlatform.first_name,
                UserPlatform.first_last_name,
                UserPlatform.email,
                UserPlatform.cellphone,
            )
            .join(UserPlatform, Enrollment.id_user_platform == UserPlatform.id)
            .where(and_(*conditions))
        )
        count_q = (
            select(func.count())
            .select_from(Enrollment)
            .join(UserPlatform, Enrollment.id_user_platform == UserPlatform.id)
            .where(and_(*conditions))
        )

        total = db.exec(count_q).one()
        offset = (page - 1) * page_size
        rows = db.exec(
            base_q.offset(offset).limit(page_size).order_by(Enrollment.enrollment_date.desc())
        ).all()
        return rows, total

    # ------------------------------------------------------------------
    # Consultas paginadas por congreso
    # ------------------------------------------------------------------

    @staticmethod
    def get_enrollments_with_details_by_congress_paginated(
        db: Session,
        congress_id: int,
        page: int,
        page_size: int,
        status: Optional[EnrollmentStatus] = None,
        search_term: Optional[str] = None,
    ):
        """
        Obtiene inscripciones de un congreso con datos del usuario, paginadas.

        Retorna: (rows, total)
        Cada row: (enrollment, first_name, first_last_name, email, cellphone)
        """
        conditions = [Enrollment.id_congress == congress_id]
        if status:
            conditions.append(Enrollment.status == status)
        if search_term:
            search = f"%{search_term}%"
            conditions.append(
                or_(
                    UserPlatform.first_name.ilike(search),
                    UserPlatform.first_last_name.ilike(search),
                    UserPlatform.email.ilike(search),
                    UserPlatform.cellphone.ilike(search),
                )
            )

        base_q = (
            select(
                Enrollment,
                UserPlatform.first_name,
                UserPlatform.first_last_name,
                UserPlatform.email,
                UserPlatform.cellphone,
            )
            .join(UserPlatform, Enrollment.id_user_platform == UserPlatform.id)
            .where(and_(*conditions))
        )
        count_q = (
            select(func.count())
            .select_from(Enrollment)
            .join(UserPlatform, Enrollment.id_user_platform == UserPlatform.id)
            .where(and_(*conditions))
        )

        total = db.exec(count_q).one()
        offset = (page - 1) * page_size
        rows = db.exec(
            base_q.offset(offset).limit(page_size).order_by(Enrollment.enrollment_date.desc())
        ).all()
        return rows, total

    # ------------------------------------------------------------------
    # Paginación general
    # ------------------------------------------------------------------

    @staticmethod
    def get_enrollments_paginated(
        db: Session,
        page: int,
        page_size: int,
        status: Optional[EnrollmentStatus] = None,
        user_id: Optional[int] = None,
        course_id: Optional[int] = None,
        congress_id: Optional[int] = None,
    ):
        """Obtiene inscripciones paginadas con filtros opcionales."""
        conditions = []
        if status:
            conditions.append(Enrollment.status == status)
        if user_id:
            conditions.append(Enrollment.id_user_platform == user_id)
        if course_id:
            conditions.append(Enrollment.id_course == course_id)
        if congress_id:
            conditions.append(Enrollment.id_congress == congress_id)

        base_q = select(Enrollment)
        count_q = select(func.count()).select_from(Enrollment)
        if conditions:
            base_q = base_q.where(and_(*conditions))
            count_q = count_q.where(and_(*conditions))

        total = db.exec(count_q).one()
        offset = (page - 1) * page_size
        enrollments = db.exec(
            base_q.offset(offset).limit(page_size).order_by(Enrollment.enrollment_date.desc())
        ).all()
        return enrollments, total

    # ------------------------------------------------------------------
    # Estadísticas
    # ------------------------------------------------------------------

    @staticmethod
    def count_enrollments_by_course_and_status(
        course_id: int,
        status: EnrollmentStatus,
        db: Session,
    ) -> int:
        """Cuenta inscripciones de un curso por estado."""
        statement = select(func.count()).select_from(Enrollment).where(
            and_(Enrollment.id_course == course_id, Enrollment.status == status)
        )
        return db.exec(statement).one()

    @staticmethod
    def count_enrollments_by_congress_and_status(
        congress_id: int,
        status: EnrollmentStatus,
        db: Session,
    ) -> int:
        """Cuenta inscripciones de un congreso por estado."""
        statement = select(func.count()).select_from(Enrollment).where(
            and_(Enrollment.id_congress == congress_id, Enrollment.status == status)
        )
        return db.exec(statement).one()
