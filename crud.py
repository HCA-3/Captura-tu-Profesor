from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status, UploadFile
import modelos
from modelos import (
    JuegoCrear,
    ConsolaCrear,
    AccesorioCrear,
    ImagenBase
)
from persistencia import (
    cargar_juegos, guardar_juegos,
    cargar_consolas, guardar_consolas,
    cargar_accesorios, guardar_accesorios
)
from utilidades import obtener_siguiente_id
import almacenamiento # Importar el módulo almacenamiento
import supabase_client # Importar para subida a Supabase

# Bases de datos en memoria (simuladas)
try:
    _db_juegos = cargar_juegos()
    _db_consolas = cargar_consolas()
    _db_accesorios = cargar_accesorios()
except HTTPException:
    # En caso de error al cargar (ej. archivo no existe y no se pudo crear), inicializar vacías
    _db_juegos = []
    _db_consolas = []
    _db_accesorios = []

async def _procesar_y_guardar_imagen(
    imagen_form: Optional[UploadFile],
    save_to_supabase: bool,
    entidad_existente: Optional[Dict[str, Any]] = None,
    campo_imagen_entidad: str = "imagen"
) -> Optional[Dict[str, str]]:
    """Función helper para procesar, guardar imagen y manejar la eliminación de la antigua."""
    imagen_data_procesada: Optional[Dict[str, str]] = None
    imagen_antigua_info: Optional[Dict[str, str]] = None

    if entidad_existente and entidad_existente.get(campo_imagen_entidad):
        imagen_antigua_info = entidad_existente[campo_imagen_entidad]

    if imagen_form:
        await almacenamiento.validar_imagen(imagen_form)
        await imagen_form.seek(0)  # Rebobinar para la subida/guardado

        if save_to_supabase:
            # Subir a Supabase
            resultado_subida = await supabase_client.upload_to_supabase(imagen_form)
            imagen_data_procesada = {
                "nombre_archivo": resultado_subida["path_in_bucket"], # Guardamos el path_in_bucket como nombre_archivo
                "url": resultado_subida["url"]
            }
        else:
            # Guardar localmente
            imagen_data_procesada = await almacenamiento.guardar_imagen(imagen_form)
        
        # Si hay una imagen nueva y existía una antigua, eliminar la antigua
        if imagen_data_procesada and imagen_antigua_info and imagen_antigua_info.get("nombre_archivo"):
            if imagen_antigua_info["url"].startswith(supabase_client.SUPABASE_URL):
                await supabase_client.delete_from_supabase(imagen_antigua_info["nombre_archivo"])
            else:
                almacenamiento.eliminar_imagen(imagen_antigua_info["nombre_archivo"])
        
        return imagen_data_procesada
    
    # Si no se proporciona una nueva imagen (imagen_form es None), pero se quiere eliminar la existente (ej. en una actualización)
    # Esta lógica específica (eliminar sin reemplazar) debe manejarse en la función de actualización si es necesario.
    # Por ahora, esta helper solo se enfoca en el guardado de una *nueva* imagen.
    return None

async def _eliminar_imagen_almacenada(imagen_info: Optional[Dict[str, Any]]):
    if imagen_info and imagen_info.get("nombre_archivo") and imagen_info.get("url"):
        if imagen_info["url"].startswith(supabase_client.SUPABASE_URL):
            await supabase_client.delete_from_supabase(imagen_info["nombre_archivo"])
        else:
            almacenamiento.eliminar_imagen(imagen_info["nombre_archivo"])

# --- Operaciones CRUD para Juegos ---
async def crear_juego(datos_juego: JuegoCrear, imagen_form: Optional[UploadFile] = None, save_to_supabase: bool = False) -> Dict[str, Any]:
    titulo_lower = datos_juego.titulo.lower()
    if any(j["titulo"].lower() == titulo_lower and not j.get("esta_eliminado") for j in _db_juegos):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un juego con este título"
        )

    imagen_data_final: Optional[Dict[str, str]] = None
    try:
        if imagen_form:
            imagen_data_final = await _procesar_y_guardar_imagen(imagen_form, save_to_supabase)
        
        nuevo_juego = {
            "id": obtener_siguiente_id(_db_juegos),
            **datos_juego.model_dump(),
            "imagen": imagen_data_final,
            "esta_eliminado": False
        }
        
        _db_juegos.append(nuevo_juego)
        guardar_juegos(_db_juegos)
        return nuevo_juego
    except Exception as e:
        # Si se procesó una nueva imagen pero falla otra cosa, intentar eliminarla
        if imagen_data_final:
            await _eliminar_imagen_almacenada(imagen_data_final)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al crear juego: {str(e)}")

