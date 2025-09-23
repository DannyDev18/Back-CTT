# BACK-CTT

Una aplicación de autenticación de usuarios construida con FastAPI, SQLModel y SQL Server.

## Descripción

Este proyecto implementa un sistema básico de autenticación de usuarios con registro, login y obtención de perfil. Utiliza JWT para la autenticación de tokens y hashing de contraseñas para seguridad.

## Tecnologías Utilizadas

- **FastAPI**: Framework web para APIs REST.
- **SQLModel**: ORM para SQLAlchemy con soporte para Pydantic.
- **SQL Server**: Base de datos relacional.
- **PyODBC**: Driver para conectar a SQL Server.
- **Python-JOSE**: Para codificar/decodificar JWT.
- **Passlib**: Para hashing de contraseñas con bcrypt.
- **Uvicorn**: Servidor ASGI para FastAPI.
- **Python-Dotenv**: Para cargar variables de entorno.

## Instalación

1. Clona el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd BACK-CTT
   ```

2. Crea un entorno virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # En Windows
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración

1. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
   ```
   SQL_SERVER=tu_servidor_sql
   SQL_PORT=1433
   SQL_DB=tu_base_de_datos
   SQL_USER=tu_usuario
   SQL_PASSWORD=tu_contraseña
   JWT_SECRET_KEY=tu_clave_secreta_para_jwt
   DEBUG=False
   ```

2. Asegúrate de tener SQL Server corriendo y accesible.

## Estructura del Proyecto

```
BACK-CTT/
├── requirements.txt
├── src/
│   ├── main.py                 # Aplicación principal FastAPI
│   ├── config/
│   │   └── db.py               # Configuración de la base de datos
│   ├── controllers/
│   │   └── user_controller.py  # Controlador para usuarios
│   ├── dependencies/
│   │   └── db_session.py       # Dependencia de sesión de DB
│   ├── models/
│   │   └── user.py             # Modelo de Usuario
│   ├── routes/
│   │   └── auth_router.py      # Endpoints de autenticación
│   └── utils/
│       └── seeds/
│           └── user_seed.py    # Seed de datos iniciales
└── README.md
```

## Uso

### Ejecutar la Aplicación

```bash
uvicorn src.main:app -p 8000 --reload
```

La aplicación estará disponible en `http://127.0.0.1:8000`.

### Documentación de la API

Visita `http://127.0.0.1:8000/docs` para la documentación interactiva de Swagger.

### Endpoints

#### Registro de Usuario
- **POST** `/auth/register`
- Descripción: Registra un nuevo usuario.
- Body: JSON con `name`, `last_name`, `email`, `password`.
- Respuesta: Mensaje de éxito o error.

#### Login
- **POST** `/auth/token`
- Descripción: Inicia sesión y obtiene un token JWT.
- Body: Form data con `username` (email) y `password`.
- Respuesta: `{"access_token": "token", "token_type": "bearer"}`

#### Perfil de Usuario
- **GET** `/auth/users/profile`
- Descripción: Obtiene el perfil del usuario autenticado.
- Headers: `Authorization: Bearer <token>`
- Respuesta: JSON con `id`, `name`, `last_name`, `email`.

### Seed de Datos

Al iniciar la aplicación, se ejecuta automáticamente un seed que crea un usuario de prueba:
- Email: `daniel.jerez@example.com`
- Password: `securepassword`

## Desarrollo

- Las tablas se crean automáticamente al iniciar la aplicación.
- Para debugging, establece `DEBUG=True` en el `.env`.
- Los endpoints están bajo el prefijo `/auth`.

## Contribución

1. Fork el proyecto.
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`).
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`).
4. Push a la rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request.

## Licencia

Este proyecto está bajo la Licencia MIT.