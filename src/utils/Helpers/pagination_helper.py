from typing import List, Optional, Dict, Any
from src.models.course import CourseStatus


class PaginationHelper:
    """Maneja la lógica de paginación"""
    
    @staticmethod
    def build_pagination_response(
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        base_path: str,
        items_key: str = "items",
        extra_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Construye la respuesta de paginación genérica
        
        Args:
            items: Lista de items a paginar
            total: Total de items
            page: Página actual
            page_size: Tamaño de página
            base_path: Path base para los links
            items_key: Nombre de la clave para los items en la respuesta (ej: 'courses', 'users')
            extra_params: Parámetros extra para los links (ej: {'status': 'ACTIVO', 'category': 'TI'})
        """
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1 and total_pages > 0
        
        # Construir parámetros extra
        extra_params_str = ""
        if extra_params:
            for key, value in extra_params.items():
                if value is not None:
                    extra_params_str += f"&{key}={value}"
        
        links = {
            "self": f"{base_path}?page={page}&page_size={page_size}{extra_params_str}",
            "next": f"{base_path}?page={page + 1}&page_size={page_size}{extra_params_str}" if has_next else None,
            "prev": f"{base_path}?page={page - 1}&page_size={page_size}{extra_params_str}" if has_prev else None,
        }
        
        return {
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "page_size": page_size,
            "has_next": has_next,
            "has_prev": has_prev,
            "links": links,
            items_key: items,
        }
    
    @staticmethod
    def create_pagination_metadata(
        total_items: int,
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """
        Crea metadata de paginación simple sin links
        
        Args:
            total_items: Total de items
            page: Página actual
            page_size: Tamaño de página
        """
        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1 and total_pages > 0
        
        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "has_next": has_next,
            "has_previous": has_previous
        }
    
    @staticmethod
    def build_courses_pagination_response(
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        base_path: str,
        status: CourseStatus,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Construye la respuesta de paginación específica para cursos (mantiene compatibilidad)"""
        status_str = status.value if isinstance(status, CourseStatus) else str(status)
        extra_params = {"status": status_str}
        if category:
            extra_params["category"] = category
        
        return PaginationHelper.build_pagination_response(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            base_path=base_path,
            items_key="courses",
            extra_params=extra_params
        )
