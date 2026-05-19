import os
import secrets
from datetime import datetime, timedelta
from hmac import compare_digest

from dotenv import load_dotenv
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import desc, and_, func
from werkzeug.security import check_password_hash

from DAO.db import db_session
from Entities.CategoriaServicio import CategoriaServicio
from Entities.Citas import Cita, EstadoCita
from Entities.Cliente import Cliente
from Entities.DetalleCita import DetalleCita
from Entities.Servicios import Servicio
from config_email import send_email

load_dotenv()
# Configuración de la aplicación Flask y seguridad de sesiones
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(32))
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
    minutes=int(os.getenv("SESSION_LIFETIME_MINUTES", "30"))
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

# Configuración del serializer para generación de tokens
serializer = URLSafeTimedSerializer(
    os.getenv("SECRET_KEY", app.config["SECRET_KEY"]),
    salt=os.getenv("SECURITY_PASSWORD_SALT", "studio02-confirmar-cita"),
)
# Configuración de seguridad para login
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOGIN_BLOCK_MINUTES = int(os.getenv("LOGIN_BLOCK_MINUTES", "15"))
LOGIN_ATTEMPTS = {}

# Rutas y lógica de la aplicación
def validar_horario_cita(fecha_inicio, fecha_fin=None):
    """Valida que la cita esté dentro del horario permitido (10 AM - 10 PM)"""
    if hasattr(fecha_inicio, 'hour'):
        inicio_hora = fecha_inicio.hour
    else:
        inicio_hora = datetime.fromisoformat(fecha_inicio).hour

    if fecha_fin is None:
        if inicio_hora < 10 or inicio_hora >= 22:
            return False, "El horario debe estar entre 10 AM y 10 PM"
    else:
        if hasattr(fecha_fin, 'hour'):
            fin_hora = fecha_fin.hour
        else:
            fin_hora = datetime.fromisoformat(fecha_fin).hour
        if inicio_hora < 10 or fin_hora > 22:
            return False, "El horario debe estar entre 10 AM y 10 PM"

    return True, ""

# Validaciones de negocio para citas y servicios, incluyendo días de la semana, solapamientos y límites por día.
def validar_dia_semana(fecha):
    """Valida que la cita NO sea en sábado (5) ni domingo (6)"""
    if hasattr(fecha, 'weekday'):
        dia = fecha.weekday()
    else:
        dia = datetime.fromisoformat(fecha).weekday()

    if dia in [5, 6]:
        return False, "No hay servicio disponible los sábados ni domingos"
    return True, ""

# Validaciones para servicios por día y solapamientos, considerando también la edición de citas existentes.
def calcular_duracion_servicios(servicios_ids):
    """Calcula la duración total en minutos de los servicios seleccionados"""
    if not servicios_ids:
        return 0
    duracion_total = 0
    for servicio_id in servicios_ids:
        servicio = db_session.query(Servicio).get(int(servicio_id))
        if servicio:
            duracion_total += servicio.duracion_minutos
    return duracion_total

# Validación de máximo 3 servicios por día y máximo 1 servicio >90 minutos por día, considerando también las citas existentes del cliente.
def calcular_fecha_fin(fecha_inicio, duracion_minutos):
    """Calcula la fecha de fin basada en la duración en minutos"""
    if isinstance(fecha_inicio, str):
        fecha_inicio = datetime.fromisoformat(fecha_inicio)
    return fecha_inicio + timedelta(minutes=duracion_minutos)

# Validación de solapamiento de citas, considerando también la edición de citas existentes. 
def validar_servicios_por_dia(id_cliente, fecha_inicio, servicios_ids, id_cita_actual=None):
    """Valida máximo 3 servicios por día y máximo 1 servicio >90 minutos por día"""
    if isinstance(fecha_inicio, str):
        fecha_inicio = datetime.fromisoformat(fecha_inicio)
# Para validar por día, obtenemos el rango del día completo y contamos los servicios existentes en ese día para el cliente, excluyendo la cita actual si se está
    fecha_inicio_dia = fecha_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_fin_dia = fecha_inicio_dia + timedelta(days=1)

    query = db_session.query(Cita).filter(
        Cita.id_cliente == id_cliente,
        Cita.estado == "agendada",
        Cita.fecha_inicio >= fecha_inicio_dia,
        Cita.fecha_inicio < fecha_fin_dia
    )
# Si estamos editando una cita, excluimos esa cita de la validación para no contar sus servicios actuales.
    if id_cita_actual:
        query = query.filter(Cita.id_cita != id_cita_actual)

    citas_dia = query.all()

    servicios_existentes_count = 0
    servicios_largo_count = 0
# Contamos los servicios existentes en las citas del día para el cliente, y cuántos de esos servicios son >90 minutos. Esto nos permitirá validar los límites al agregar nuevos servicios.
    for cita in citas_dia:
        servicios_existentes_count += len(cita.detalles)
        for detalle in cita.detalles:
            if detalle.servicio.duracion_minutos > 90:
                servicios_largo_count += 1
