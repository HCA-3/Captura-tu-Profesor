from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status, UploadFile, Form
from fastapi.param_functions import Depends
import modelos
from modelos import (
    Juego, JuegoCrear, JuegoBase,
    Consola, ConsolaCrear, ConsolaBase,
    Accesorio, AccesorioCrear, AccesorioBase,
    ConsolaConAccesorios, JuegoCompatibilidad, ImagenBase
)
from persistencia import (
    cargar_juegos, guardar_juegos,
    cargar_consolas, guardar_consolas,
    cargar_accesorios, guardar_accesorios
)
from utilidades import obtener_siguiente_id
import almacenamiento

# --- Inicialización de "Bases de Datos" en Memoria ---
try:
    _db_juegos: List[Dict[str, Any]] = cargar_juegos()
except HTTPException as e:
    print(f"Error crítico al cargar datos iniciales de juegos: {e.detail}. Iniciando con datos vacíos.")
    _db_juegos = []

try:
    _db_consolas: List[Dict[str, Any]] = cargar_consolas()
except HTTPException as e:
    print(f"Error crítico al cargar datos iniciales de consolas: {e.detail}. Iniciando con datos vacíos.")
    _db_consolas = []

try:
    _db_accesorios: List[Dict[str, Any]] = cargar_accesorios()
except HTTPException as e:
    print(f"Error crítico al cargar datos iniciales de accesorios: {e.detail}. Iniciando con datos vacíos.")
    _db_accesorios = []

# --- Operaciones CRUD para Juegos ---
def obtener_juego_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    """Busca un juego por ID (incluyendo borrados lógicamente)."""
    for juego in _db_juegos:
        if juego.get("id") == id_juego:
            return juego
    return None

def obtener_juego_activo_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    """Busca un juego activo por ID."""
    juego = obtener_juego_por_id(id_juego)
    if juego and not juego.get("esta_eliminado", False):
        return juego
    return None

def obtener_juegos(saltar: int = 0, limite: int = 100, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    """Obtiene una lista de juegos."""
    if incluir_eliminados:
        resultados = _db_juegos
    else:
        resultados = [j for j in _db_juegos if not j.get("esta_eliminado", False)]
    inicio = max(0, saltar)
    fin = inicio + max(0, limite)
    return resultados[inicio:fin]

async def crear_juego(datos_juego: JuegoCrear, imagen: Optional[UploadFile] = None) -> Dict[str, Any]:
    """Crea un nuevo juego."""
    nuevo_id = obtener_siguiente_id()
    
    # Validación de título duplicado
    titulo_nuevo = datos_juego.titulo.strip().lower()
    existente = next((j for j in _db_juegos if j.get("titulo", "").strip().lower() == titulo_nuevo and not j.get("esta_eliminado")), None)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un juego activo con el título '{datos_juego.titulo}'."
        )

    # Procesar imagen si existe
    imagen_data = None
    if imagen:
        try:
            imagen_data = await almacenamiento.guardar_imagen(imagen)
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error al guardar imagen para nuevo juego: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar la imagen del juego"
            )

    nuevo_juego_dict = Juego(
        id=nuevo_id,
        esta_eliminado=False,
        imagen=imagen_data,
        **datos_juego.model_dump(exclude_none=True)
    ).model_dump()

    _db_juegos.append(nuevo_juego_dict)
    guardar_juegos(_db_juegos)
    return nuevo_juego_dict

