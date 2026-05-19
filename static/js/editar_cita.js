// input de fecha
const fechaInicio = document.getElementById('fecha_inicio');
// contenedor del error
const errorInicio = document.getElementById('error-inicio');
// boton submit
const submitBtn = document.getElementById('submitBtn');
// formulario
const form = document.getElementById('editForm');
// datos enviados desde html
const citaId = citaData.citaId;
const servicios = citaData.servicios;
const apiUrl = citaData.apiUrl;
// validar disponibilidad
async function validarDisponibilidad() {
    // fecha seleccionada
    const inicio = fechaInicio.value;
    // si no hay fecha salir
    if (!inicio) return true;
    try {
        // request al backend
        const response = await fetch(apiUrl, {

            method: 'POST',

            headers: {
                'Content-Type': 'application/json'
            },

            body: JSON.stringify({

                fecha_inicio: inicio,

                servicios: servicios,

                id_cita: citaId

            })
        });
        // convertir respuesta
        const data = await response.json();
        // si no disponible mostrar error
        if (!data.disponible) {
            errorInicio.textContent = data.mensaje;
            errorInicio.classList.add('show');
            fechaInicio.classList.add('input-invalid');
            submitBtn.disabled = true;
            return false;
        } else {
            // limpiar errores
            errorInicio.classList.remove('show');
            fechaInicio.classList.remove('input-invalid');
            submitBtn.disabled = false;
            return true;
        }
    } catch (error) {
        console.error('Error:', error);
        return true;
    }
}

// validar al cambiar fecha
fechaInicio.addEventListener(

    'change',

    validarDisponibilidad

);


// validar antes de enviar
form.addEventListener(
    'submit',
    async (e) => {
        e.preventDefault();
        const esValido = await validarDisponibilidad();
        if (esValido) {
            form.submit();
        }
    });

// validacion inicial
validarDisponibilidad();