async def actualizar_juego(id_juego: int, datos_actualizacion_dict: Dict[str, Any], imagen_form: Optional[UploadFile] = None, save_to_supabase: bool = False) -> Dict[str, Any]:
    juego_existente = next((j for j in _db_juegos if j["id"] == id_juego and not j.get("esta_eliminado")), None)
    if not juego_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Juego no encontrado o inactivo")

    if "titulo" in datos_actualizacion_dict and datos_actualizacion_dict["titulo"]:
        nuevo_titulo_lower = datos_actualizacion_dict["titulo"].lower()
        if nuevo_titulo_lower != juego_existente["titulo"].lower():
            if any(j["id"] != id_juego and j["titulo"].lower() == nuevo_titulo_lower and not j.get("esta_eliminado") for j in _db_juegos):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe otro juego con este título"
                )

    imagen_data_actualizada: Optional[Dict[str, str]] = None
    try:
        if imagen_form:
            imagen_data_actualizada = await _procesar_y_guardar_imagen(imagen_form, save_to_supabase, juego_existente)
        
        for field, value in datos_actualizacion_dict.items():
            if value is not None:
                 juego_existente[field] = value
        
        if imagen_data_actualizada:
            juego_existente["imagen"] = imagen_data_actualizada
        # Si imagen_form es None y se quiere borrar explícitamente la imagen, 
        # main.py debería pasar un marcador o el modelo Pydantic debería manejarlo.
        # Por ahora, si imagen_form es None, no se toca la imagen existente a menos que imagen_data_actualizada la reemplace.
            
        guardar_juegos(_db_juegos)
        return juego_existente
    except Exception as e:
        # Si se guardó una nueva imagen pero falla otra cosa, y no es la que ya estaba, eliminarla
        if imagen_data_actualizada and imagen_data_actualizada != juego_existente.get("imagen"):
            await _eliminar_imagen_almacenada(imagen_data_actualizada)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al actualizar juego: {str(e)}")

async def eliminar_logico_juego(id_juego: int) -> Dict[str, Any]:
    juego = next((j for j in _db_juegos if j["id"] == id_juego), None)
    if not juego or juego.get("esta_eliminado"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Juego no encontrado o ya eliminado")
    
    await _eliminar_imagen_almacenada(juego.get("imagen"))
    juego["imagen"] = None

    juego["esta_eliminado"] = True
    guardar_juegos(_db_juegos)
    return juego

# --- Operaciones CRUD para Consolas ---
async def crear_consola(datos_consola: ConsolaCrear, imagen_form: Optional[UploadFile] = None, save_to_supabase: bool = False) -> Dict[str, Any]:
    nombre_lower = datos_consola.nombre.lower()
    if any(c["nombre"].lower() == nombre_lower and not c.get("esta_eliminado") for c in _db_consolas):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una consola con este nombre"
        )
    imagen_data_final: Optional[Dict[str, str]] = None
    try:
        if imagen_form:
            imagen_data_final = await _procesar_y_guardar_imagen(imagen_form, save_to_supabase)
        nueva_consola = {
            "id": obtener_siguiente_id(_db_consolas),
            **datos_consola.model_dump(),
            "imagen": imagen_data_final,
            "esta_eliminado": False
        }
        _db_consolas.append(nueva_consola)
        guardar_consolas(_db_consolas)
        return nueva_consola
    except Exception as e:
        if imagen_data_final:
            await _eliminar_imagen_almacenada(imagen_data_final)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al crear consola: {str(e)}")

async def actualizar_consola(id_consola: int, datos_actualizacion_dict: Dict[str, Any], imagen_form: Optional[UploadFile] = None, save_to_supabase: bool = False) -> Dict[str, Any]:
    consola_existente = next((c for c in _db_consolas if c["id"] == id_consola and not c.get("esta_eliminado")), None)
    if not consola_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consola no encontrada o inactiva")

    if "nombre" in datos_actualizacion_dict and datos_actualizacion_dict["nombre"]:
        nuevo_nombre_lower = datos_actualizacion_dict["nombre"].lower()
        if nuevo_nombre_lower != consola_existente["nombre"].lower():
            if any(c["id"] != id_consola and c["nombre"].lower() == nuevo_nombre_lower and not c.get("esta_eliminado") for c in _db_consolas):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe otra consola con este nombre"
                )
    imagen_data_actualizada: Optional[Dict[str, str]] = None
    try:
        if imagen_form:
            imagen_data_actualizada = await _procesar_y_guardar_imagen(imagen_form, save_to_supabase, consola_existente)
        
        for field, value in datos_actualizacion_dict.items():
            if value is not None:
                consola_existente[field] = value
        
        if imagen_data_actualizada:
            consola_existente["imagen"] = imagen_data_actualizada
            
        guardar_consolas(_db_consolas)
        return consola_existente
    except Exception as e:
        if imagen_data_actualizada and imagen_data_actualizada != consola_existente.get("imagen"):
            await _eliminar_imagen_almacenada(imagen_data_actualizada)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al actualizar consola: {str(e)}")