async def actualizar_juego(id_juego: int, datos_actualizacion: JuegoCrear, imagen: Optional[UploadFile] = None) -> Optional[Dict[str, Any]]:
    """Actualiza un juego existente."""
    juego = obtener_juego_por_id(id_juego)
    if juego is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Juego con ID {id_juego} no encontrado.")
    if juego.get("esta_eliminado", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El juego con ID {id_juego} está eliminado y no se puede modificar."
        )

    # Procesar imagen si se proporciona
    imagen_data = None
    if imagen:
        try:
            # Eliminar imagen anterior si existe
            if juego.get("imagen") and juego["imagen"].get("nombre_archivo"):
                almacenamiento.eliminar_imagen(juego["imagen"]["nombre_archivo"])
            
            imagen_data = await almacenamiento.guardar_imagen(imagen)
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error al actualizar imagen del juego {id_juego}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar la nueva imagen del juego"
            )

    # Validar título duplicado si se intenta cambiar
    if "titulo" in datos_actualizacion.model_dump(exclude_unset=True):
        titulo_nuevo = datos_actualizacion.titulo.strip().lower()
        titulo_actual = juego.get("titulo", "").strip().lower()
        if titulo_nuevo != titulo_actual:
            existente = next((j for j in _db_juegos if j.get("id") != id_juego and j.get("titulo", "").strip().lower() == titulo_nuevo and not j.get("esta_eliminado")), None)
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe otro juego activo con el título '{datos_actualizacion.titulo}'."
                )

    # Aplicar actualizaciones
    campos_actualizables = set(JuegoBase.model_fields.keys())
    for clave, valor in datos_actualizacion.model_dump(exclude_unset=True).items():
        if clave in campos_actualizables:
            juego[clave] = valor
    
    # Actualizar imagen si se proporcionó una nueva
    if imagen_data is not None:
        juego['imagen'] = imagen_data

    guardar_juegos(_db_juegos)
    return juego

def eliminar_logico_juego(id_juego: int) -> Optional[Dict[str, Any]]:
    """Marca un juego como eliminado (borrado lógico)."""
    juego = obtener_juego_por_id(id_juego)
    if juego is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Juego con ID {id_juego} no encontrado.")
    if juego.get("esta_eliminado"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Juego con ID {id_juego} ya está eliminado.")

    juego['esta_eliminado'] = True
    guardar_juegos(_db_juegos)
    return juego

def filtrar_juegos_por_genero(genero: str) -> List[Dict[str, Any]]:
    """Busca juegos activos por género."""
    consulta_genero = genero.strip().lower()
    if not consulta_genero:
        return []
    juegos_activos = obtener_juegos(limite=len(_db_juegos), incluir_eliminados=False)
    return [j for j in juegos_activos if consulta_genero in j.get("genero", "").lower()]

def buscar_juegos_por_desarrollador(nombre_dev: str) -> List[Dict[str, Any]]:
    """Busca juegos activos por nombre de desarrollador."""
    consulta_dev = nombre_dev.strip().lower()
    if not consulta_dev:
        return []
    juegos_activos = obtener_juegos(limite=len(_db_juegos), incluir_eliminados=False)
    return [j for j in juegos_activos if consulta_dev in j.get("nombre_desarrollador", "").lower()]

# --- Operaciones CRUD para Consolas ---
def obtener_consola_por_id(id_consola: int) -> Optional[Dict[str, Any]]:
    """Busca una consola por ID (incluyendo borradas lógicamente)."""
    for consola in _db_consolas:
        if consola.get("id") == id_consola:
            return consola
    return None

def obtener_consola_activa_por_id(id_consola: int) -> Optional[Dict[str, Any]]:
    """Busca una consola activa por ID."""
    consola = obtener_consola_por_id(id_consola)
    if consola and not consola.get("esta_eliminado", False):
        return consola
    return None

def obtener_consolas(saltar: int = 0, limite: int = 100, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    """Obtiene una lista de consolas."""
    if incluir_eliminados:
        resultados = _db_consolas
    else:
        resultados = [c for c in _db_consolas if not c.get("esta_eliminado", False)]
    inicio = max(0, saltar)
    fin = inicio + max(0, limite)
    return resultados[inicio:fin]

async def crear_consola(datos_consola: ConsolaCrear, imagen: Optional[UploadFile] = None) -> Dict[str, Any]:
    """Crea una nueva consola."""
    nuevo_id = obtener_siguiente_id()
    
    # Validación de nombre duplicado
    nombre_nuevo = datos_consola.nombre.strip().lower()
    existente = next((c for c in _db_consolas if c.get("nombre", "").strip().lower() == nombre_nuevo and not c.get("esta_eliminado")), None)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una consola activa con el nombre '{datos_consola.nombre}'."
        )

    # Procesar imagen si existe
    imagen_data = None
    if imagen:
        try:
            imagen_data = await almacenamiento.guardar_imagen(imagen)
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error al guardar imagen para nueva consola: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar la imagen de la consola"
            )

    nueva_consola_dict = Consola(
        id=nuevo_id,
        esta_eliminado=False,
        imagen=imagen_data,
        **datos_consola.model_dump(exclude_none=True)
    ).model_dump()

    _db_consolas.append(nueva_consola_dict)
    guardar_consolas(_db_consolas)
    return nueva_consola_dict

