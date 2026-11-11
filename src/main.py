"""Punto de entrada de la aplicación: capa de exposición (API REST) de la tienda online"""

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from schemas import (
    PedidoCreate,
    PedidoRead,
    ProductoCreate,
    ProductoRead,
    UsuarioCreate,
    UsuarioRead,
)
from Services.Tienda_service import (
    ConflictoError,
    NoEncontradoError,
    TiendaError,
    TiendaService,
)

app = FastAPI(
    title="Tienda online",
    description="API REST de la tienda online construida sobre TiendaService.",
    version="1.0.0",
)

# Única instancia del servicio: guarda en memoria usuarios, productos y pedidos
tienda = TiendaService()

# Datos de ejemplo
tienda.registrar_usuario("cliente", "Iago Novo", "iagon@email.com", "Calle Gregorio Hernandez, A Coruña")
tienda.registrar_usuario("cliente", "Eladio Dapena", "eladio.dap@email.com", "Avenida Finisterre, A Coruña")
tienda.registrar_usuario("administrador", "Antón González", "admin@tienda.com")

def get_tienda() -> TiendaService:
    return tienda


#Estado del servicio (lo usa el HEALTHCHECK del contenedor Docker)
@app.get("/health", tags=["Sistema"], summary="Comprobar que la API está viva")
def health():
    return {"status": "ok"}


#Control de errores
# Los errores de negocio del servicio se traducen a códigos HTTP con un formato
# único: {"detail": "mensaje"} (el mismo que usa FastAPI en sus errores 404/422).
@app.exception_handler(NoEncontradoError)
async def no_encontrado_handler(request: Request, exc: NoEncontradoError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(ConflictoError)
async def conflicto_handler(request: Request, exc: ConflictoError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.exception_handler(TiendaError)
async def tienda_error_handler(request: Request, exc: TiendaError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


#Usuarios
@app.post("/usuarios", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED,
          tags=["Usuarios"], summary="Crear un usuario")
def crear_usuario(datos: UsuarioCreate, servicio: TiendaService = Depends(get_tienda)):
    usuario = servicio.registrar_usuario(
        datos.tipo, datos.nombre, str(datos.email), datos.direccion
    )
    return UsuarioRead.desde_dominio(usuario)


@app.get("/usuarios", response_model=list[UsuarioRead],
         tags=["Usuarios"], summary="Listar usuarios")
def listar_usuarios(servicio: TiendaService = Depends(get_tienda)):
    return [UsuarioRead.desde_dominio(u) for u in servicio.ver_usuarios()]


@app.get("/usuarios/{usuario_id}", response_model=UsuarioRead,
         tags=["Usuarios"], summary="Obtener un usuario")
def obtener_usuario(usuario_id: str, servicio: TiendaService = Depends(get_tienda)):
    return UsuarioRead.desde_dominio(servicio.obtener_usuario(usuario_id))


#Productos
@app.post("/productos", response_model=ProductoRead, response_model_exclude_none=True,
          status_code=status.HTTP_201_CREATED, tags=["Productos"],
          summary="Crear un producto (genérico, electrónico o ropa)")
def crear_producto(datos: ProductoCreate, servicio: TiendaService = Depends(get_tienda)):
    producto = servicio.crear_producto(
        datos.tipo, datos.nombre, datos.precio, datos.stock,
        meses_garantia=datos.meses_garantia, talla=datos.talla, color=datos.color,
    )
    return ProductoRead.desde_dominio(producto)


@app.get("/productos", response_model=list[ProductoRead], response_model_exclude_none=True,
         tags=["Productos"], summary="Listar productos")
def listar_productos(servicio: TiendaService = Depends(get_tienda)):
    return [ProductoRead.desde_dominio(p) for p in servicio.ver_productos()]


@app.get("/productos/{producto_id}", response_model=ProductoRead,
         response_model_exclude_none=True, tags=["Productos"], summary="Obtener un producto")
def obtener_producto(producto_id: str, servicio: TiendaService = Depends(get_tienda)):
    return ProductoRead.desde_dominio(servicio.obtener_producto(producto_id))


@app.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT,
            tags=["Productos"], summary="Eliminar un producto")
def eliminar_producto(producto_id: str, servicio: TiendaService = Depends(get_tienda)):
    if not servicio.borrar_producto(producto_id):
        raise NoEncontradoError(f"El producto con id '{producto_id}' no existe.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


#Pedidos
@app.post("/pedidos", response_model=PedidoRead, status_code=status.HTTP_201_CREATED,
          tags=["Pedidos"], summary="Crear un pedido")
def crear_pedido(datos: PedidoCreate, servicio: TiendaService = Depends(get_tienda)):
    # El servicio comprueba que el cliente y los productos existen y que hay stock
    pedido = servicio.realizar_pedido(
        datos.cliente_id,
        [(item.producto_id, item.cantidad) for item in datos.items],
    )
    return PedidoRead.desde_dominio(pedido)


@app.get("/usuarios/{cliente_id}/pedidos", response_model=list[PedidoRead],
         tags=["Pedidos"], summary="Historial de pedidos de un cliente")
def listar_pedidos_cliente(cliente_id: str, servicio: TiendaService = Depends(get_tienda)):
    return [PedidoRead.desde_dominio(p) for p in servicio.ver_pedidos_usuario(cliente_id)]


#Como ejecutarlo
#cd "C:\Users\anton\Desktop\UIE\3º Curso Semestre 1\Arquitectura del software\Prácticas Arquitectura del software\Practica evaluada 2\Tienda_online"
#pip install -r requirements.txt
#uvicorn main:app --reload

#Para probarlo
# [direccion que me haya dado la terminal] y añadirle el /docs
# Ahora mismo me quedaria así (http://127.0.0.1:8000/docs)
# Y probarlo en el navegador en visual studio no me funciona, pero en el navegador si

#Para acabar de ejecutarlo
#Ctrl + C en la terminal para parar el servidor
#Cerrar la pestaña del navegador