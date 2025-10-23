from typing import List, Optional, Dict, Any
from src.models.course import (
    CourseStatus,
)

class PaginationHelper:
    """Maneja la lógica de paginación"""
    
    @staticmethod
    def build_pagination_response(
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        base_path: str,
        status: CourseStatus,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Construye la respuesta de paginación"""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1 and total_pages > 0
        
        status_str = status.value if isinstance(status, CourseStatus) else str(status)
        category_param = f"&category={category}" if category else ""
        
        links = {
            "self": f"{base_path}?page={page}&page_size={page_size}&status={status_str}{category_param}",
            "next": f"{base_path}?page={page + 1}&page_size={page_size}&status={status_str}{category_param}" if has_next else None,
            "prev": f"{base_path}?page={page - 1}&page_size={page_size}&status={status_str}{category_param}" if has_prev else None,
        }
        
        return {
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "page_size": page_size,
            "has_next": has_next,
            "has_prev": has_prev,
            "links": links,
            "courses": items,
        }
