# Studio 02

## 1. Que es este proyecto

Este proyecto es una app web para un estudio de belleza.

La idea principal es muy clara. Una clienta entra, revisa servicios, agenda una cita, confirma esa cita por correo y despues el area admin puede revisar el historial y mover el estado de cada reserva.

No es una pagina solo de presentacion. Aqui ya hay una mezcla de catalogo, agenda, validaciones, login para administracion, historial y envio de correo.

## 2. Como esta armado

El proyecto esta dividido en partes que se entienden bastante bien cuando las ves por carpeta.

`app.py`

Aqui vive casi toda la logica principal. Desde este archivo se levantan las rutas, se validan horarios, se confirma si una cita se puede guardar, se protege el login y se controla el flujo general de la app.

`DAO`

Aqui esta la conexion con la base de datos usando SQLAlchemy. Es la capa que deja lista la sesion para consultar, guardar y actualizar datos.

`Entities`

Aqui estan los modelos. En esta carpeta se define como se ven clientes, citas, detalles de cita, servicios y categorias de servicio.

`templates`

Aqui estan las vistas HTML. Esta carpeta trae la pagina de inicio, la pagina de servicios, la vista para reservar, el login, el historial admin y la pantalla para editar una cita.

`static`

Aqui esta la parte visual y de apoyo. Trae estilos, imagenes, manifest para modo instalable y el service worker.

`studio`

Esta carpeta es el entorno virtual del proyecto. Basicamente guarda Python y las librerias instaladas.

## 3. Que hace la app de inicio a fin

El flujo real del proyecto se mueve asi.

1. La persona entra a la pagina principal y ve una landing con imagenes, texto de marca y accesos a servicios o reservas.

2. Si quiere ver el catalogo entra a la vista de servicios, donde el sistema trae categorias y servicios desde la base de datos.

3. Si quiere reservar entra a la vista de calendario. Ahi llena su nombre, apellido, telefono, correo, fecha y servicios.

4. Antes de guardar, la app revisa varias cosas. Revisa que haya datos obligatorios, que el dia no sea sabado o domingo, que el horario este dentro de la ventana permitida, que no se pasen de servicios por dia y que no se pise con otra cita.

5. Si todo sale bien, la cita se guarda primero como pendiente.

6. Luego se genera un enlace temporal de confirmacion y se manda por correo.

7. Cuando la clienta abre ese enlace, la cita cambia de pendiente a agendada.

8. Del lado admin se puede entrar al historial para revisar todas las citas, editar fechas, cancelar, completar o marcar no asistio.

## 4. Backend explicado sin rollo

### 4.1 Arranque general

La app usa Flask como framework principal.

Al arrancar hace estas cosas.

1. Carga variables de entorno.

2. Configura la llave secreta de sesion.

3. Define cuanto dura una sesion.

4. Ajusta banderas de seguridad para cookies.

5. Crea un serializador para tokens temporales de confirmacion.

6. Define limites para intentos de login.

## 5. Reglas del negocio que ya trae

Esta parte es de las mas importantes porque aqui se ve que el proyecto no solo pinta bonito, tambien piensa antes de guardar.

### 5.1 Horario permitido

Las citas solo se permiten dentro del rango de 10 de la manana a 10 de la noche.

Si una cita empieza antes o termina despues de ese rango, se rechaza.

### 5.2 Dias disponibles

No se permiten citas en sabado ni domingo.

### 5.3 Cantidad maxima de servicios por dia

Una misma clienta no puede tener mas de 3 servicios en el mismo dia.

### 5.4 Servicios largos por dia

Solo se permite 1 servicio mayor a 90 minutos por dia para una misma clienta.

### 5.5 Solapamiento de agenda

No se puede guardar una cita si se cruza en tiempo con otra cita ya agendada.

Esto evita que dos personas queden montadas en el mismo bloque de horario.

## 6. Seguridad que ya existe

La app trae varias cosas buenas en seguridad.

### 6.1 Sesiones protegidas