async def actualizar_consola(id_consola: int, datos_actualizacion: ConsolaCrear, imagen: Optional[UploadFile] = None) -> Optional[Dict[str, Any]]:
    """Actualiza una consola existente."""
    consola = obtener_consola_por_id(id_consola)
    if consola is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Consola con ID {id_consola} no encontrada.")
    if consola.get("esta_eliminado", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La consola con ID {id_consola} está eliminada y no se puede modificar."
        )

    # Procesar imagen si se proporciona
    imagen_data = None
    if imagen:
        try:
            # Eliminar imagen anterior si existe
            if consola.get("imagen") and consola["imagen"].get("nombre_archivo"):
                almacenamiento.eliminar_imagen(consola["imagen"]["nombre_archivo"])
            
            imagen_data = await almacenamiento.guardar_imagen(imagen)
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error al actualizar imagen de la consola {id_consola}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar la nueva imagen de la consola"
            )

    # Validar nombre duplicado si se intenta cambiar
    if "nombre" in datos_actualizacion.model_dump(exclude_unset=True):
        nombre_nuevo = datos_actualizacion.nombre.strip().lower()
        nombre_actual = consola.get("nombre", "").strip().lower()
        if nombre_nuevo != nombre_actual:
            existente = next((c for c in _db_consolas if c.get("id") != id_consola and c.get("nombre", "").strip().lower() == nombre_nuevo and not c.get("esta_eliminado")), None)
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe otra consola activa con el nombre '{datos_actualizacion.nombre}'."
                )

    # Aplicar actualizaciones
    campos_actualizables = set(ConsolaBase.model_fields.keys())
    for clave, valor in datos_actualizacion.model_dump(exclude_unset=True).items():
        if clave in campos_actualizables:
            consola[clave] = valor
    
    # Actualizar imagen si se proporcionó una nueva
    if imagen_data is not None:
        consola['imagen'] = imagen_data

    guardar_consolas(_db_consolas)
    return consola

