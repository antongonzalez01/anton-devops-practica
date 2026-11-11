# Tienda online: práctica de DevOps

**Autor:** Antón González Formoso

## Descripción

API REST de una tienda online desarrollada en Python con **FastAPI** (Práctica 2). Permite:

- **Usuarios**: registrar clientes (con dirección postal) y administradores, listarlos y consultarlos.
- **Productos**: crear productos genéricos, electrónicos (con meses de garantía) o de ropa (con talla y color), listarlos, consultarlos y eliminarlos.
- **Pedidos**: un cliente realiza un pedido de varios productos. Se comprueba el stock, se descuenta y se calcula el total. Se puede consultar el historial de pedidos de cada cliente.

Los datos se guardan en memoria (no hay base de datos). Al arrancar se crean tres usuarios de ejemplo.

## Estructura

```
.
├── src/
│   ├── main.py                  # Capa de exposición: endpoints de la API (FastAPI)
│   ├── schemas.py               # Esquemas Pydantic de petición y respuesta
│   ├── Services/
│   │   └── Tienda_service.py    # Lógica de negocio (TiendaService) y errores propios
│   └── models/
│       ├── Usuario.py           # Usuario, Cliente, Administrador
│       ├── Producto.py          # Producto, ProductoElectronico, ProductoRopa
│       └── Pedido.py            # Pedido
├── .github/workflows/docker.yml # CI: build -> run -> test -> push
├── Dockerfile
├── .dockerignore
├── requirements.txt             # Dependencias con versiones fijadas
└── README.md
```

## Ejecución en local (sin Docker)

```bash
pip install -r requirements.txt
uvicorn main:app --app-dir src --reload
```

Abre http://127.0.0.1:8000/docs para probar la API desde Swagger UI.

## Docker

La imagen parte de `python:3.12-slim`. Primero instala las dependencias de `requirements.txt` (en una capa que se cachea) y después copia el código de `src/`. La aplicación se ejecuta con un usuario sin privilegios (`appuser`). El `.dockerignore` deja fuera `.git`, las cachés, los entornos virtuales y los ficheros `.env`.

### Construir la imagen

```bash
docker build -t tienda-online:1.0.0 .
docker tag tienda-online:1.0.0 tienda-online:latest
```

### Ejecutar el contenedor

```bash
# En primer plano (Ctrl + C para parar)
docker run --rm -p 8000:8000 tienda-online:1.0.0

# En segundo plano, con nombre
docker run -d --name tienda -p 8000:8000 tienda-online:1.0.0
docker logs -f tienda        # ver los logs
docker stop tienda && docker rm tienda

# En otro puerto, usando la variable de entorno PORT
docker run --rm -e PORT=9000 -p 9000:9000 tienda-online:1.0.0
```

### Variables de entorno

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `PORT`   | `8000`            | Puerto en el que escucha uvicorn dentro del contenedor |

La aplicación no necesita secretos. Si en el futuro los necesitara, se pasarían con `-e` o `--env-file .env`; el `.env` está en `.gitignore` y en `.dockerignore`, así que nunca se sube.

### Salida esperada y pruebas

Al arrancar, el contenedor muestra algo parecido a esto:

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Pasos de prueba:

1. **Documentación interactiva:** abre http://localhost:8000/docs.
2. **Estado:** `curl http://localhost:8000/health` → `{"status":"ok"}`
3. **Usuarios de ejemplo:** `curl http://localhost:8000/usuarios` → lista con 3 usuarios (2 clientes y el administrador `admin@tienda.com`).
4. **Crear un producto:**
   ```bash
   curl -X POST http://localhost:8000/productos \
     -H "Content-Type: application/json" \
     -d '{"tipo":"electronico","nombre":"Portátil","precio":649.99,"stock":10,"meses_garantia":24}'
   ```
   → `201 Created` con el producto y su `id`.
5. **Crear un pedido:** usa el `id` de un cliente (paso 3) y el del producto (paso 4):
   ```bash
   curl -X POST http://localhost:8000/pedidos \
     -H "Content-Type: application/json" \
     -d '{"cliente_id":"<id_cliente>","items":[{"producto_id":"<id_producto>","cantidad":2}]}'
   ```
   → `201 Created` con `"total": 1299.98`. Si pides más unidades de las que hay en stock, la respuesta es `409 Conflict`.
6. **Estado del contenedor:** `docker ps` debe mostrar `(healthy)` gracias al `HEALTHCHECK`.

### Publicar y descargar la imagen (registry)

**GitHub Container Registry (automático):** el workflow `.github/workflows/docker.yml` construye la imagen, la arranca y prueba los endpoints en cada Pull Request. Al fusionar en `main`, además la publica:

```bash
docker pull ghcr.io/antongonzalez01/anton-devops-practica:latest
docker run --rm -p 8000:8000 ghcr.io/antongonzalez01/anton-devops-practica:latest
```

**Docker Hub (manual):**

```bash
docker login
docker tag tienda-online:1.0.0 <usuario_dockerhub>/tienda-online:1.0.0
docker push <usuario_dockerhub>/tienda-online:1.0.0
docker pull <usuario_dockerhub>/tienda-online:1.0.0
```

## Flujo de trabajo con Git

- `main`: rama principal y estable.
- `feature/<nombre>`: una rama corta por cada funcionalidad (por ejemplo, `feature/docker`). Se integra en `main` mediante un Pull Request.