async def eliminar_logico_consola(id_consola: int) -> Dict[str, Any]:
    consola = next((c for c in _db_consolas if c["id"] == id_consola), None)
    if not consola or consola.get("esta_eliminado"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consola no encontrada o ya eliminada")

    await _eliminar_imagen_almacenada(consola.get("imagen"))
    consola["imagen"] = None
    consola["esta_eliminado"] = True

    # También eliminar lógicamente los accesorios asociados y sus imágenes
    for acc in _db_accesorios:
        if acc["id_consola"] == id_consola and not acc.get("esta_eliminado"):
            await _eliminar_imagen_almacenada(acc.get("imagen"))
            acc["imagen"] = None
            acc["esta_eliminado"] = True
            
    guardar_consolas(_db_consolas)
    guardar_accesorios(_db_accesorios)
    return consola

# --- Operaciones CRUD para Accesorios ---
async def crear_accesorio(datos_accesorio: AccesorioCrear, imagen_form: Optional[UploadFile] = None, save_to_supabase: bool = False) -> Dict[str, Any]:
    consola_madre = next((c for c in _db_consolas if c["id"] == datos_accesorio.id_consola and not c.get("esta_eliminado")), None)
    if not consola_madre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La consola con ID {datos_accesorio.id_consola} no existe o no está activa."
        )
    
    nombre_lower = datos_accesorio.nombre.lower()
    if any(a["nombre"].lower() == nombre_lower and a["id_consola"] == datos_accesorio.id_consola and not a.get("esta_eliminado") for a in _db_accesorios):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un accesorio con este nombre para la consola ID {datos_accesorio.id_consola}"
        )

    imagen_data_final: Optional[Dict[str, str]] = None
    try:
        if imagen_form:
            imagen_data_final = await _procesar_y_guardar_imagen(imagen_form, save_to_supabase)
        nuevo_accesorio = {
            "id": obtener_siguiente_id(_db_accesorios),
            **datos_accesorio.model_dump(),
            "imagen": imagen_data_final,
            "esta_eliminado": False
        }
        _db_accesorios.append(nuevo_accesorio)
        guardar_accesorios(_db_accesorios)
        return nuevo_accesorio
    except Exception as e:
        if imagen_data_final:
            await _eliminar_imagen_almacenada(imagen_data_final)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al crear accesorio: {str(e)}")

async def actualizar_accesorio(id_accesorio: int, datos_actualizacion_dict: Dict[str, Any], imagen_form: Optional[UploadFile] = None, save_to_supabase: bool = False) -> Dict[str, Any]:
    accesorio_existente = next((a for a in _db_accesorios if a["id"] == id_accesorio and not a.get("esta_eliminado")), None)
    if not accesorio_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accesorio no encontrado o inactivo")

    if "id_consola" in datos_actualizacion_dict and datos_actualizacion_dict["id_consola"] and datos_actualizacion_dict["id_consola"] != accesorio_existente["id_consola"]:
        consola_madre_nueva = next((c for c in _db_consolas if c["id"] == datos_actualizacion_dict["id_consola"] and not c.get("esta_eliminado")), None)
        if not consola_madre_nueva:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La nueva consola con ID {datos_actualizacion_dict['id_consola']} no existe o no está activa."
            )
    
    id_consola_para_validacion_nombre = datos_actualizacion_dict.get("id_consola", accesorio_existente["id_consola"])
    if "nombre" in datos_actualizacion_dict and datos_actualizacion_dict["nombre"]:
        nuevo_nombre_lower = datos_actualizacion_dict["nombre"].lower()
        if nuevo_nombre_lower != accesorio_existente["nombre"].lower() or id_consola_para_validacion_nombre != accesorio_existente["id_consola"]:
            if any(a["id"] != id_accesorio and \
                   a["nombre"].lower() == nuevo_nombre_lower and \
                   a["id_consola"] == id_consola_para_validacion_nombre and \
                   not a.get("esta_eliminado") for a in _db_accesorios):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe un accesorio con este nombre para la consola ID {id_consola_para_validacion_nombre}"
                )

    imagen_data_actualizada: Optional[Dict[str, str]] = None
    try:
        if imagen_form:
            imagen_data_actualizada = await _procesar_y_guardar_imagen(imagen_form, save_to_supabase, accesorio_existente)
        
        for field, value in datos_actualizacion_dict.items():
            if value is not None:
                accesorio_existente[field] = value
        
        if imagen_data_actualizada:
            accesorio_existente["imagen"] = imagen_data_actualizada
            
        guardar_accesorios(_db_accesorios)
        return accesorio_existente
    except Exception as e:
        if imagen_data_actualizada and imagen_data_actualizada != accesorio_existente.get("imagen"):
            await _eliminar_imagen_almacenada(imagen_data_actualizada)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno al actualizar accesorio: {str(e)}")