def eliminar_logico_consola(id_consola: int) -> Optional[Dict[str, Any]]:
    """Marca una consola como eliminada (borrado lógico)."""
    consola = obtener_consola_por_id(id_consola)
    if consola is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Consola con ID {id_consola} no encontrada.")
    if consola.get("esta_eliminado"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Consola con ID {id_consola} ya está eliminada.")

    # Eliminar imagen asociada si existe
    if consola.get("imagen") and consola["imagen"].get("nombre_archivo"):
        try:
            almacenamiento.eliminar_imagen(consola["imagen"]["nombre_archivo"])
        except Exception as e:
            print(f"Error al eliminar imagen de la consola {id_consola}: {e}")

    consola['esta_eliminado'] = True
    
    # Marcar accesorios asociados como eliminados
    accesorios_afectados = obtener_accesorios_por_consola(id_consola, incluir_eliminados=False)
    for acc in accesorios_afectados:
        eliminar_logico_accesorio(acc['id'])
    
    guardar_consolas(_db_consolas)
    return consola

def buscar_consolas_por_fabricante(fabricante: str) -> List[Dict[str, Any]]:
    """Busca consolas activas por fabricante."""
    consulta = fabricante.strip().lower()
    if not consulta:
        return []
    consolas_activas = obtener_consolas(limite=len(_db_consolas), incluir_eliminados=False)
    return [c for c in consolas_activas if consulta in c.get("fabricante", "").lower()]

# --- Operaciones CRUD para Accesorios ---
def obtener_accesorio_por_id(id_accesorio: int) -> Optional[Dict[str, Any]]:
    """Busca un accesorio por ID (incluyendo borrados lógicamente)."""
    for acc in _db_accesorios:
        if acc.get("id") == id_accesorio:
            return acc
    return None

def obtener_accesorio_activo_por_id(id_accesorio: int) -> Optional[Dict[str, Any]]:
    """Busca un accesorio activo por ID."""
    acc = obtener_accesorio_por_id(id_accesorio)
    if acc and not acc.get("esta_eliminado", False):
        return acc
    return None

def obtener_accesorios(saltar: int = 0, limite: int = 100, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    """Obtiene una lista de accesorios."""
    if incluir_eliminados:
        resultados = _db_accesorios
    else:
        resultados = [a for a in _db_accesorios if not a.get("esta_eliminado", False)]
    inicio = max(0, saltar)
    fin = inicio + max(0, limite)
    return resultados[inicio:fin]

async def crear_accesorio(datos_accesorio: AccesorioCrear, imagen: Optional[UploadFile] = None) -> Dict[str, Any]:
    """Crea un nuevo accesorio."""
    # Validar que la consola asociada existe y está activa
    consola_asociada = obtener_consola_activa_por_id(datos_accesorio.id_consola)
    if consola_asociada is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se encontró una consola activa con ID {datos_accesorio.id_consola} para asociar el accesorio."
        )

    # Validación de nombre duplicado para la misma consola
    nombre_nuevo = datos_accesorio.nombre.strip().lower()
    existente = next((
        a for a in _db_accesorios
        if a.get("id_consola") == datos_accesorio.id_consola
        and a.get("nombre", "").strip().lower() == nombre_nuevo
        and not a.get("esta_eliminado")
    ), None)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un accesorio activo con el nombre '{datos_accesorio.nombre}' para la consola ID {datos_accesorio.id_consola}."
        )

    # Procesar imagen si existe
    imagen_data = None
    if imagen:
        try:
            imagen_data = await almacenamiento.guardar_imagen(imagen)
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error al guardar imagen para nuevo accesorio: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar la imagen del accesorio"
            )

    nuevo_id = obtener_siguiente_id()
    nuevo_accesorio_dict = Accesorio(
        id=nuevo_id,
        esta_eliminado=False,
        imagen=imagen_data,
        **datos_accesorio.model_dump(exclude_none=True)
    ).model_dump()

    _db_accesorios.append(nuevo_accesorio_dict)
    guardar_accesorios(_db_accesorios)
    return nuevo_accesorio_dict

async def actualizar_accesorio(id_accesorio: int, datos_actualizacion: AccesorioCrear, imagen: Optional[UploadFile] = None) -> Optional[Dict[str, Any]]:
    """Actualiza un accesorio existente."""
    accesorio = obtener_accesorio_por_id(id_accesorio)
    if accesorio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Accesorio con ID {id_accesorio} no encontrado.")
    if accesorio.get("esta_eliminado", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El accesorio con ID {id_accesorio} está eliminado y no se puede modificar."
        )

    # Procesar imagen si se proporciona
    imagen_data = None
    if imagen:
        try:
            # Eliminar imagen anterior si existe
            if accesorio.get("imagen") and accesorio["imagen"].get("nombre_archivo"):
                almacenamiento.eliminar_imagen(accesorio["imagen"]["nombre_archivo"])
            
            imagen_data = await almacenamiento.guardar_imagen(imagen)
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error al actualizar imagen del accesorio {id_accesorio}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar la nueva imagen del accesorio"
            )

    # Validar si se cambia id_consola: la nueva consola debe existir y estar activa
    if "id_consola" in datos_actualizacion.model_dump(exclude_unset=True) and datos_actualizacion.id_consola != accesorio.get("id_consola"):
        nueva_consola = obtener_consola_activa_por_id(datos_actualizacion.id_consola)
        if nueva_consola is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se encontró una consola activa con ID {datos_actualizacion.id_consola} para re-asociar el accesorio."
            )

    # Validar nombre duplicado si se cambia (dentro de la consola nueva o actual)
    consola_id_final = datos_actualizacion.id_consola if "id_consola" in datos_actualizacion.model_dump(exclude_unset=True) else accesorio.get("id_consola")
    if "nombre" in datos_actualizacion.model_dump(exclude_unset=True):
        nombre_nuevo = datos_actualizacion.nombre.strip().lower()
        nombre_actual = accesorio.get("nombre", "").strip().lower()

        if nombre_nuevo != nombre_actual or consola_id_final != accesorio.get("id_consola"):
            existente = next((
                a for a in _db_accesorios
                if a.get("id") != id_accesorio
                and a.get("id_consola") == consola_id_final
                and a.get("nombre", "").strip().lower() == nombre_nuevo
                and not a.get("esta_eliminado")
            ), None)
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe otro accesorio activo con el nombre '{datos_actualizacion.nombre}' para la consola ID {consola_id_final}."
                )

    # Aplicar actualizaciones
    campos_actualizables = set(AccesorioBase.model_fields.keys())
    for clave, valor in datos_actualizacion.model_dump(exclude_unset=True).items():
        if clave in campos_actualizables:
            accesorio[clave] = valor
    
    # Actualizar imagen si se proporcionó una nueva
    if imagen_data is not None:
        accesorio['imagen'] = imagen_data

    guardar_accesorios(_db_accesorios)
    return accesorio

