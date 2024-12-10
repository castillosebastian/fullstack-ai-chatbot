# Chat Application

## Descripción
Aplicación de chat en tiempo real construida con FastAPI (backend) y Streamlit (frontend). Utiliza Redis para el manejo de mensajes asíncronos a través de workers.

## Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Redis Server

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd <nombre-del-proyecto>
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En Linux/Mac
source venv/bin/activate
```

3. Instalar dependencias:
```bash
# Dependencias del servidor
cd server
pip install -r requirements.txt

# Dependencias del frontend
cd ../frontend
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
# En server/.env
REDIS_HOST=localhost
REDIS_PORT=6379
SERVER_HOST=localhost
SERVER_PORT=8000

# En frontend/.env
SERVER_URL=http://localhost:8501
```

## Ejecución

1. Iniciar Redis Server:
```bash
# En Windows (si está instalado como servicio)
net start redis

# En Linux/Mac
redis-server
```

2. Iniciar el servidor (desde la carpeta server):
```bash
cd server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Iniciar el worker (desde la carpeta server):
```bash
cd server
python worker.py
```

4. Iniciar el frontend (desde la carpeta frontend):
```bash
cd frontend
streamlit run chat_ui.py
```

## Acceso a la Aplicación

- Frontend (Streamlit): http://localhost:8501
- API Backend: http://localhost:8000
- Documentación API (Swagger): http://localhost:8000/docs

## Estructura del Proyecto
```
.
├── frontend/
│   ├── chat_ui.py
│   └── requirements.txt
└── server/
    ├── src/
    │   ├── routes/
    │   ├── redis/
    │   └── socket/
    ├── main.py
    ├── worker.py
    └── requirements.txt
```

## Desarrollo

Para desarrollo local, asegúrate de:

1. Tener Redis corriendo localmente
2. El servidor FastAPI debe estar ejecutándose
3. Al menos un worker debe estar activo para procesar mensajes
4. La interfaz de Streamlit debe estar corriendo

## Solución de Problemas

Si encuentras problemas al ejecutar la aplicación:

1. Verifica que Redis esté corriendo:
```bash
redis-cli ping
```
Deberías recibir "PONG" como respuesta

2. Asegúrate que todos los servicios estén corriendo en los puertos correctos
3. Revisa los logs del servidor y worker para identificar posibles errores
4. Verifica que las variables de entorno estén configuradas correctamente

