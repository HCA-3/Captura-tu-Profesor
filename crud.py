from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
import modelos
# Importar todos los modelos necesarios
from modelos import (
    Juego, JuegoCrear, JuegoBase,
    Consola, ConsolaCrear, ConsolaBase,
    Accesorio, AccesorioCrear, AccesorioBase,
    ConsolaConAccesorios, JuegoCompatibilidad # Añadir nuevos modelos de relación/respuesta
)
from persistencia import (
    cargar_juegos, guardar_juegos,
    cargar_consolas, guardar_consolas,
    cargar_accesorios, guardar_accesorios
)
from utilidades import obtener_siguiente_id

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
# (obtener_juego_por_id, obtener_juego_activo_por_id, obtener_juegos, crear_juego, actualizar_juego, eliminar_logico_juego, filtrar_juegos_por_genero, buscar_juegos_por_desarrollador)
# ... (Estas funciones permanecen igual que en la versión anterior) ...
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
    # Asegurar que saltar y limite no causen IndexError
    inicio = max(0, saltar)
    fin = inicio + max(0, limite)
    return resultados[inicio:fin]


def crear_juego(datos_juego: JuegoCrear) -> Dict[str, Any]:
    """Crea un nuevo juego."""
    nuevo_id = obtener_siguiente_id()
    # Validación opcional: Evitar títulos duplicados activos
    titulo_nuevo = datos_juego.titulo.strip().lower()
    existente = next((j for j in _db_juegos if j.get("titulo", "").strip().lower() == titulo_nuevo and not j.get("esta_eliminado")), None)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un juego activo con el título '{datos_juego.titulo}'."
        )

    nuevo_juego_dict = Juego(
        id=nuevo_id,
        esta_eliminado=False,
        **datos_juego.model_dump() # Usar model_dump() en Pydantic v2+
    ).model_dump()

    _db_juegos.append(nuevo_juego_dict)
    guardar_juegos(_db_juegos)
    return nuevo_juego_dict

def actualizar_juego(id_juego: int, datos_actualizacion: JuegoCrear) -> Optional[Dict[str, Any]]:
    """Actualiza un juego existente."""
    indice_juego = -1
    for i, juego in enumerate(_db_juegos):
        if juego.get("id") == id_juego:
            # No actualizar si está marcado como eliminado
            if juego.get("esta_eliminado", False):
                 raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, # O 400 Bad Request
                    detail=f"El juego con ID {id_juego} está eliminado y no se puede modificar."
                )
            indice_juego = i
            break

    if indice_juego == -1:
        # Si no se encontró, lanzar 404 explícito
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Juego con ID {id_juego} no encontrado.")


    juego_a_actualizar = _db_juegos[indice_juego]
    # Usar model_dump con exclude_unset=True para obtener solo los campos enviados
    datos_nuevos = datos_actualizacion.model_dump(exclude_unset=True)

    # Validar título duplicado si se intenta cambiar
    if "titulo" in datos_nuevos:
        titulo_nuevo = datos_nuevos["titulo"].strip().lower()
        titulo_actual = juego_a_actualizar.get("titulo", "").strip().lower()
        if titulo_nuevo != titulo_actual:
             existente = next((j for i, j in enumerate(_db_juegos) if i != indice_juego and j.get("titulo", "").strip().lower() == titulo_nuevo and not j.get("esta_eliminado")), None)
             if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe otro juego activo con el título '{datos_nuevos['titulo']}'."
                )

    # Aplicar actualizaciones solo a los campos definidos en JuegoBase
    campos_actualizables = set(JuegoBase.model_fields.keys()) # Pydantic v2+
    for clave, valor in datos_nuevos.items():
         if clave in campos_actualizables:
              juego_a_actualizar[clave] = valor

    # _db_juegos[indice_juego] = juego_a_actualizar # Ya se modifica por referencia
    guardar_juegos(_db_juegos)
    return juego_a_actualizar # Devolver el diccionario actualizado


def eliminar_logico_juego(id_juego: int) -> Optional[Dict[str, Any]]:
    """Marca un juego como eliminado (borrado lógico)."""
    juego = obtener_juego_por_id(id_juego)
    if juego is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Juego con ID {id_juego} no encontrado.")
    if juego.get("esta_eliminado"):
        # Considerar si devolver el juego ya eliminado o un 404/409
         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Juego con ID {id_juego} ya está eliminado.")


    juego['esta_eliminado'] = True
    guardar_juegos(_db_juegos)
    return juego # Devolver el juego marcado como eliminado

