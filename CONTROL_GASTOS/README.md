# Sistema de Control de Gastos — Flask + SQLite

Aplicación web para registrar gastos y generar reportes, desarrollada en **Python, Flask y SQLite**.

## Acceso
- Usuario de demostración: `admin`
- Clave de demostración: `123`

## Funcionamiento
1. Acceder a `/login` e ingresar las credenciales.
2. Registrar cada gasto con **fecha, descripción y monto en soles**.
3. Consultar los últimos movimientos y el total acumulado.
4. Abrir **Reportes** y filtrar por fecha inicial y final.
5. Imprimir o guardar el reporte en PDF con el navegador.
6. Cerrar sesión desde **Salir**.

Los gastos se almacenan en SQLite y persisten entre reinicios locales. El reporte se calcula a partir de los registros existentes.

## Capturas de pantalla de la aplicación
**Pendiente de incorporar capturas reales tras ejecutar la aplicación.** No se incluyen imágenes simuladas.

Cuando se obtengan capturas reales, subirlas a `capturas/` y referenciarlas aquí:

- `capturas/01-login.png`: pantalla de acceso.
- `capturas/02-registro.png`: formulario de registro.
- `capturas/03-listado.png`: listado de gastos.
- `capturas/04-reporte.png`: reporte por fechas.

## Ejecución local
```bash
cd CONTROL_GASTOS
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Abrir http://127.0.0.1:5000/login

## Seguridad y despliegue
Las credenciales `admin / 123` son exclusivamente para evaluación académica. Cambiar `ADMIN_USER`, `ADMIN_PASSWORD` y `SECRET_KEY` antes de publicar. Para producción, implementar hash de contraseñas, CSRF y limitación de intentos de acceso. Usar almacenamiento persistente para `DATABASE_PATH` en servicios cloud; de lo contrario se pueden perder datos.

**Proyecto académico desarrollado con Flask, Python y SQLite.**
