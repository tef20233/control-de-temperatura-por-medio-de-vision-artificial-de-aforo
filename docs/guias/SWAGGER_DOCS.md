# 📚 Documentación API con Swagger

## 🎯 Acceder a la Documentación Swagger

Una vez que el backend esté ejecutándose, puedes acceder a la documentación interactiva de Swagger en:

```
http://localhost:5000/api/docs
```

O desde cualquier dispositivo en tu red local:

```
http://192.168.1.19:5000/api/docs
```

## ✨ Características

### 1. **Interfaz Interactiva**
- Visualiza todos los endpoints disponibles
- Prueba las peticiones directamente desde el navegador
- Ve los schemas de request/response
- Ejemplos de uso para cada endpoint

### 2. **Endpoints Documentados**

#### 🏠 Sistema
- `GET /` - Información general de la API
- `GET /api/status` - Estado actual del sistema

#### 📹 Cámara
- `POST /api/camera/start` - Iniciar procesamiento
- `POST /api/camera/stop` - Detener procesamiento
- `POST /api/camera/test` - Probar conexión a cámara
- `POST /api/camera/scan` - Escanear red en busca de cámaras
- `POST /api/camera/change` - Cambiar fuente de cámara
- `GET /api/camera/stats` - Estadísticas de cámara

#### ⚙️ Configuración
- `GET /api/config` - Obtener configuración actual
- `POST /api/config` - Actualizar configuración

#### 🤖 Modelos
- `GET /api/models` - Información de modelos YOLO cargados

#### 📊 Métricas
- `GET /api/history` - Historial de ocupación y estadísticas

## 🚀 Ejemplo de Uso

### 1. Verificar Estado del Sistema

```bash
curl -X GET "http://localhost:5000/api/status"
```

Respuesta:
```json
{
  "running": false,
  "camera_active": false,
  "current_count": 0,
  "occupancy_rate": 0.0,
  "fps": 0.0,
  "max_capacity": 50,
  "models_loaded": ["yolov8n", "yolov8s", "yolov8m"],
  "connected_clients": 0
}
```

### 2. Iniciar Cámara

```bash
curl -X POST "http://localhost:5000/api/camera/start"
```

### 3. Actualizar Configuración

```bash
curl -X POST "http://localhost:5000/api/config" \
  -H "Content-Type: application/json" \
  -d '{
    "max_capacity": 100,
    "confidence_threshold": 0.4,
    "ensemble_strategy": "best"
  }'
```

### 4. Probar Conexión a Cámara

```bash
curl -X POST "http://localhost:5000/api/camera/test" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_url": "http://192.168.1.100:5000",
    "timeout": 5
  }'
```

### 5. Escanear Red

```bash
curl -X POST "http://localhost:5000/api/camera/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "ips": ["192.168.1.100", "192.168.196.100"],
    "port": 5000,
    "timeout": 3
  }'
```

## 📝 Schemas de Datos

### Config Object
```json
{
  "max_capacity": 50,
  "ensemble_strategy": "best",
  "confidence_threshold": 0.3,
  "enable_privacy": false,
  "camera_source": 0,
  "camera_type": "webcam"
}
```

### Status Object
```json
{
  "running": true,
  "camera_active": true,
  "current_count": 15,
  "occupancy_rate": 0.3,
  "fps": 28.5,
  "max_capacity": 50,
  "models_loaded": ["yolov8n", "yolov8s", "yolov8m"],
  "connected_clients": 2
}
```

## 🔧 Configuración de Swagger

La configuración de Swagger se encuentra en `app.py`:

```python
swagger_config = {
    "specs_route": "/api/docs"  # Ruta de la documentación
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Sistema de Control de Aforo - API",
        "version": "1.0.0"
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http"]
}
```

## 🎨 Personalización

Para personalizar la documentación de un endpoint, edita el docstring del método:

```python
@app.route('/api/ejemplo', methods=['POST'])
def ejemplo():
    """
    Descripción del endpoint
    ---
    tags:
      - Categoría
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            campo:
              type: string
    responses:
      200:
        description: Respuesta exitosa
    """
    return jsonify({"mensaje": "ok"})
```

## 📖 Recursos Adicionales

- [Documentación de Flasgger](https://github.com/flasgger/flasgger)
- [Especificación Swagger/OpenAPI](https://swagger.io/specification/)
- [Editor Swagger Online](https://editor.swagger.io/)

## 🐛 Solución de Problemas

### Swagger no carga
- Verifica que `flasgger` esté instalado: `pip list | grep flasgger`
- Revisa los logs del backend por errores de importación

### Los endpoints no aparecen
- Asegúrate de que los docstrings tengan el formato correcto
- Verifica que uses el separador `---` en el docstring

### Errores de CORS
- CORS ya está configurado en el backend para aceptar todas las solicitudes
- Si tienes problemas, verifica la configuración de `flask-cors`