# Obtenemos los servicios nuevos que se quieren agregar, y contamos cuántos de esos servicios son >90 minutos. Esto nos permitirá validar los límites al agregar nuevos servicios.
    servicios_nuevos = [db_session.query(Servicio).get(int(s)) for s in servicios_ids]
    servicios_nuevos = [s for s in servicios_nuevos if s]

    servicios_nuevos_largo = [s for s in servicios_nuevos if s.duracion_minutos > 90]

    total_servicios = servicios_existentes_count + len(servicios_nuevos)
    if total_servicios > 3:
        return False, f"Máximo 3 servicios por día. Ya tiene {servicios_existentes_count}, intenta agregar {len(servicios_nuevos)}."

    total_largo = servicios_largo_count + len(servicios_nuevos_largo)
    if total_largo > 1:
        return False, "Solo se puede agendar 1 servicio de más de 90 minutos por día."

    return True, ""

# Validación de solapamiento de citas, considerando también la edición de citas existentes. Se valida que no exista otra cita agendada que se solape en el mismo lapso de tiempo, excluyendo la cita actual si se está editando.
def validar_solapamiento(fecha_inicio, fecha_fin, id_cita_actual=None):
    """Valida que no haya otra cita agendada en el mismo lapso de tiempo"""
    if isinstance(fecha_inicio, str):
        fecha_inicio = datetime.fromisoformat(fecha_inicio)
    if isinstance(fecha_fin, str):
        fecha_fin = datetime.fromisoformat(fecha_fin)
# Para validar solapamiento, buscamos cualquier cita que se solape con el rango de fecha_inicio a fecha_fin. Si estamos editando una cita, excluimos esa cita de la validación para no comparar contra sí misma.
    query = db_session.query(Cita).filter(
        Cita.estado == "agendada",
        Cita.fecha_inicio < fecha_fin,
        Cita.fecha_fin > fecha_inicio
    )
# Si estamos editando una cita, excluimos esa cita de la validación para no comparar contra sí misma.
    if id_cita_actual:
        query = query.filter(Cita.id_cita != id_cita_actual)

    citas_solapadas = query.all()

    if citas_solapadas:
        return False, "Ya existe una cita agendada en ese horario. Por favor, selecciona otro horario."
    return True, ""

# Resto de la aplicación con rutas, autenticación, manejo de sesiones, y lógica de negocio para registro y gestión de citas.
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# Inyección de token CSRF en formularios y aplicación de cabeceras de seguridad en las respuestas.
@app.context_processor
def inject_csrf_token():
    return {"csrf_token": _generar_csrf_token}

# Aplicación de cabeceras de seguridad y control de cache para rutas sensibles.
@app.after_request
def apply_security_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
# Para rutas sensibles, aplicamos cabeceras de no-cache para evitar que el navegador almacene información sensible en caché. Esto se aplica a las rutas de login, historial y edición de citas, así como a cualquier ruta si el usuario está logueado.
    if request.endpoint in {"login", "historial", "editar_cita"} or _usuario_logueado():
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response

# Funciones auxiliares para autenticación, manejo de sesiones, generación de tokens CSRF, validación de credenciales, y construcción de eventos para el calendario.
def _usuario_logueado():
    return bool(session.get("logueado"))

# Funciones auxiliares para manejo de intentos de login, generación de tokens CSRF, validación de credenciales, y construcción de eventos para el calendario.
def _cliente_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "desconocido"

# Funciones auxiliares para manejo de intentos de login, generación de tokens CSRF, validación de credenciales, y construcción de eventos para el calendario.
def _login_attempt_key(usuario):
    return f"{_cliente_ip()}:{(usuario or '').strip().lower()}"

# Funciones auxiliares para manejo de intentos de login, generación de tokens CSRF, validación de credenciales, y construcción de eventos para el calendario.
def _login_bloqueado(usuario):
    intento = LOGIN_ATTEMPTS.get(_login_attempt_key(usuario))
    if not intento:
        return False, None
# Si el intento existe pero el tiempo de bloqueo ha expirado, limpiamos el intento para permitir nuevos intentos de login.
    if intento["blocked_until"] <= datetime.utcnow():
        LOGIN_ATTEMPTS.pop(_login_attempt_key(usuario), None)
        return False, None
