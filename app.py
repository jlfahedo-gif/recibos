from flask import Flask, render_template_string, request, send_file
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os
import openpyxl

app = Flask(__name__)

# Carpeta base para recibos
BASE_RECIBOS = "recibos_generados"

# Archivo para el folio
FOLIO_FILE = "folio.txt"

# Función para obtener folio persistente por fecha
def obtener_folio():
    fecha = datetime.now().strftime("%Y%m%d")
    folio_archivo = f"folio_{fecha}.txt"
    try:
        with open(folio_archivo, "r") as f:
            num = int(f.read())
    except:
        num = 0
    num += 1
    with open(folio_archivo, "w") as f:
        f.write(str(num))
    return f"{fecha}-{str(num).zfill(3)}"

# Ruta principal para generar recibo
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        monto = request.form.get("monto")

        folio = obtener_folio()
        fecha_carpeta = datetime.now().strftime("%Y-%m-%d")
        ruta = os.path.join(BASE_RECIBOS, fecha_carpeta)
        os.makedirs(ruta, exist_ok=True)

        # Crear imagen del recibo
        img = Image.new("RGB", (600, 400), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((50, 50), f"Recibo: {folio}", fill=(0, 0, 0), font=font)
        draw.text((50, 100), f"Nombre: {nombre}", fill=(0, 0, 0), font=font)
        draw.text((50, 150), f"Monto: ${monto}", fill=(0, 0, 0), font=font)

        salida = os.path.join(ruta, f"recibo_{folio}.jpg")
        img.save(salida)

        # Guardar en Excel
        excel_path = os.path.join(BASE_RECIBOS, "recibos.xlsx")
        if os.path.exists(excel_path):
            wb = openpyxl.load_workbook(excel_path)
            ws = wb.active
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["Folio", "Nombre", "Monto", "Fecha"])

        ws.append([folio, nombre, monto, fecha_carpeta])
        wb.save(excel_path)

        return f"Recibo generado: {salida} <br><a href='/'>← Volver</a>"

    return """
        <h2>Generar Recibo</h2>
        <form method="POST">
            Nombre: <input name="nombre"><br>
            Monto: <input name="monto"><br>
            <button type="submit">Generar</button>
        </form>
        <br>
        <a href="/historial">Ver Historial</a>
    """

# Historial de recibos
@app.route("/historial")
def historial():
    recibos = []
    if os.path.exists(BASE_RECIBOS):
        for fecha in sorted(os.listdir(BASE_RECIBOS), reverse=True):
            carpeta = os.path.join(BASE_RECIBOS, fecha)
            if not os.path.isdir(carpeta):
                continue
            for archivo in sorted(os.listdir(carpeta), reverse=True):
                recibos.append(f"{fecha}/{archivo}")

    return render_template_string("""
        <h2>Historial de Recibos</h2>
        <a href="/">← Volver</a><br><br>
        {% for r in recibos %}
            <a href="/ver/{{r}}" target="_blank">{{r}}</a><br>
        {% endfor %}
    """, recibos=recibos)

# Ver un recibo
@app.route("/ver/<path:archivo>")
def ver_recibo(archivo):
    ruta = os.path.join(BASE_RECIBOS, archivo)
    if os.path.exists(ruta):
        return send_file(ruta)
    return "Archivo no encontrado"

if __name__ == "__main__":
    os.makedirs(BASE_RECIBOS, exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5001)