async def eliminar_logico_accesorio(id_accesorio: int) -> Dict[str, Any]:
    accesorio = next((a for a in _db_accesorios if a["id"] == id_accesorio), None)
    if not accesorio or accesorio.get("esta_eliminado"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accesorio no encontrado o ya eliminado")

    await _eliminar_imagen_almacenada(accesorio.get("imagen"))
    accesorio["imagen"] = None
    accesorio["esta_eliminado"] = True
    guardar_accesorios(_db_accesorios)
    return accesorio

# --- Funciones de lectura (no necesitan cambios para save_to_supabase) ---
def obtener_juegos(saltar: int = 0, limite: int = 10, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    juegos_filtrados = _db_juegos if incluir_eliminados else [j for j in _db_juegos if not j.get("esta_eliminado")]
    return juegos_filtrados[saltar : saltar + limite]

def obtener_juego_activo_por_id(id_juego: int) -> Optional[Dict[str, Any]]:
    juego = next((j for j in _db_juegos if j["id"] == id_juego and not j.get("esta_eliminado")), None)
    return juego

def filtrar_juegos_por_genero(genero: str) -> List[Dict[str, Any]]:
    genero_lower = genero.lower()
    return [j for j in _db_juegos if not j.get("esta_eliminado") and j.get("genero") and genero_lower in j["genero"].lower()]

def buscar_juegos_por_desarrollador(nombre_dev: str) -> List[Dict[str, Any]]:
    nombre_dev_lower = nombre_dev.lower()
    return [j for j in _db_juegos if not j.get("esta_eliminado") and j.get("nombre_desarrollador") and nombre_dev_lower in j["nombre_desarrollador"].lower()]

def obtener_consolas(saltar: int = 0, limite: int = 10, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    consolas_filtradas = _db_consolas if incluir_eliminados else [c for c in _db_consolas if not c.get("esta_eliminado")]
    return consolas_filtradas[saltar : saltar + limite]

def obtener_consola_activa_por_id(id_consola: int) -> Optional[Dict[str, Any]]:
    consola = next((c for c in _db_consolas if c["id"] == id_consola and not c.get("esta_eliminado")), None)
    return consola

def buscar_consolas_por_fabricante(fabricante: str) -> List[Dict[str, Any]]:
    fabricante_lower = fabricante.lower()
    return [c for c in _db_consolas if not c.get("esta_eliminado") and c.get("fabricante") and fabricante_lower in c["fabricante"].lower()]

def obtener_accesorios_por_consola(id_consola: int, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    accesorios_filtrados = [a for a in _db_accesorios if a["id_consola"] == id_consola]
    if not incluir_eliminados:
        accesorios_filtrados = [a for a in accesorios_filtrados if not a.get("esta_eliminado")]
    return accesorios_filtrados

def obtener_accesorios(saltar: int = 0, limite: int = 10, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    accesorios_filtrados = _db_accesorios if incluir_eliminados else [a for a in _db_accesorios if not a.get("esta_eliminado")]
    return accesorios_filtrados[saltar : saltar + limite]

def obtener_accesorio_activo_por_id(id_accesorio: int) -> Optional[Dict[str, Any]]:
    accesorio = next((a for a in _db_accesorios if a["id"] == id_accesorio and not a.get("esta_eliminado")), None)
    return accesorio

def obtener_compatibilidad_juego(id_juego: int) -> Dict[str, Any]:
    juego = obtener_juego_activo_por_id(id_juego)
    if not juego:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Juego no encontrado o inactivo")

    consolas_compatibles_info = []
    juego_plataformas_lower = [p.lower() for p in juego.get("plataformas", [])]

    for consola_dict in _db_consolas:
        if not consola_dict.get("esta_eliminado") and consola_dict["nombre"].lower() in juego_plataformas_lower:
            accesorios_de_consola = obtener_accesorios_por_consola(consola_dict["id"], incluir_eliminados=False)
            consola_con_accesorios = {
                **consola_dict,
                "accesorios": accesorios_de_consola
            }
            consolas_compatibles_info.append(consola_con_accesorios)
    
    return {"juego": juego, "consolas_compatibles": consolas_compatibles_info}