def filtrar_juegos_por_genero(genero: str) -> List[Dict[str, Any]]:
    """Busca juegos activos por género (búsqueda parcial, insensible a mayúsculas)."""
    consulta_genero = genero.strip().lower()
    if not consulta_genero:
        return [] # O podrías lanzar un 400 Bad Request si se requiere un término
    juegos_activos = obtener_juegos(limite=len(_db_juegos), incluir_eliminados=False) # Obtener todos los activos
    return [j for j in juegos_activos if consulta_genero in j.get("genero", "").lower()]

def buscar_juegos_por_desarrollador(nombre_dev: str) -> List[Dict[str, Any]]:
    """Busca juegos activos por nombre de desarrollador (búsqueda parcial, insensible a mayúsculas)."""
    consulta_dev = nombre_dev.strip().lower()
    if not consulta_dev:
        return []
    juegos_activos = obtener_juegos(limite=len(_db_juegos), incluir_eliminados=False)
    return [j for j in juegos_activos if consulta_dev in j.get("nombre_desarrollador", "").lower()]


# --- Operaciones CRUD para Consolas ---
# (obtener_consola_por_id, obtener_consola_activa_por_id, obtener_consolas, crear_consola, actualizar_consola, eliminar_logico_consola, buscar_consolas_por_fabricante)
# ... (Estas funciones permanecen igual que en la versión anterior) ...
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

def crear_consola(datos_consola: ConsolaCrear) -> Dict[str, Any]:
    """Crea una nueva consola."""
    nuevo_id = obtener_siguiente_id()
    # Validación: Evitar nombres duplicados activos
    nombre_nuevo = datos_consola.nombre.strip().lower()
    existente = next((c for c in _db_consolas if c.get("nombre", "").strip().lower() == nombre_nuevo and not c.get("esta_eliminado")), None)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una consola activa con el nombre '{datos_consola.nombre}'."
        )

    nueva_consola_dict = Consola(
        id=nuevo_id,
        esta_eliminado=False,
        **datos_consola.model_dump()
    ).model_dump()

    _db_consolas.append(nueva_consola_dict)
    guardar_consolas(_db_consolas)
    return nueva_consola_dict

def actualizar_consola(id_consola: int, datos_actualizacion: ConsolaCrear) -> Optional[Dict[str, Any]]:
    """Actualiza una consola existente."""
    indice_consola = -1
    for i, consola in enumerate(_db_consolas):
        if consola.get("id") == id_consola:
            if consola.get("esta_eliminado", False):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, # O 400
                    detail=f"La consola con ID {id_consola} está eliminada y no se puede modificar."
                )
            indice_consola = i
            break

    if indice_consola == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Consola con ID {id_consola} no encontrada.")


    consola_a_actualizar = _db_consolas[indice_consola]
    datos_nuevos = datos_actualizacion.model_dump(exclude_unset=True)

    # Validar nombre duplicado si se cambia
    if "nombre" in datos_nuevos:
        nombre_nuevo = datos_nuevos["nombre"].strip().lower()
        nombre_actual = consola_a_actualizar.get("nombre", "").strip().lower()
        if nombre_nuevo != nombre_actual:
             existente = next((c for i, c in enumerate(_db_consolas) if i != indice_consola and c.get("nombre", "").strip().lower() == nombre_nuevo and not c.get("esta_eliminado")), None)
             if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe otra consola activa con el nombre '{datos_nuevos['nombre']}'."
                )

    # Aplicar actualizaciones
    campos_actualizables = set(ConsolaBase.model_fields.keys())
    for clave, valor in datos_nuevos.items():
         if clave in campos_actualizables:
              consola_a_actualizar[clave] = valor

    guardar_consolas(_db_consolas)
    return consola_a_actualizar


