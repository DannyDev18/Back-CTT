import json
from typing import List, Dict

class GeneralSerializer:
    """Maneja la serialización/deserialización de datos JSON"""
    
    @staticmethod
    def serialize_json_field(data: List | Dict | None) -> str:
        """Convierte una lista o dict a JSON string"""
        return json.dumps(data) if data else json.dumps([])
    
    @staticmethod
    def deserialize_json_field(data: str | None) -> List | Dict:
        """Convierte un JSON string a lista o dict"""
        if not data:
            return []
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return []