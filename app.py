from flask import Flask, render_template, request, redirect, url_for, jsonify
from DAO.db import db_session
from sqlalchemy import desc

# Importar todos los modelos juntos para que SQLAlchemy
# resuelva las relaciones entre clases antes de cualquier consulta
import Entities
from Entities.Citas import Cita
from Entities.Cliente import Cliente
from Entities.CategoriaServicio import CategoriaServicio
from Entities.Servicios import Servicio
from Entities.DetalleCita import DetalleCita
app = Flask(__name__)


# --- Configuración de Sesión ---
@app.teardown_appcontext
def shutdown_session(exception=None):
    """Cierra la sesión de base de datos al finalizar cada petición."""
    db_session.remove()


# --- Rutas de Navegación ---
@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")


@app.route('/servicios', methods=["GET"])
def servicios():
    try:
        # Obtenemos todas las categorías para los botones de filtro
        categorias = db_session.query(CategoriaServicio).all()
        
        # Obtenemos todos los servicios para el catálogo
        servicios_lista = db_session.query(Servicio).all()
        
        # Pasamos los datos al template
        return render_template("servicios.html", 
                               categorias=categorias, 
                               servicios=servicios_lista)
    except Exception as e:
        # Si algo falla, es mejor saber qué es
        print(f"Error en /servicios: {e}")
        return f"Error al cargar el catálogo: {str(e)}", 500


@app.route('/calendario', methods=["GET"])
def calendario():
    return render_template("calendario.html")


# --- Lógica del Historial ---
@app.route('/historial', methods=["GET"])
def historial():
    """Consulta todas las citas ordenadas por fecha reciente."""
    try:
        # Usamos fecha_inicio (fue renombrada desde 'fecha' en la migración)
        lista_citas = db_session.query(Cita).order_by(desc(Cita.fecha_inicio)).all()
        return render_template('historial.html', citas=lista_citas)
    except Exception as e:
        return f"Error al cargar el historial: {str(e)}", 500


# --- Guardar nueva cita ---
@app.route('/guardar_cita', methods=["POST"])
def guardar_cita():
    try:
        id_cliente   = request.form.get('id_cliente')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin    = request.form.get('fecha_fin')
        notas        = request.form.get('notas', '')

        nueva_cita = Cita(
            id_cliente   = id_cliente,
            fecha_inicio = fecha_inicio,
            fecha_fin    = fecha_fin,
            estado       = 'agendada',
            notas        = notas
        )

        db_session.add(nueva_cita)
        db_session.commit()

        return redirect(url_for('historial'))

    except Exception as e:
        db_session.rollback()
        return f"Error al guardar la cita: {str(e)}", 500

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
        return jsonify({
            "status":  "error",
            "mensaje": str(e)
        }), 500

    finally:
        db.close()


if __name__ == "__main__":
    app.run(debug=True)