Cuando el admin inicia sesion, Flask guarda el estado de acceso en sesion y marca la sesion como permanente por el tiempo definido.

### 6.2 Token CSRF

Se genera un token para formularios sensibles y se valida en el login.

### 6.3 Limite de intentos de login

Si alguien falla muchas veces con el mismo usuario desde la misma direccion, se bloquea por unos minutos.

### 6.4 Encabezados de seguridad

La respuesta agrega protecciones para evitar cosas como contenido mal interpretado o embebido raro en otros sitios.

### 6.5 Cache desactivado en zonas sensibles

Las pantallas privadas o de sesion evitan cache para no dejar datos expuestos en navegador.

## 7. Rutas y comportamiento real

Aqui va la parte que explica que hace cada pantalla o accion.

### 7.1 Inicio

Muestra la landing principal del negocio.

Su funcion es presentar la marca y llevar a servicios o reservas.

### 7.2 Servicios

Consulta categorias y servicios desde la base de datos y pinta el catalogo agrupado.

### 7.3 Calendario

Carga clientes, categorias, servicios y citas activas.

Con eso renderiza la vista para reservar y tambien el calendario visual con eventos ya agendados.

### 7.4 Login admin

Sirve para entrar al panel privado.

Si el usuario y la clave son correctos, se abre sesion y manda al historial.

Si no, registra intento fallido y puede bloquear temporalmente.

### 7.5 Cerrar sesion

Limpia por completo la sesion actual y regresa al login.

### 7.6 Guardar cliente

Crea un cliente directo desde formulario y lo guarda en base de datos.

### 7.7 Guardar cita

Esta es de las rutas mas completas del proyecto.

Hace todo esto.

1. Lee datos del formulario.

2. Valida nombre, apellido y correo.

3. Revisa si el correo ya existe.

4. Si el correo existe con el mismo nombre y apellido, actualiza datos del cliente y reutiliza su registro.

5. Si el correo existe pero pertenece a otra persona, rechaza el intento.

6. Valida que haya fecha.

7. Valida que haya al menos un servicio.

8. Valida dia permitido.

9. Valida horario permitido.

10. Si la clienta no existia, la crea.

11. Valida limite de servicios por dia.

12. Calcula duracion total.

13. Calcula fecha de fin.

14. Revisa que no se salga del horario.

15. Revisa que no se cruce con otra cita.

16. Guarda la cita en estado pendiente.

17. Guarda el detalle de cada servicio elegido.

18. Genera un token temporal.

19. Manda correo de confirmacion.

### 7.8 Confirmar cita

Recibe un token, lo valida por tiempo y cambia la cita a estado agendada.

El enlace expira en 15 minutos.

### 7.9 Historial

Es la vista admin donde se listan todas las citas ordenadas por fecha de inicio en orden descendente.

Aqui se puede ver cliente, rango de tiempo, servicios, notas, estado y acciones disponibles.

### 7.10 Editar cita

Abre una vista para cambiar la fecha y hora de una cita existente.

No cambia los servicios. Solo mueve el horario y conserva la duracion total ya calculada por los servicios que tiene esa cita.

### 7.11 Actualizar cita

Toma la nueva fecha, recalcula la hora final segun la duracion acumulada de sus servicios y vuelve a pasar por validaciones de dia, horario y cruce con otras citas.

### 7.12 API de disponibilidad

Esta parte le da vida al frontend.

Recibe una fecha y una lista de servicios. Luego responde si ese bloque esta libre o no.

Tambien devuelve la duracion total y la fecha final calculada cuando todo esta bien.

### 7.13 Cancelar cita

Cambia el estado de una cita a cancelada.

### 7.14 Completar cita

Solo deja completar citas que ya estan agendadas.

### 7.15 Marcar no asistio

Solo deja marcar no asistio si la cita estaba agendada.

## 8. Modelos de datos

La base del proyecto gira alrededor de 5 modelos.

### 8.1 Categoria de servicio

Guarda la categoria general.

Ejemplos claros pueden ser cabello, facial, maquillaje o manicura.

Una categoria puede tener muchos servicios.

