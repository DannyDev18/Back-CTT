from typing import Dict, Any
from src.models.user_platform import UserPlatform


class UserPlatformSerializer:
    """Maneja la serialización de usuarios de la plataforma"""
    
    @staticmethod
    def user_to_dict(user: UserPlatform, include_password: bool = False) -> Dict[str, Any]:
        """Convierte un usuario a diccionario"""
        user_dict = {
            "id": user.id,
            "identification": user.identification,
            "first_name": user.first_name,
            "second_name": user.second_name,
            "first_last_name": user.first_last_name,
            "second_last_name": user.second_last_name,
            "cellphone": user.cellphone,
            "email": user.email,
            "address": user.address,
            "type": user.type
        }
        
        if include_password:
            user_dict["password"] = user.password
        
        return user_dict
