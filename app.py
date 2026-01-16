from flask import Flask, request, send_file, render_template_string
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from num2words import num2words
from openpyxl import Workbook, load_workbook
import os

app = Flask(__name__)

# =============================
# CONFIGURACIÓN
# =============================
BASE_RECIBOS = "recibos_generados"
EXCEL_FILE = "recibos.xlsx"

os.makedirs(BASE_RECIBOS, exist_ok=True)

# =============================
# FOLIO PERSISTENTE POR FECHA
# =============================
def obtener_folio():
    fecha = datetime.now().strftime("%Y%m%d")
    archivo_folio = f"folio_{fecha}.txt"

    if not os.path.exists(archivo_folio):
        with open(archivo_folio, "w") as f:
            f.write("0")

    with open(archivo_folio, "r") as f:
        num = int(f.read())

    num += 1

    with open(archivo_folio, "w") as f:
        f.write(str(num))

    return f"RE-{fecha}-{str(num).zfill(3)}"

# =============================
# GUARDAR EN EXCEL
# =============================
def guardar_en_excel(fecha, folio, nombre, concepto, monto, archivo):
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.append(["Fecha", "Folio", "Nombre", "Concepto", "Monto", "Archivo"])
        wb.save(EXCEL_FILE)

    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    ws.append([fecha, folio, nombre, concepto, monto, archivo])
    wb.save(EXCEL_FILE)

# =============================
# FORMULARIO PRINCIPAL
# =============================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nombre = request.form["nombre"]
        concepto = request.form["concepto"]
        monto = request.form["monto"]

        folio = obtener_folio()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Carpeta por fecha
        carpeta_fecha = datetime.now().strftime("%Y-%m-%d")
        ruta = os.path.join(BASE_RECIBOS, carpeta_fecha)
        os.makedirs(ruta, exist_ok=True)

        salida = f"{ruta}/recibo_{folio}.jpg"

        # Crear imagen
        img = Image.open("plantilla.jpg")
        draw = ImageDraw.Draw(img)

        font = ImageFont.load_default()

        draw.text((50, 50), f"Folio: {folio}", fill="black", font=font)
        draw.text((50, 80), f"Fecha: {fecha}", fill="black", font=font)
        draw.text((50, 110), f"Nombre: {nombre}", fill="black", font=font)
        draw.text((50, 140), f"Concepto: {concepto}", fill="black", font=font)
        draw.text((50, 170), f"Monto: ${monto}", fill="black", font=font)

        img.save(salida)

        # Guardar en Excel
        guardar_en_excel(fecha, folio, nombre, concepto, monto, salida)

        return send_file(salida, mimetype="image/jpeg")

    return """
    <h2>Generar Recibo</h2>
    <form method="post">
        Nombre:<br><input name="nombre"><br><br>
        Concepto:<br><input name="concepto"><br><br>
        Monto:<br><input name="monto"><br><br>
        <button>Generar Recibo</button>
    </form>
    <br>
    <a href="/historial">📂 Ver historial</a><br>
    <a href="/excel">📊 Descargar Excel</a>
    """

# =============================
# HISTORIAL
# =============================
@app.route("/historial")
def historial():
    recibos = []

    for fecha in sorted(os.listdir(BASE_RECIBOS), reverse=True):
        carpeta = os.path.join(BASE_RECIBOS, fecha)
        for archivo in sorted(os.listdir(carpeta), reverse=True):
            recibos.append(f"{fecha}/{archivo}")

    return render_template_string("""
    <h2>Historial de Recibos</h2>
    <a href="/">← Volver</a><br><br>
    {% for r in recibos %}
        <a href="/ver/{{r}}" target="_blank">{{r}}</a><br>
    {% endfor %}
    """, recibos=recibos)

# =============================
# VER RECIBO
# =============================
@app.route("/ver/<path:archivo>")
def ver_recibo(archivo):
    return send_file(os.path.join(BASE_RECIBOS, archivo))

# =============================
# DESCARGAR EXCEL
# =============================
@app.route("/excel")
def descargar_excel():
    return send_file(EXCEL_FILE, as_attachment=True)

# =============================
# EJECUCIÓN
# =============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