### 8.2 Servicio

Guarda el nombre del servicio, precio, duracion en minutos y a que categoria pertenece.

Un servicio puede aparecer muchas veces dentro de detalles de cita.

### 8.3 Cliente

Guarda nombre, apellido, telefono, correo, notas y fecha de registro.

El correo es unico, asi que no se repite entre personas distintas.

Un cliente puede tener muchas citas.

### 8.4 Cita

Guarda quien es la clienta, cuando empieza, cuando termina, en que estado va y notas extra.

Tambien conecta con la lista de detalles que dicen que servicios se incluyeron.

Los estados que maneja el sistema son pendiente, agendada, completada, cancelada y no asistio.

### 8.5 Detalle de cita

Esta tabla es la union entre cita y servicio.

Sirve para guardar que servicios forman parte de una cita y con que precio quedaron aplicados.

## 9. Vistas del proyecto

### 9.1 Vista principal

La pagina principal esta pensada como landing elegante.

Trae navbar, hero, seccion de destacados, bloque sobre el estudio y cierre con llamada a reservar.

El objetivo de esta vista es vender la experiencia y empujar hacia la reserva.

### 9.2 Vista de servicios

Esta vista funciona como catalogo visual.

Agrupa servicios por categoria, les pone imagen, duracion y precio. Tambien deja filtrar por categoria sin recargar toda la pagina.

### 9.3 Vista de calendario y reserva

Aqui esta el corazon del sistema.

Del lado izquierdo vive el formulario de reserva.

Del lado derecho vive FullCalendar con la agenda visible.

Cuando una persona selecciona fecha o servicios, el frontend consulta disponibilidad en tiempo real para avisar si ese horario sirve o no.

### 9.4 Vista de login

Es la entrada al panel privado. Tiene un estilo separado del resto para marcar mejor la zona admin.

### 9.5 Vista de historial

Es la tabla admin donde se revisa todo el movimiento de citas.

Desde aqui se concentran casi todas las acciones de seguimiento.

### 9.6 Vista de editar

Es una pantalla chica pero importante. Sirve para mover una cita ya creada sin tocar el resto de sus datos principales.

## 10. Frontend y experiencia

La parte visual del proyecto mezcla una estetica boutique con una navegacion bastante directa.

### 10.1 Estilos

Hay una hoja global con colores crema, tinta y tonos calidos.

La tipografia combina una fuente serif elegante con una sans mas limpia para equilibrar marca y legibilidad.

### 10.2 Calendario visual

La agenda se pinta con FullCalendar.

Se usa vista semanal por defecto y se restringen horarios a dias habiles entre 10 y 22 horas.

### 10.3 Validacion en vivo

Cuando cambias fecha o seleccionas servicios, el frontend consulta al backend para saber si el horario esta libre.

Eso evita que la persona mande el formulario a ciegas.

### 10.4 Manifest y service worker

El proyecto ya trae base para sentirse medio instalable.

Tiene manifest y service worker, asi que ya existe una intencion de modo app o experiencia mas parecida a una mini PWA.

## 11. Correo y confirmacion

El modulo de correo usa SMTP.

Su trabajo es mandar el mensaje de confirmacion apenas se registra una cita nueva.

El cuerpo del correo le dice a la clienta que su perfil fue creado, le recuerda sus datos y le pasa el enlace para confirmar.

Si el correo no esta bien configurado, la funcion avisa por consola y devuelve fallo.

## 12. Conexion a base de datos

La app esta apuntando a MySQL con PyMySQL.

Se crea un engine y una sesion compartida por peticion usando SQLAlchemy.

Eso deja el acceso a base de datos listo para consultar y persistir datos desde cualquier ruta.

## 13. Cosas importantes que vale la pena saber

1. La app guarda una cita primero como pendiente. No entra directo como agendada.

2. La confirmacion por correo es una parte central del flujo.

3. El historial no solo muestra. Tambien administra estados.

4. La duracion total de una cita depende de la suma de sus servicios.

5. El sistema intenta evitar sobrecupo antes de guardar y tambien mientras la persona llena el formulario.