def eliminar_logico_consola(id_consola: int) -> Optional[Dict[str, Any]]:
    """Marca una consola como eliminada (borrado lógico)."""
    consola = obtener_consola_por_id(id_consola)
    if consola is None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Consola con ID {id_consola} no encontrada.")
    if consola.get("esta_eliminado"):
         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Consola con ID {id_consola} ya está eliminada.")


    consola['esta_eliminado'] = True
    # Consideración: Al eliminar una consola, ¿qué pasa con sus accesorios?
    # Podríamos marcarlos como eliminados también.
    accesorios_afectados = obtener_accesorios_por_consola(id_consola, incluir_eliminados=False)
    for acc in accesorios_afectados:
        eliminar_logico_accesorio(acc['id']) # Llama a la función de borrado lógico de accesorios
    print(f"INFO: {len(accesorios_afectados)} accesorios asociados a la consola {id_consola} también han sido marcados como eliminados.")

    guardar_consolas(_db_consolas) # Guardar el estado de la consola
    # Nota: guardar_accesorios se llama dentro de eliminar_logico_accesorio
    return consola

def buscar_consolas_por_fabricante(fabricante: str) -> List[Dict[str, Any]]:
    """Busca consolas activas por fabricante (búsqueda parcial, insensible a mayúsculas)."""
    consulta = fabricante.strip().lower()
    if not consulta:
        return []
    consolas_activas = obtener_consolas(limite=len(_db_consolas), incluir_eliminados=False)
    return [c for c in consolas_activas if consulta in c.get("fabricante", "").lower()]


# --- Operaciones CRUD para Accesorios ---
# (obtener_accesorio_por_id, obtener_accesorio_activo_por_id, obtener_accesorios, crear_accesorio, actualizar_accesorio, eliminar_logico_accesorio, obtener_accesorios_por_consola)
# ... (Estas funciones permanecen igual que en la versión anterior) ...
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

def crear_accesorio(datos_accesorio: AccesorioCrear) -> Dict[str, Any]:
    """Crea un nuevo accesorio."""
    # 1. Validar que la consola asociada existe y está activa
    consola_asociada = obtener_consola_activa_por_id(datos_accesorio.id_consola)
    if consola_asociada is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Cambiado a 400, es un input inválido
            detail=f"No se encontró una consola activa con ID {datos_accesorio.id_consola} para asociar el accesorio."
        )

    # 2. Validación opcional: Evitar nombres duplicados para la *misma consola*
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

    # 3. Crear el accesorio
    nuevo_id = obtener_siguiente_id()
    nuevo_accesorio_dict = Accesorio(
        id=nuevo_id,
        esta_eliminado=False,
        **datos_accesorio.model_dump()
    ).model_dump()

    _db_accesorios.append(nuevo_accesorio_dict)
    guardar_accesorios(_db_accesorios)
    return nuevo_accesorio_dict

def actualizar_accesorio(id_accesorio: int, datos_actualizacion: AccesorioCrear) -> Optional[Dict[str, Any]]:
    """Actualiza un accesorio existente."""
    indice_accesorio = -1
    for i, acc in enumerate(_db_accesorios):
        if acc.get("id") == id_accesorio:
            if acc.get("esta_eliminado", False):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, # O 400
                    detail=f"El accesorio con ID {id_accesorio} está eliminado y no se puede modificar."
                )
            indice_accesorio = i
            break

    if indice_accesorio == -1:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Accesorio con ID {id_accesorio} no encontrado.")


    accesorio_a_actualizar = _db_accesorios[indice_accesorio]
    datos_nuevos = datos_actualizacion.model_dump(exclude_unset=True)

    # 1. Validar si se cambia id_consola: la nueva consola debe existir y estar activa
    if "id_consola" in datos_nuevos and datos_nuevos["id_consola"] != accesorio_a_actualizar.get("id_consola"):
        nueva_consola = obtener_consola_activa_por_id(datos_nuevos["id_consola"])
        if nueva_consola is None:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, # Cambiado a 400
                detail=f"No se encontró una consola activa con ID {datos_nuevos['id_consola']} para re-asociar el accesorio."
            )

    # 2. Validar nombre duplicado si se cambia (dentro de la consola nueva o actual)
    consola_id_final = datos_nuevos.get("id_consola", accesorio_a_actualizar.get("id_consola"))
    if "nombre" in datos_nuevos:
        nombre_nuevo = datos_nuevos["nombre"].strip().lower()
        nombre_actual = accesorio_a_actualizar.get("nombre", "").strip().lower()

        # Validar solo si el nombre cambia O si la consola cambia
        if nombre_nuevo != nombre_actual or consola_id_final != accesorio_a_actualizar.get("id_consola"):
             existente = next((
                a for i, a in enumerate(_db_accesorios)
                if i != indice_accesorio # Excluir el propio accesorio
                and a.get("id_consola") == consola_id_final
                and a.get("nombre", "").strip().lower() == nombre_nuevo
                and not a.get("esta_eliminado")
            ), None)
             if existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ya existe otro accesorio activo con el nombre '{datos_nuevos['nombre']}' para la consola ID {consola_id_final}."
                )

    # 3. Aplicar actualizaciones
    campos_actualizables = set(AccesorioBase.model_fields.keys())
    for clave, valor in datos_nuevos.items():
         if clave in campos_actualizables:
              accesorio_a_actualizar[clave] = valor

    guardar_accesorios(_db_accesorios)
    return accesorio_a_actualizar

