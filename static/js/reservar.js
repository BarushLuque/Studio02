// esperar carga completa
document.addEventListener('DOMContentLoaded', function () {

    // calendario
    const calendarEl = document.getElementById('calendar');

    // eventos enviados desde flask
    const eventosServer = reservaConfig.eventos || [];

    // crear calendario
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        locale: 'es',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        slotMinTime: '10:00:00',
        slotMaxTime: '22:00:00',
        allDaySlot: false,
        selectable: true,
        events: eventosServer,
        selectConstraint: 'businessHours',
        businessHours: [
            {
                daysOfWeek: [1, 2, 3, 4, 5],
                startTime: '10:00',
                endTime: '22:00'
            }
        ],
        // click en evento
        eventClick: function(info) {
            const servicios =
                (info.event.extendedProps &&
                 info.event.extendedProps.servicios) || [];
            const notas =
                (info.event.extendedProps &&
                 info.event.extendedProps.notas) || '';
            let msg = "Cliente: " + info.event.title + "\n\n";
            if (servicios.length) {
                msg += "Servicios:\n- " +
                       servicios.join("\n- ") + "\n\n";
            }
            msg += "Notas: " + (notas || "N/A");
            alert(msg);
        },
        // seleccionar fecha
        select: function(info) {
            const toLocal = function(date) {
                const off = date.getTimezoneOffset();
                const local =
                    new Date(date.getTime() - off * 60000);
                return local.toISOString().slice(0, 16);
            };
            document.getElementById('fecha_inicio').value =
                toLocal(info.start);
            validarDisponibilidad();
        }
    });
    // renderizar calendario
    calendar.render();
    // elementos del formulario
    const fechaInicio = document.getElementById('fecha_inicio');
    const errorInicio = document.getElementById('error-inicio');
    const duracionInfo = document.getElementById('duracion-info');
    const form = document.getElementById('appointment-form');
    const submitBtn =
        form.querySelector('button[type="submit"]');
    const serviciosCheckboxes =
        form.querySelectorAll('input[name="servicios"]');
    // obtener servicios seleccionados
    function obtenerServiciosSeleccionados() {
        return Array.from(serviciosCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
    }
    // actualizar texto de duracion
    function actualizarDuracion() {
        const servicios =
            obtenerServiciosSeleccionados();
        if (servicios.length === 0) {
            duracionInfo.textContent =
                'Selecciona servicios para ver la duración';
            return;
        }
        if (servicios.length > 3) {
            duracionInfo.textContent =
                'Maximo 3 servicios por dia';
            duracionInfo.style.color = '#d32f2f';
            return;
        }
        duracionInfo.textContent =
            `Servicios: ${servicios.length} seleccionados`;
        duracionInfo.style.color = 'var(--muted)';
    }
    // validar disponibilidad
    async function validarDisponibilidad() {
        const inicio = fechaInicio.value;
        const servicios =
            obtenerServiciosSeleccionados();
        if (!inicio || servicios.length === 0)
            return true;
        try {
            const response = await fetch(
                reservaConfig.apiUrl,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        fecha_inicio: inicio,
                        servicios: servicios
                    })
                }
            );
            const data = await response.json();
            // si no disponible
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

    // cambio de fecha
    fechaInicio.addEventListener(
        'change',
        validarDisponibilidad

    );

    // cambios en checkboxes
    serviciosCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {

            actualizarDuracion();

            validarDisponibilidad();
        });

    });

    // validar antes de submit
    form.addEventListener(

        'submit',
        async (e) => {
            e.preventDefault();

            const esValido =
                await validarDisponibilidad();

            if (esValido) {

                form.submit();
            }

        }

    );

    // iniciar texto
    actualizarDuracion();

});