## 14. Puntos curiosos del codigo

Aqui van varias observaciones utiles si luego quieres seguir puliendo el proyecto.

1. Hay un archivo JS viejo para calendario que parece venir de una version anterior del flujo. La vista actual del calendario ya trae su propio script dentro del HTML.

2. El manifest apunta a una ruta de arranque distinta de la principal visible de Flask. Eso conviene revisarlo si quieres pulir la experiencia instalable.

3. El proyecto mezcla estilos globales con estilos embebidos en una de las vistas. Funciona, pero si luego quieres ordenarlo mas, ahi hay una buena oportunidad.

4. La carpeta del entorno virtual esta dentro del repo. Para desarrollo local no rompe nada, pero hace mucho ruido si luego vas a compartir o versionar mas limpio.

## 15. Como levantarlo

La idea general para correrlo es esta.

1. Tener Python.

2. Tener MySQL activo.

3. Crear o usar la base de datos del estudio.

4. Instalar dependencias dentro del entorno virtual o en tu entorno actual.

5. Configurar los datos secretos y de correo.

6. Ejecutar el archivo principal.

La app esta pensada para correr en una direccion local de red y puerto 8080.

## 16.

## 17. Funciones clave dentro de `app.py`

Aqui ya nos metemos a lo importante del archivo principal.

### 17.1 `validar_horario_cita`

Esta funcion revisa si la hora de una cita entra dentro del horario permitido.

Puede trabajar tanto con una fecha de inicio sola como con inicio y fin.

Su papel real es evitar citas fuera de ventana operativa.

### 17.2 `validar_dia_semana`

Revisa si la fecha cae en sabado o domingo.

Si cae ahi, la cita no pasa.

Es una regla simple, pero central para el negocio.

### 17.3 `calcular_duracion_servicios`

Recibe una lista de ids de servicios y suma cuantos minutos duran en total.

Esta funcion es la base para saber cuanto va a durar una cita completa.

### 17.4 `calcular_fecha_fin`

Toma la fecha de inicio y la duracion total.

Con eso calcula la hora final de la cita.

Sin esta funcion seria muy dificil validar cruces de agenda correctamente.

### 17.5 `validar_servicios_por_dia`

Esta es una de las funciones mas utiles de toda la app.

Revisa cuantos servicios tiene ya una clienta en el mismo dia y tambien revisa si ya uso un servicio largo de mas de 90 minutos.

Con esto se controla mejor la carga diaria.

### 17.6 `validar_solapamiento`

Se encarga de revisar si el bloque de tiempo que se quiere guardar choca con otra cita ya agendada.

En terminos practicos, esta funcion evita el doble apartado del mismo horario.

### 17.7 `shutdown_session`

Se ejecuta al cerrar el contexto de la app.

Su trabajo es limpiar la sesion de base de datos para no dejar conexiones colgadas.

### 17.8 `inject_csrf_token`

Le pasa al motor de plantillas la funcion que genera el token CSRF.

Eso deja disponible `csrf_token()` dentro de los HTML.

### 17.9 `apply_security_headers`

Agrega encabezados de seguridad a cada respuesta.

Tambien desactiva cache en rutas sensibles o cuando hay sesion iniciada.

### 17.10 `_usuario_logueado`

Es una ayuda pequeña pero importante.

Solo revisa si existe la marca de sesion que dice que el admin ya entro.

### 17.11 `_cliente_ip`

Busca la direccion del cliente.

Primero intenta con el encabezado de proxy y si no existe usa la direccion remota normal.

### 17.12 `_login_attempt_key`

Arma una llave unica con ip y usuario.

Esa llave se usa para llevar control de intentos fallidos.

### 17.13 `_login_bloqueado`

Revisa si esa llave ya esta bloqueada temporalmente por muchos intentos fallidos.

Si ya paso el tiempo del bloqueo, limpia el registro.

### 17.14 `_registrar_login_fallido`

Suma un intento fallido al contador.

Si llega al limite, marca la hora hasta la cual se bloquea el acceso.