def eliminar_logico_accesorio(id_accesorio: int) -> Optional[Dict[str, Any]]:
    """Marca un accesorio como eliminado (borrado lógico)."""
    accesorio = obtener_accesorio_por_id(id_accesorio)
    if accesorio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Accesorio con ID {id_accesorio} no encontrado.")
    if accesorio.get("esta_eliminado"):
        return accesorio

    # Eliminar imagen asociada si existe
    if accesorio.get("imagen") and accesorio["imagen"].get("nombre_archivo"):
        try:
            almacenamiento.eliminar_imagen(accesorio["imagen"]["nombre_archivo"])
        except Exception as e:
            print(f"Error al eliminar imagen del accesorio {id_accesorio}: {e}")

    accesorio['esta_eliminado'] = True
    guardar_accesorios(_db_accesorios)
    return accesorio

def obtener_accesorios_por_consola(id_consola: int, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    """Obtiene los accesorios asociados a una consola específica."""
    accesorios_consola = [
        acc for acc in _db_accesorios
        if acc.get("id_consola") == id_consola
    ]

    if not incluir_eliminados:
        accesorios_consola = [acc for acc in accesorios_consola if not acc.get("esta_eliminado", False)]

    return accesorios_consola

# --- Función de Compatibilidad Juego-Consola-Accesorio ---
def obtener_compatibilidad_juego(id_juego: int) -> Dict[str, Any]:
    """Obtiene los detalles de un juego, las consolas activas compatibles y sus accesorios."""
    juego = obtener_juego_activo_por_id(id_juego)
    if juego is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Juego con ID {id_juego} no encontrado o está inactivo."
        )

    plataformas_juego = [p.strip().lower() for p in juego.get("plataformas", []) if p]
    if not plataformas_juego:
        return {"juego": juego, "consolas_compatibles": []}

    consolas_activas = obtener_consolas(limite=len(_db_consolas), incluir_eliminados=False)
    consolas_compatibles_encontradas = []

    for consola in consolas_activas:
        nombre_consola_lower = consola.get("nombre", "").strip().lower()
        if nombre_consola_lower and nombre_consola_lower in plataformas_juego:
            accesorios_consola = obtener_accesorios_por_consola(
                id_consola=consola['id'],
                incluir_eliminados=False
            )
            consola_con_accesorios = {**consola, "accesorios": accesorios_consola}
            consolas_compatibles_encontradas.append(consola_con_accesorios)

    resultado = {
        "juego": juego,
        "consolas_compatibles": consolas_compatibles_encontradas
    }

    try:
        JuegoCompatibilidad.model_validate(resultado)
    except Exception as e:
        print(f"Error de validación al construir JuegoCompatibilidad para juego {id_juego}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al procesar la compatibilidad del juego.")

    return resultado