def eliminar_logico_accesorio(id_accesorio: int) -> Optional[Dict[str, Any]]:
    """Marca un accesorio como eliminado (borrado lógico)."""
    accesorio = obtener_accesorio_por_id(id_accesorio)
    if accesorio is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Accesorio con ID {id_accesorio} no encontrado.")
    if accesorio.get("esta_eliminado"):
        # Evitar doble borrado o errores si se llama múltiples veces (ej. desde borrado de consola)
        print(f"INFO: El accesorio con ID {id_accesorio} ya estaba marcado como eliminado.")
        return accesorio # Devolver el estado actual
        # O podrías lanzar 409 si prefieres ser estricto:
        # raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Accesorio con ID {id_accesorio} ya está eliminado.")

    accesorio['esta_eliminado'] = True
    guardar_accesorios(_db_accesorios)
    return accesorio

def obtener_accesorios_por_consola(id_consola: int, incluir_eliminados: bool = False) -> List[Dict[str, Any]]:
    """Obtiene los accesorios asociados a una consola específica."""
    # No necesitamos verificar la existencia de la consola aquí,
    # ya que simplemente filtramos la lista de accesorios.
    # La verificación se hará en el endpoint que llama a esta función si es necesario.

    accesorios_consola = [
        acc for acc in _db_accesorios
        if acc.get("id_consola") == id_consola
    ]

    if not incluir_eliminados:
        accesorios_consola = [acc for acc in accesorios_consola if not acc.get("esta_eliminado", False)]

    return accesorios_consola


# --- Nueva Función de Compatibilidad Juego-Consola-Accesorio ---

def obtener_compatibilidad_juego(id_juego: int) -> Dict[str, Any]:
    """
    Obtiene los detalles de un juego, las consolas activas en las que se ejecuta
    (según su campo 'plataformas') y los accesorios activos para esas consolas.
    """
    # 1. Obtener el juego activo
    juego = obtener_juego_activo_por_id(id_juego)
    if juego is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Juego con ID {id_juego} no encontrado o está inactivo."
        )

    # 2. Obtener plataformas del juego (en minúsculas para comparación)
    plataformas_juego = [p.strip().lower() for p in juego.get("plataformas", []) if p]
    if not plataformas_juego:
        # Si el juego no tiene plataformas listadas, no podemos encontrar consolas compatibles.
        return {"juego": juego, "consolas_compatibles": []}

    # 3. Obtener todas las consolas activas
    consolas_activas = obtener_consolas(limite=len(_db_consolas), incluir_eliminados=False)

    # 4. Filtrar consolas cuya nombre (en minúsculas) esté en las plataformas del juego
    consolas_compatibles_encontradas = []
    for consola in consolas_activas:
        nombre_consola_lower = consola.get("nombre", "").strip().lower()
        if nombre_consola_lower and nombre_consola_lower in plataformas_juego:
            # 5. Para cada consola compatible, obtener sus accesorios activos
            accesorios_consola = obtener_accesorios_por_consola(
                id_consola=consola['id'],
                incluir_eliminados=False
            )
            # Crear el objeto ConsolaConAccesorios (como diccionario)
            consola_con_accesorios = {**consola, "accesorios": accesorios_consola}
            consolas_compatibles_encontradas.append(consola_con_accesorios)

    # 6. Construir el resultado final
    resultado = {
        "juego": juego,
        "consolas_compatibles": consolas_compatibles_encontradas
    }

    # Validar con Pydantic (opcional pero recomendado para asegurar la estructura)
    try:
        JuegoCompatibilidad.model_validate(resultado)
    except Exception as e:
        print(f"Error de validación al construir JuegoCompatibilidad para juego {id_juego}: {e}")
        # Podrías lanzar un 500 aquí si la estructura interna falla
        raise HTTPException(status_code=500, detail="Error interno al procesar la compatibilidad del juego.")

    return resultado