### 17.15 `_limpiar_intentos_login`

Cuando un login sale bien, esta funcion borra el historial de intentos fallidos de ese usuario e ip.

### 17.16 `_generar_csrf_token`

Genera un token aleatorio y lo guarda en sesion si todavia no existe.

Es la base de la proteccion CSRF.

### 17.17 `_validar_csrf`

Compara el token guardado en sesion con el token mandado por el formulario.

Si no coinciden, corta la peticion con error.

### 17.18 `_credenciales_admin_validas`

Revisa si el usuario coincide con el admin esperado.

Luego valida la clave usando hash o texto plano segun lo que haya en variables de entorno.

### 17.19 `_redirect_login`

Centraliza la redireccion al login para rutas privadas.

Tambien lanza un mensaje para avisar que primero hay que iniciar sesion.

### 17.20 `_construir_eventos_calendario`

Transforma las citas de base de datos en el formato que entiende FullCalendar.

Eso incluye titulo, horas y propiedades extra como servicios y notas.

### 17.21 `index`

Muestra la landing principal.

### 17.22 `servicios`

Carga categorias y servicios desde base de datos para construir el catalogo.

### 17.23 `calendario`

Carga clientes, categorias, servicios y citas agendadas.

Despues manda todo a la vista de reserva.

### 17.24 `login`

Maneja tanto la vista del formulario como el proceso de autenticacion.

Valida CSRF, revisa si hay bloqueo temporal, comprueba credenciales y abre sesion si todo sale bien.

### 17.25 `logout`

Limpia la sesion y saca al admin del panel privado.

### 17.26 `guardar_cliente`

Guarda un nuevo cliente directo en base de datos.

Es una funcion corta, pero resuelve el alta rapida.

### 17.27 `guardar_cita`

Esta es la funcion mas pesada del proyecto.

Coordina validacion de datos, deteccion de cliente existente, creacion de cliente nuevo, calculo de duracion, validacion de agenda, guardado de cita, guardado de detalles y envio de correo.

Si hubiera que señalar el centro del sistema, seria esta funcion.

### 17.28 `confirmar_cita`

Valida el token temporal del correo.

Si el token sirve, cambia el estado de la cita a agendada.

### 17.29 `historial`

Carga todas las citas para el panel admin.

Es la base del seguimiento operativo.

### 17.30 `editar_cita`

Busca una cita concreta y abre la vista para mover fecha y hora.

### 17.31 `actualizar_cita`

Toma los cambios enviados desde la pantalla de edicion, recalcula el rango horario y vuelve a pasar por validaciones.

### 17.32 `api_validar_disponibilidad`

Es la ruta que responde al frontend mientras la persona esta llenando el formulario.

Regresa si un horario esta disponible y tambien calcula datos utiles para mostrar o validar.

### 17.33 `cancelar_cita`

Cambia el estado de la cita a cancelada.

### 17.34 `completar_cita`

Marca una cita como completada, pero solo si ya estaba agendada.

### 17.35 `marcar_no_asistio`

Marca que la clienta no se presento.

Igual que la anterior, solo tiene sentido cuando la cita ya estaba agendada.

## 18. Partes clave de los HTML

Aqui no todo son funciones con nombre, pero si hay bloques importantes que mueven la experiencia.

### 18.1 `index.html`

Esta vista hace el trabajo de presentar la marca.

Sus piezas clave son estas.

1. Navbar para moverse entre inicio, servicios, agenda y admin.

2. Hero principal para vender la experiencia del estudio.

3. Seccion de servicios destacados para empujar a exploracion del catalogo.

4. Bloque sobre el estudio para darle tono mas personal al negocio.

5. Llamada final a reservar para cerrar con accion clara.

6. Registro del service worker para experiencia instalable.

### 18.2 `servicios.html`

Esta vista organiza el catalogo y lo vuelve facil de recorrer.

Lo mas importante aqui es esto.

1. Barra fija de navegacion.

2. Encabezado de pagina con texto de contexto.

3. Barra de filtros por categoria.