# Si el intento existe y el tiempo de bloqueo aún no ha expirado, calculamos los minutos restantes de bloqueo para informar al usuario.
    restante = intento["blocked_until"] - datetime.utcnow()
    minutos = max(1, int(restante.total_seconds() // 60))
    return True, minutos

# Funciones auxiliares para manejo de intentos de login, generación de tokens CSRF, validación de credenciales, y construcción de eventos para el calendario.
def _registrar_login_fallido(usuario):
    llave = _login_attempt_key(usuario)
    ahora = datetime.utcnow()
    intento = LOGIN_ATTEMPTS.get(
        llave,
        {"count": 0, "blocked_until": ahora},
    )
    intento["count"] += 1
# Si el número de intentos supera el máximo permitido, establecemos un tiempo de bloqueo para ese usuario/IP.
    if intento["count"] >= MAX_LOGIN_ATTEMPTS:
        intento["blocked_until"] = ahora + timedelta(minutes=LOGIN_BLOCK_MINUTES)

    LOGIN_ATTEMPTS[llave] = intento

# Funciones auxiliares para manejo de intentos de login, generación de tokens CSRF, validación de credenciales, y construcción de eventos para el calendario.
def _limpiar_intentos_login(usuario):
    LOGIN_ATTEMPTS.pop(_login_attempt_key(usuario), None)

# Funciones auxiliares para manejo de intentos de login, generación de tokens CSRF, validación de credenciales, y construcción de eventos para el calendario.
def _generar_csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token

# Funciones auxiliares para manejo de intentos de login, generación de tokens CSRF, validación de credenciales, y construcción de eventos para el calendario.
def _validar_csrf():
    token_sesion = session.get("_csrf_token")
    token_form = request.form.get("csrf_token", "")
    if not token_sesion or not compare_digest(token_sesion, token_form):
        abort(400, description="Token CSRF invalido")

# Funciones auxiliares para manejo de intentos de login, generación de tokens CSRF, validación de credenciales, y construcción de eventos para el calendario.
def _credenciales_admin_validas(usuario, password):
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")
    admin_password_plain = os.getenv("ADMIN_PASSWORD")
# Validamos que el usuario ingresado coincida con el usuario admin configurado. Si no coincide, retornamos False inmediatamente para evitar validaciones innecesarias.
    if usuario != admin_username:
        return False

    if admin_password_hash:
        return check_password_hash(admin_password_hash, password)

    if admin_password_plain:
        return compare_digest(admin_password_plain, password)

    return False

# Funciones auxiliares para manejo de intentos de login, generación de tokens CSRF, validación de credenciales, y construcción de eventos para el calendario.
def _redirect_login():
    flash("Debes iniciar sesiOn primero", "error")
    return redirect(url_for("login"))

# Funciones auxiliares para manejo de intentos de login, generación de tokens CSRF, validación de credenciales, y construcción de eventos para el calendario.
def _construir_eventos_calendario(citas):
    # FullCalendar espera una estructura simple por evento.
    eventos = []
    for cita in citas:
        eventos.append(
            {
                "title": f"{cita.cliente.nombre} {cita.cliente.apellido}",
                "start": cita.fecha_inicio.isoformat(),
                "end": cita.fecha_fin.isoformat(),
                "extendedProps": {
                    "servicios": [
                        f"{detalle.servicio.nombre_servicio} - ${detalle.precio_aplicado}"
                        for detalle in cita.detalles
                    ],
                    "notas": cita.notas,
                },
            }
        )
    return eventos


# Rutas publicas de navegacion.
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Rutas publicas de navegacion.
@app.route("/servicios", methods=["GET"])
def servicios():
    try:
        categorias = db_session.query(CategoriaServicio).all()
        servicios_lista = db_session.query(Servicio).all()
        return render_template(
            "servicios.html",
            categorias=categorias,
            servicios=servicios_lista,
        )
    except Exception as e:
        print(f"Error en /servicios: {e}")
        return f"Error al cargar el catalogo: {str(e)}", 500

# Rutas para calendario, autenticacion, registro y confirmacion de clientes y citas, historial y mantenimiento de citas.
@app.route("/calendario", methods=["GET"])
def calendario():
    try:
        clientes = db_session.query(Cliente).all()
        categorias = db_session.query(CategoriaServicio).all()
        servicios = db_session.query(Servicio).all()
        citas = db_session.query(Cita).filter(Cita.estado == "agendada").all()

        return render_template(
            "calendario.html",
            clientes=clientes,
            categorias=categorias,
            servicios=servicios,
            eventos=_construir_eventos_calendario(citas),
        )
    except Exception as e:
        return f"Error al cargar calendario: {str(e)}", 500


# Autenticacion de administracion
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        _validar_csrf()

        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")

        bloqueado, minutos_restantes = _login_bloqueado(usuario)
        if bloqueado:
            flash(
                f"Acceso bloqueado temporalmente. Intenta de nuevo en {minutos_restantes} minuto(s).",
                "error",
            )
            return render_template("login.html"), 429

        if _credenciales_admin_validas(usuario, password):
            session.clear()
            session["logueado"] = True
            session["usuario"] = usuario
            session.permanent = True
            session["_csrf_token"] = secrets.token_urlsafe(32)
            _limpiar_intentos_login(usuario)
            return redirect(url_for("historial"))

        _registrar_login_fallido(usuario)
        flash("Usuario o contraseNa incorrectos", "error")

    return render_template("login.html")

# Ruta para cerrar sesión, que limpia la sesión y redirige al login.
@app.route("/logout")
def logout():
    session.clear()
    flash("SesiOn cerrada correctamente", "success")
    return redirect(url_for("login"))


# Registro y confirmacion de clientes y citas
@app.route("/guardar_cliente", methods=["POST"])
def guardar_cliente():
    try:
        nuevo = Cliente(
            nombre=request.form.get("nombre"),
            apellido=request.form.get("apellido"),
            telefono=request.form.get("telefono"),
            email=request.form.get("email"),
        )
        db_session.add(nuevo)
        db_session.commit()
        flash("Cliente registrado con exito", "success")
        return redirect(url_for("calendario"))
    except Exception as e:
        db_session.rollback()
        flash(f"Error al registrar cliente: {str(e)}", "error")
        return redirect(url_for("calendario"))

# Registro y confirmacion de clientes y citas
@app.route("/guardar_cita", methods=["POST"])
def guardar_cita():
    # Para registrar una cita, primero validamos los datos ingresados, luego creamos o actualizamos el cliente según corresponda, validamos las reglas de negocio para la cita y servicios, guardamos la cita y sus detalles en la base de datos, generamos un token de confirmación y enviamos un correo al cliente con el enlace para confirmar su cita. Si ocurre algún error en el proceso, hacemos
    try:
        nombre = (request.form.get("nombre") or "").strip()
        apellido = (request.form.get("apellido") or "").strip()
        telefono = (request.form.get("telefono", "") or "").strip()
        email = (request.form.get("email") or "").strip()
        fecha_inicio = request.form.get("fecha_inicio")
        notas = request.form.get("notas", "")
        servicios_seleccionados = request.form.getlist("servicios")

# Validamos que se hayan ingresado los campos obligatorios de nombre, apellido y email. Si falta alguno, mostramos un error y redirigimos al calendario.
        if not nombre or not apellido or not email:
            flash("Debes ingresar nombre, apellido y correo", "error")
            return redirect(url_for("calendario"))

        # Validar que el email no esté registrado
        nombre_normalizado = nombre.lower()
        apellido_normalizado = apellido.lower()
        email_normalizado = email.lower()

# Buscamos si ya existe un cliente con el mismo email (ignorando mayúsculas) para evitar registros duplicados. Si el email ya existe pero el nombre o apellido no coinciden, mostramos un error indicando que el correo ya está registrado. Si el email existe y el nombre y apellido coinciden, permitimos actualizar los datos del cliente existente.
        cliente_existente = db_session.query(Cliente).filter(
            func.lower(Cliente.email) == email_normalizado
        ).first()
        if cliente_existente:
            mismo_nombre = (cliente_existente.nombre or "").strip().lower() == nombre_normalizado
            mismo_apellido = (cliente_existente.apellido or "").strip().lower() == apellido_normalizado

# Si el email ya existe pero el nombre o apellido no coinciden, mostramos un error indicando que el correo ya está registrado. Si el email existe y el nombre y apellido coinciden, permitimos actualizar los datos del cliente existente.
            if not (mismo_nombre and mismo_apellido):
                flash("Correo ya registrado, intenta con otro", "error")
                return redirect(url_for("calendario"))
# Si el email existe y el nombre y apellido coinciden, permitimos actualizar los datos del cliente existente.
            cliente_existente.nombre = nombre
            cliente_existente.apellido = apellido
            cliente_existente.telefono = telefono
            cliente_existente.email = email
            id_cliente = cliente_existente.id_cliente
# Si el email existe y el nombre y apellido coinciden, permitimos actualizar los datos del cliente existente.
        if not fecha_inicio:
            flash("Todos los campos obligatorios deben llenarse", "error")
            return redirect(url_for("calendario"))
# Validamos que se haya seleccionado al menos un servicio para la cita. Si no se selecciona ningún servicio, mostramos un error y redirigimos al calendario.
        if not servicios_seleccionados:
            flash("Debes seleccionar al menos un servicio", "error")
            return redirect(url_for("calendario"))
# Validamos que la fecha de inicio de la cita sea válida y esté dentro del horario permitido. Si no es válida o no está dentro del horario, mostramos un error y redirigimos al calendario.
        valido, mensaje = validar_dia_semana(fecha_inicio)
        if not valido:
            flash(mensaje, "error")
            return redirect(url_for("calendario"))
# Validamos que la fecha de inicio de la cita sea válida y esté dentro del horario permitido. Si no es válida o no está dentro del horario, mostramos un error y redirigimos al calendario.
        valido, mensaje = validar_horario_cita(fecha_inicio, None)
        if not valido:
            flash(mensaje, "error")
            return redirect(url_for("calendario"))
# Si el cliente no existe, lo creamos. Si el cliente ya existía, actualizamos sus datos con la información ingresada en el formulario.
        if not cliente_existente:
            nuevo_cliente = Cliente(
                nombre=nombre,
                apellido=apellido,
                telefono=telefono,
                email=email,
            )
            db_session.add(nuevo_cliente)
            db_session.flush()
            id_cliente = nuevo_cliente.id_cliente
# Validamos las reglas de negocio para la cita y servicios seleccionados, como máximo 3 servicios por día y máximo 1 servicio >90 minutos por día, considerando también las citas existentes del cliente. Si no se cumplen las reglas, mostramos un error y redirigimos al calendario.
        valido, mensaje = validar_servicios_por_dia(id_cliente, fecha_inicio, servicios_seleccionados)
        if not valido:
            flash(mensaje, "error")
            return redirect(url_for("calendario"))
# Calculamos la duración total de los servicios seleccionados para la cita, y con eso calculamos la fecha de fin de la cita. Esto nos permitirá validar el horario de la cita y también guardar correctamente el rango de tiempo que ocupa la cita en el calendario.
        duracion_total = calcular_duracion_servicios(servicios_seleccionados)
        fecha_fin = calcular_fecha_fin(fecha_inicio, duracion_total)
# Validamos que la cita no se solape con otra cita agendada en el mismo lapso de tiempo, considerando también la edición de citas existentes. Si hay un solapamiento, mostramos un error y redirigimos al calendario.
        valido, mensaje = validar_horario_cita(fecha_inicio, fecha_fin)
        if not valido:
            flash(mensaje, "error")
            return redirect(url_for("calendario"))
# Validamos que la cita no se solape con otra cita agendada en el mismo lapso de tiempo, considerando también la edición de citas existentes. Si hay un solapamiento, mostramos un error y redirigimos al calendario.
        valido, mensaje = validar_solapamiento(fecha_inicio, fecha_fin)
        if not valido:
            flash(mensaje, "error")
            return redirect(url_for("calendario"))
# Si todas las validaciones pasan, creamos la cita con estado "pendiente" y guardamos los detalles de la cita con los servicios seleccionados. Luego generamos un token de confirmación y enviamos un correo al cliente con el enlace para confirmar su cita. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un error y redirigimos al calendario.
        nueva_cita = Cita(
            id_cliente=id_cliente,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=EstadoCita.pendiente,
            notas=notas,
        )
        db_session.add(nueva_cita)
        db_session.commit()
# Guardamos los detalles de la cita con los servicios seleccionados, aplicando el precio actual de cada servicio. Esto nos permitirá tener un historial correcto de qué servicios se agendaron en cada cita y a qué precio, incluso si luego se cambian los precios de los servicios en el catálogo.
        for servicio_id in servicios_seleccionados:
            servicio = db_session.query(Servicio).get(int(servicio_id))
            detalle = DetalleCita(
                id_cita=nueva_cita.id_cita,
                id_servicio=servicio.id_servicio,
                precio_aplicado=servicio.precio,
            )
            db_session.add(detalle)
        db_session.commit()
# Generamos un token de confirmación para la cita recién creada, que incluye el ID de la cita y tiene una expiración de 15 minutos. Luego construimos el enlace de confirmación utilizando ese token, y enviamos un correo al cliente con el enlace para confirmar su cita. Si el correo se envía correctamente, mostramos un mensaje informando al cliente que revise su correo para confirmar la cita. Si hay un error al enviar el correo, mostramos un mensaje informando que la cita fue registrada pero hubo un error al enviar el correo, y sugerimos contactar soporte.
        token = serializer.dumps(str(nueva_cita.id_cita), salt="confirmar-cita")
        link = url_for("confirmar_cita", token=token, _external=True)

        cliente = db_session.query(Cliente).get(int(id_cliente))
        subject = "Confirma tu cita en Studio 02"
# Construimos el cuerpo del correo con un mensaje amigable que incluye los datos del cliente, un resumen de la cita y el enlace para confirmar. También informamos que el enlace expira en 15 minutos para incentivar al cliente a confirmar lo antes posible.
        body = f"""Hola {cliente.nombre},

Bienvenido a Studio 02. Tu perfil ha sido creado con los siguientes datos:

Nombre: {cliente.nombre} {cliente.apellido}
Correo: {cliente.email}
Teléfono: {cliente.telefono}

Para confirmar tu cita, haz clic en el siguiente enlace:
{link}

Este enlace expira en 15 minutos.

¡Gracias por confiar en Studio 02!"""

        email_enviado = send_email(cliente.email, subject, body)

        if email_enviado:
            flash(
                "Tu cita ha sido registrada como pendiente. Revisa tu correo para confirmarla.",
                "info",
            )
        else:
            flash(
                "Cita registrada, pero hubo error al enviar el correo. Contacta soporte.",
                "error",
            )
        return redirect(url_for("calendario"))
    except Exception as e:
        db_session.rollback()
        flash(f"Error al guardar la cita: {str(e)}", "error")
        return redirect(url_for("calendario"))


@app.route("/confirmar_cita/<token>")
def confirmar_cita(token):
    try:
        cita_id = serializer.loads(token, salt="confirmar-cita", max_age=900)
        cita = db_session.query(Cita).get(int(cita_id))

        if not cita:
            flash("Cita no encontrada", "error")
            return redirect(url_for("calendario"))

        cita.estado = EstadoCita.agendada
        db_session.commit()

        flash("Tu cita ha sido confirmada con exito", "success")
        return redirect(url_for("calendario"))
    except Exception as e:
        flash(f"Error al confirmar cita: {str(e)}", "error")
        return redirect(url_for("calendario"))


# Historial y mantenimiento de citas, incluyendo edición, cancelación y completado de citas, con validaciones de negocio para cada acción.
@app.route("/historial", methods=["GET"])
def historial():
    if not _usuario_logueado():
        return _redirect_login()
# Para mostrar el historial de citas, obtenemos todas las citas ordenadas por fecha de inicio descendente para mostrar primero las más recientes. Luego renderizamos la plantilla del historial pasando la lista de citas. Si ocurre algún error al cargar las citas, mostramos un mensaje de error.
    try:
        lista_citas = db_session.query(Cita).order_by(desc(Cita.fecha_inicio)).all()
        return render_template("historial.html", citas=lista_citas)
    except Exception as e:
        return f"Error al cargar el historial: {str(e)}", 500

# Para editar una cita, primero validamos que el usuario esté logueado. Luego buscamos la cita por su ID y si no la encontramos mostramos un error. Si la cita existe, renderizamos la plantilla de edición pasando los datos de la cita para que se puedan modificar. Si ocurre algún error al cargar la cita, mostramos un mensaje de error.
@app.route("/editar_cita/<int:id_cita>", methods=["GET"])
def editar_cita(id_cita):
    if not _usuario_logueado():
        return _redirect_login()
# Para editar una cita, primero validamos que el usuario esté logueado. Luego buscamos la cita por su ID y si no la encontramos mostramos un error. Si la cita existe, renderizamos la plantilla de edición pasando los datos de la cita para que se puedan modificar. Si ocurre algún error al cargar la cita, mostramos un mensaje de error.
    try:
        cita = db_session.query(Cita).get(id_cita)
        if not cita:
            flash("Cita no encontrada", "error")
            return redirect(url_for("historial"))

        return render_template("editar_cita.html", cita=cita)
    except Exception as e:
        flash(f"Error al cargar la cita: {str(e)}", "error")
        return redirect(url_for("historial"))

# Para actualizar una cita, primero validamos que el usuario esté logueado. Luego buscamos la cita por su ID y si no la encontramos mostramos un error. Si la cita existe, validamos los datos ingresados en el formulario, aplicamos las reglas de negocio para la cita y servicios, actualizamos la cita y sus detalles en la base de datos, y redirigimos al historial con un mensaje de éxito. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un mensaje de error y redirigimos a la edición de la cita.
@app.route("/actualizar_cita/<int:id_cita>", methods=["POST"])
def actualizar_cita(id_cita):
    if not _usuario_logueado():
        return _redirect_login()
# Para actualizar una cita, primero validamos que el usuario esté logueado. Luego buscamos la cita por su ID y si no la encontramos mostramos un error. Si la cita existe, validamos los datos ingresados en el formulario, aplicamos las reglas de negocio para la cita y servicios, actualizamos la cita y sus detalles en la base de datos, y redirigimos al historial con un mensaje de éxito. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un mensaje de error y redirigimos a la edición de la cita.
    try:
        cita = db_session.query(Cita).get(id_cita)
        if not cita:
            flash("Cita no encontrada", "error")
            return redirect(url_for("historial"))
#   Validamos los datos ingresados en el formulario, aplicamos las reglas de negocio para la cita y servicios, actualizamos la cita y sus detalles en la base de datos, y redirigimos al historial con un mensaje de éxito. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un mensaje de error y redirigimos a la edición de la cita.
        fecha_inicio = request.form.get("fecha_inicio")
        notas = request.form.get("notas", "")
#   Validamos que se haya ingresado la fecha de inicio de la cita. Si no se ingresa, mostramos un error y redirigimos a la edición de la cita.
        if not fecha_inicio:
            flash("El campo de fecha es obligatorio", "error")
            return redirect(url_for("editar_cita", id_cita=id_cita))
#   Validamos que la fecha de inicio de la cita sea válida y esté dentro del horario permitido. Si no es válida o no está dentro del horario, mostramos un error y redirigimos a la edición de la cita.
        valido, mensaje = validar_dia_semana(fecha_inicio)
        if not valido:
            flash(mensaje, "error")
            return redirect(url_for("editar_cita", id_cita=id_cita))
#   Validamos que la fecha de inicio de la cita sea válida y esté dentro del horario permitido. Si no es válida o no está dentro del horario, mostramos un error y redirigimos a la edición de la cita.
        servicios_ids = [detalle.id_servicio for detalle in cita.detalles]
        duracion_total = calcular_duracion_servicios(servicios_ids)
        fecha_fin = calcular_fecha_fin(fecha_inicio, duracion_total)
#   Validamos que la cita no se solape con otra cita agendada en el mismo lapso de tiempo, considerando también la edición de citas existentes. Si hay un solapamiento, mostramos un error y redirigimos a la edición de la cita.
        valido, mensaje = validar_horario_cita(fecha_inicio, fecha_fin)
        if not valido:
            flash(mensaje, "error")
            return redirect(url_for("editar_cita", id_cita=id_cita))
#   Validamos que la cita no se solape con otra cita agendada en el mismo lapso de tiempo, considerando también la edición de citas existentes. Si hay un solapamiento, mostramos un error y redirigimos a la edición de la cita.
        valido, mensaje = validar_solapamiento(fecha_inicio, fecha_fin, id_cita)
        if not valido:
            flash(mensaje, "error")
            return redirect(url_for("editar_cita", id_cita=id_cita))
#   Si todas las validaciones pasan, actualizamos la cita con la nueva fecha de inicio, fecha de fin y notas. Luego redirigimos al historial con un mensaje de éxito. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un mensaje de error y redirigimos a la edición de la cita.
        cita.fecha_inicio = fecha_inicio
        cita.fecha_fin = fecha_fin
        cita.notas = notas
        db_session.commit()
#   Si todas las validaciones pasan, actualizamos la cita con la nueva fecha de inicio, fecha de fin y notas. Luego redirigimos al historial con un mensaje de éxito. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un mensaje de error y redirigimos a la edición de la cita.
        flash("Cita actualizada correctamente", "success")
        return redirect(url_for("historial"))
    except Exception as e:
        db_session.rollback()
        flash(f"Error al actualizar la cita: {str(e)}", "error")
        return redirect(url_for("editar_cita", id_cita=id_cita))

# Ruta API para validar la disponibilidad de un horario para una cita, considerando las reglas de negocio para servicios por día, duración de servicios, y solapamiento de citas. Esta ruta se puede consumir desde el frontend para validar en tiempo real si el horario seleccionado es válido antes de enviar el formulario de registro o edición de cita.
@app.route("/api/validar_disponibilidad", methods=["POST"])
def api_validar_disponibilidad():
    try:
        data = request.get_json()
        fecha_inicio = data.get("fecha_inicio")
        servicios_ids = data.get("servicios", [])
        id_cliente = data.get("id_cliente")
        id_cita_actual = data.get("id_cita")

        valido, mensaje = validar_dia_semana(fecha_inicio)
        if not valido:
            return jsonify({"disponible": False, "mensaje": mensaje})

        duracion_total = calcular_duracion_servicios(servicios_ids)
        fecha_fin = calcular_fecha_fin(fecha_inicio, duracion_total)

        valido, mensaje = validar_horario_cita(fecha_inicio, fecha_fin)
        if not valido:
            return jsonify({"disponible": False, "mensaje": mensaje})

        if id_cliente and servicios_ids:
            valido, mensaje = validar_servicios_por_dia(id_cliente, fecha_inicio, servicios_ids, id_cita_actual)
            if not valido:
                return jsonify({"disponible": False, "mensaje": mensaje})

        valido, mensaje = validar_solapamiento(fecha_inicio, fecha_fin, id_cita_actual)
        if not valido:
            return jsonify({"disponible": False, "mensaje": mensaje})

        return jsonify({"disponible": True, "mensaje": "Horario disponible", "duracion": duracion_total, "fecha_fin": fecha_fin.isoformat()})
    except Exception as e:
        return jsonify({"disponible": False, "mensaje": f"Error: {str(e)}"}), 500

# Rutas para cancelar, completar o marcar como no asistio una cita desde el historial, con validaciones de negocio para cada acción. Solo las citas agendadas pueden ser canceladas, completadas o marcadas como no asistio. Si la cita no existe o no está en estado agendada, mostramos un error.
@app.route("/cancelar_cita/<int:id_cita>", methods=["POST"])
def cancelar_cita(id_cita):
    if not _usuario_logueado():
        return _redirect_login()
# Para cancelar una cita, primero validamos que el usuario esté logueado. Luego buscamos la cita por su ID y si no la encontramos mostramos un error. Si la cita existe, validamos que esté en estado agendada para permitir su cancelación. Si la cita está en estado agendada, actualizamos su estado a cancelada y redirigimos al historial con un mensaje de éxito. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un mensaje de error y redirigimos al historial.
    try:
        cita = db_session.query(Cita).get(id_cita)
        if not cita:
            flash("Cita no encontrada", "error")
            return redirect(url_for("historial"))

        cita.estado = EstadoCita.cancelada
        db_session.commit()

        flash("Cita cancelada correctamente", "success")
        return redirect(url_for("historial"))
    except Exception as e:
        db_session.rollback()
        flash(f"Error al cancelar la cita: {str(e)}", "error")
        return redirect(url_for("historial"))

# Para completar una cita, primero validamos que el usuario esté logueado. Luego buscamos la cita por su ID y si no la encontramos mostramos un error. Si la cita existe, validamos que esté en estado agendada para permitir marcarla como completada. Si la cita está en estado agendada, actualizamos su estado a completada y redirigimos al historial con un mensaje de éxito. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un mensaje de error y redirigimos al historial.
@app.route("/completar_cita/<int:id_cita>", methods=["POST"])
def completar_cita(id_cita):
    if not _usuario_logueado():
        return _redirect_login()
# Para completar una cita, primero validamos que el usuario esté logueado. Luego buscamos la cita por su ID y si no la encontramos mostramos un error. Si la cita existe, validamos que esté en estado agendada para permitir marcarla como completada. Si la cita está en estado agendada, actualizamos su estado a completada y redirigimos al historial con un mensaje de éxito. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un mensaje de error y redirigimos al historial.
    try:
        cita = db_session.query(Cita).get(id_cita)
        if not cita:
            flash("Cita no encontrada", "error")
            return redirect(url_for("historial"))

        if cita.estado != EstadoCita.agendada:
            flash("Solo las citas agendadas pueden marcarse como completadas", "error")
            return redirect(url_for("historial"))

        cita.estado = EstadoCita.completada
        db_session.commit()

        flash("Cita marcada como completada", "success")
        return redirect(url_for("historial"))
    except Exception as e:
        db_session.rollback()
        flash(f"Error al marcar la cita como completada: {str(e)}", "error")
        return redirect(url_for("historial"))

# Para marcar una cita como no asistio, primero validamos que el usuario esté logueado. Luego buscamos la cita por su ID y si no la encontramos mostramos un error. Si la cita existe, validamos que esté en estado agendada para permitir marcarla como no asistio. Si la cita está en estado agendada, actualizamos su estado a no asistio y redirigimos al historial con un mensaje de éxito. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un mensaje de error y redirigimos al historial.
@app.route("/marcar_no_asistio/<int:id_cita>", methods=["POST"])
def marcar_no_asistio(id_cita):
    if not _usuario_logueado():
        return _redirect_login()
# Para marcar una cita como no asistio, primero validamos que el usuario esté logueado. Luego buscamos la cita por su ID y si no la encontramos mostramos un error. Si la cita existe, validamos que esté en estado agendada para permitir marcarla como no asistio. Si la cita está en estado agendada, actualizamos su estado a no asistio y redirigimos al historial con un mensaje de éxito. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un mensaje de error y redirigimos al historial.
    try:
        cita = db_session.query(Cita).get(id_cita)
        if not cita:
            flash("Cita no encontrada", "error")
            return redirect(url_for("historial"))
# Para marcar una cita como no asistio, primero validamos que el usuario esté logueado. Luego buscamos la cita por su ID y si no la encontramos mostramos un error. Si la cita existe, validamos que esté en estado agendada para permitir marcarla como no asistio. Si la cita está en estado agendada, actualizamos su estado a no asistio y redirigimos al historial con un mensaje de éxito. Si ocurre algún error en el proceso, hacemos rollback de la base de datos, mostramos un mensaje de error y redirigimos al historial.
        if cita.estado != EstadoCita.agendada:
            flash("Solo las citas agendadas pueden marcarse como no asistio", "error")
            return redirect(url_for("historial"))

        cita.estado = EstadoCita.no_asistio
        db_session.commit()

        flash("Cita marcada como no asistio", "success")
        return redirect(url_for("historial"))
    except Exception as e:
        db_session.rollback()
        flash(f"Error al marcar la cita como no asistio: {str(e)}", "error")
        return redirect(url_for("historial"))
    
# esto nomas era para validar rapido la conexion de la db, no es parte de la app ni nada, asi que lo dejo comentado por si se necesita en algun momento hacer pruebas rapidas de conexion a la db sin tener que pasar por el login y todo eso.
"""""
# Ruta auxiliar para validar rapidamente la conexion.
@app.route("/test-db")
def test_db():
    db = db_session()
    try:
        clientes = db.query(Cliente).all()
        resultado = [
            {
                "id_cliente": cliente.id_cliente,
                "nombre": cliente.nombre,
                "apellido": cliente.apellido,
                "telefono": cliente.telefono,
                "email": cliente.email,
            }
            for cliente in clientes
        ]
        return jsonify(
            {
                "status": "ok",
                "mensaje": "Conexion a la base de datos exitosa",
                "total": len(resultado),
                "clientes": resultado,
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500
    finally:
        db.close()
"""
#Recordar cambiar el host
#poner el debug en false
if __name__ == "__main__":
    app.run(host="192.168.1.74", port=8080, debug=True)