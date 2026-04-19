document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    const serviceSelect = document.querySelector('select[name="servicio"]');
    const dateInput = document.getElementById('selected-date');

    // Lógica para capturar el servicio desde la URL
    const urlParams = new URLSearchParams(window.location.search);
    const servicioSeleccionado = urlParams.get('servicio');
    if (servicioSeleccionado && serviceSelect) {
        serviceSelect.value = servicioSeleccionado;
    }

    // Inicialización de FullCalendar
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        locale: 'es',
        slotMinTime: '09:00:00',
        slotMaxTime: '20:00:00',
        allDaySlot: false,
        selectable: true,
        editable: false,
        height: 'auto', // Ayuda a que se adapte mejor a la tarjeta blanca
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        buttonText: {
            today: 'Hoy',
            month: 'Mes',
            week: 'Semana',
            day: 'Día'
        },
        // Al seleccionar un horario disponible
        select: function(info) {
            // Formatear la fecha para que sea legible en el input de la izquierda
            dateInput.value = info.startStr.replace('T', ' ').substring(0, 16);
            
            // Efecto visual: Resalta el borde del input para indicarle al usuario que se llenó
            dateInput.style.borderColor = "#6a5ca2";
            dateInput.style.backgroundColor = "#f8efed";
            setTimeout(() => {
                dateInput.style.borderColor = "#ddd";
                dateInput.style.backgroundColor = "transparent";
            }, 800);
        },
        // Origen de datos para citas ya agendadas (JSON desde Flask/MySQL)
        events: '/get_citas' 
    });

    calendar.render();
});