4. Bloques por categoria con imagen, numero y nombre.

5. Filas de servicio con nombre, duracion y precio.

6. Script `filterCat` que muestra u oculta categorias sin recargar la pagina.

En otras palabras, esta vista no solo enseña datos. Tambien los ordena para que el catalogo se sienta mas curado.

### 18.3 `calendario.html`

Esta es la vista mas viva del proyecto.

Tiene piezas muy importantes.

1. Formulario de reserva con nombre, apellido, telefono, correo, fecha, servicios y notas.

2. Calendario FullCalendar que pinta las citas ya agendadas.

3. Bloque `data-eventos` que recibe los eventos serializados desde Flask.

4. Script que inicializa FullCalendar.

5. Logica `eventClick` para mostrar detalle de servicios y notas.

6. Logica `select` para pasar la fecha elegida del calendario al formulario.

7. Funcion `obtenerServiciosSeleccionados` para leer los servicios marcados.

8. Funcion `actualizarDuracion` para avisar visualmente cuantos servicios se llevan.

9. Funcion `validarDisponibilidad` para consultar al backend en tiempo real.

10. Intercepcion del envio del formulario para no mandar datos invalidos.

Si `guardar_cita` es el corazon del backend, este HTML es el corazon del frontend.

### 18.4 `login.html`

Aunque esta vista parece simple, hace algo muy importante.

1. Tiene formulario de acceso admin.

2. Incluye el token CSRF oculto.

3. Muestra mensajes flash de error.

4. Separa visualmente el area privada del resto de la app.

### 18.5 `historial.html`

Esta vista convierte la informacion en tablero de trabajo.

Sus partes clave son estas.

1. Tabla principal con cliente, inicio, fin, servicios, notas, estado y acciones.

2. Chips visuales para listar servicios de cada cita.

3. Botones para editar, completar, marcar no asistio o cancelar.

4. Condiciones de plantilla para ocultar acciones cuando la cita ya no se puede mover.

5. Estado vacio cuando no hay registros.

### 18.6 `editar_cita.html`

Esta vista esta enfocada en una sola tarea y por eso funciona bien.

1. Muestra el nombre del cliente en modo solo lectura.

2. Deja cambiar fecha y hora.

3. Enseña la lista de servicios ya asociados.

4. Calcula y muestra la duracion total.

5. Tiene un script que vuelve a consultar disponibilidad antes de guardar.

## 19. Entidades explicadas una por una

### 19.1 `CategoriaServicio`

Representa una categoria general del catalogo.

Su trabajo es agrupar servicios similares.

La relacion importante aqui es `servicios`, porque una categoria puede tener muchos servicios hijos.

### 19.2 `Servicio`

Representa un servicio individual del estudio.

Guarda categoria, nombre, precio y duracion.

Sus relaciones clave son `categoria` para saber a que grupo pertenece y `detalles` para saber en que citas ha sido usado.

### 19.3 `Cliente`

Representa a cada persona registrada en el sistema.

Guarda sus datos base y mantiene la relacion `citas`, que conecta al cliente con su historial de reservas.

El correo unico ayuda a que no se duplique gente con facilidad.

### 19.4 `EstadoCita`

No es una tabla, pero si una pieza clave.

Es el enum que define los estados validos de una cita.

Gracias a esto, el flujo del sistema no se queda en un simple activo o inactivo, sino que diferencia pendiente, agendada, completada, cancelada y no asistio.

### 19.5 `Cita`

Esta es la entidad central del negocio.

Conecta cliente, horas, estado, notas y detalles.

Sus relaciones mas importantes son `cliente` y `detalles`.

La primera dice de quien es la cita.

La segunda dice que servicios exactos forman parte de esa cita.

### 19.6 `DetalleCita`

Esta entidad actua como puente entre `Cita` y `Servicio`.

Su razon de existir es guardar cada servicio individual dentro de una cita concreta.

Tambien guarda el precio aplicado en ese momento, lo cual sirve mucho si algun dia cambian precios en el catalogo pero quieres conservar el valor historico.
