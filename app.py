from flask import Flask, flash, render_template, request, redirect, url_for, jsonify
from itsdangerous import URLSafeTimedSerializer
from DAO.db import db_session
from sqlalchemy import desc
import Entities
from Entities.Citas import Cita
from Entities.Cliente import Cliente
from Entities.CategoriaServicio import CategoriaServicio
from Entities.Servicios import Servicio
from Entities.DetalleCita import DetalleCita
from config_email import send_email

app = Flask(__name__)
app.secret_key = "21"  # clave pq si no nos peta el programa

# --- Configuración de Sesión ---
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# --- Rutas de Navegación ---
@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")

@app.route('/servicios', methods=["GET"])
def servicios():
    try:
        categorias = db_session.query(CategoriaServicio).all()
        servicios_lista = db_session.query(Servicio).all()
        return render_template("servicios.html", categorias=categorias, servicios=servicios_lista)
    except Exception as e:
        print(f"Error en /servicios: {e}")
        return f"Error al cargar el catálogo: {str(e)}", 500

@app.route('/calendario', methods=["GET"])
def calendario():
    try:
        clientes = db_session.query(Cliente).all()
        categorias = db_session.query(CategoriaServicio).all()
        servicios = db_session.query(Servicio).all()
        citas = db_session.query(Cita).filter(Cita.estado == 'agendada').all()

        # Convertir citas a eventos para FullCalendar
        eventos = []
        for c in citas:
            eventos.append({
                "title": f"{c.cliente.nombre} {c.cliente.apellido}",
                "start": c.fecha_inicio.isoformat(),
                "end": c.fecha_fin.isoformat(),
                "extendedProps": {
                    "servicios": [f"{d.servicio.nombre_servicio} - ${d.precio_aplicado}" for d in c.detalles],
                    "notas": c.notas
                }
            })

        return render_template(
            "calendario.html",
            clientes=clientes,
            categorias=categorias,
            servicios=servicios,
            eventos=eventos
        )
    except Exception as e:
        return f"Error al cargar calendario: {str(e)}", 500

# --- Lógica del Historial ---
@app.route('/historial', methods=["GET"])
def historial():
    try:
        lista_citas = db_session.query(Cita).order_by(desc(Cita.fecha_inicio)).all()
        return render_template('historial.html', citas=lista_citas)
    except Exception as e:
        return f"Error al cargar el historial: {str(e)}", 500
    
    
serializer = URLSafeTimedSerializer("CLAVE_SECRETA_SUPERSEGURA")
@app.route('/guardar_cliente', methods=["POST"])
def guardar_cliente():
    try:
        nuevo = Cliente(
            nombre   = request.form.get('nombre'),
            apellido = request.form.get('apellido'),
            telefono = request.form.get('telefono'),
            email    = request.form.get('email')
        )
        db_session.add(nuevo)
        db_session.commit()
        flash("Cliente registrado con éxito", "success")
        return redirect(url_for('calendario'))
    except Exception as e:
        db_session.rollback()
        flash(f"Error al registrar cliente: {str(e)}", "error")
        return redirect(url_for('calendario'))

@app.route('/guardar_cita', methods=["POST"])
def guardar_cita():
    try:
        id_cliente   = request.form.get('id_cliente')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin    = request.form.get('fecha_fin')
        notas        = request.form.get('notas', '')

        if not id_cliente or not fecha_inicio or not fecha_fin:
            flash("Todos los campos obligatorios deben llenarse", "error")
            return redirect(url_for('calendario'))

        # Guardar cita como pendiente
        nueva_cita = Cita(
            id_cliente   = id_cliente,
            fecha_inicio = fecha_inicio,
            fecha_fin    = fecha_fin,
            estado       = 'pendiente',
            notas        = notas
        )
        db_session.add(nueva_cita)
        db_session.commit()

        # Guardar servicios seleccionados, o algo asi
        servicios_seleccionados = request.form.getlist('servicios')
        for s in servicios_seleccionados:
            servicio = db_session.query(Servicio).get(int(s))
            detalle = DetalleCita(
                id_cita        = nueva_cita.id_cita,
                id_servicio    = servicio.id_servicio,
                precio_aplicado = servicio.precio
            )
            db_session.add(detalle)
        db_session.commit()

        # Generar token de verificación
        token = serializer.dumps(str(nueva_cita.id_cita), salt="confirmar-cita")
        link = url_for("confirmar_cita", token=token, _external=True)

        # Enviar correo
        cliente = db_session.query(Cliente).get(int(id_cliente))
        subject = "Confirma tu cita en Studio 02"
        body = f"Hola {cliente.nombre}, confirma tu cita haciendo clic en este enlace:\n{link}"
        send_email(cliente.email, subject, body)

        # Mensaje!!!!!!!!!!!!!!!!!!!!!!!
        flash("Tu cita ha sido registrada como pendiente. Revisa tu correo para confirmarla.", "info")
        return redirect(url_for('calendario'))

    except Exception as e:
        db_session.rollback()
        flash(f"Error al guardar la cita: {str(e)}", "error")
        return redirect(url_for('calendario'))
    
@app.route('/confirmar_cita/<token>')
def confirmar_cita(token):
    try:
        # Validar token (expira en 1 hora por ejemplo, el max_age es modificable pero 3600 es lo normal
        cita_id = serializer.loads(token, salt="confirmar-cita", max_age=3600)
        cita = db_session.query(Cita).get(int(cita_id))

        if not cita:
            flash("Cita no encontrada", "error")
            return redirect(url_for("calendario"))

        # Cambiar estado a agendada
        cita.estado = "agendada"
        db_session.commit()

        flash("Tu cita ha sido confirmada con éxito", "success")
        return redirect(url_for("calendario"))

    except Exception as e:
        flash(f"Error al confirmar cita: {str(e)}", "error")
        return redirect(url_for("calendario"))


@app.route('/test-db')
def test_db():
    db = db_session()
    try:
        clientes = db.query(Cliente).all()
        resultado = [
            {
                "id_cliente": c.id_cliente,
                "nombre":     c.nombre,
                "apellido":   c.apellido,
                "telefono":   c.telefono,
                "email":      c.email,
            }
            for c in clientes
        ]
        return jsonify({
            "status":   "ok",
            "mensaje":  "Conexión a la base de datos exitosa",
            "total":    len(resultado),
            "clientes": resultado
        })
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500
    finally:
        db.close()

if __name__ == "__main__":
    app.run(debug=True)
