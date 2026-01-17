from flask import Flask, request, send_file, render_template_string
from PIL import Image, ImageDraw, ImageFont
from num2words import num2words
from datetime import datetime
import os
import openpyxl

app = Flask(__name__)

PLANTILLA = "plantilla.jpg"
FONT = "fonts/AmericanTypewriter.ttc"
BASE_RECIBOS = "recibos_generados"
EXCEL_FILE = "recibos.xlsx"

# ---------- FOLIO POR FECHA ----------
def obtener_folio():
    fecha = datetime.now().strftime("%Y%m%d")
    archivo = f"folio_{fecha}.txt"

    if os.path.exists(archivo):
        with open(archivo, "r") as f:
            num = int(f.read())
    else:
        num = 0

    num += 1

    with open(archivo, "w") as f:
        f.write(str(num))

    return f"RE-{fecha}-{str(num).zfill(3)}"

# ---------- REGISTRAR EN EXCEL ----------
def registrar_excel(folio, fecha, nombre, concepto, cantidad):
    if not os.path.exists(EXCEL_FILE):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Folio", "Fecha", "Nombre", "Concepto", "Cantidad"])
        wb.save(EXCEL_FILE)

    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    ws.append([folio, fecha, nombre, concepto, cantidad])
    wb.save(EXCEL_FILE)

# ---------- GENERAR RECIBO ----------
@app.route("/", methods=["GET", "POST"])
def generar():
    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        concepto = request.form.get("concepto", "").strip()
        cantidad = request.form.get("cantidad", "0").strip()

        if not nombre or not concepto or not cantidad:
            return "Faltan datos"

        cantidad = float(cantidad)

        folio = obtener_folio()
        fecha = datetime.now().strftime("%d/%m/%Y")
        letra = num2words(cantidad, lang="es").upper() + " PESOS"

        img = Image.open(PLANTILLA)
        d = ImageDraw.Draw(img)

        font = ImageFont.truetype(FONT, 28)
        font_big = ImageFont.truetype(FONT, 32)

        d.text((380, 20), folio, fill="red", font=font)
        d.text((300, 120), fecha, fill="black", font=font)
        d.text((540, 120), nombre, fill="black", font=font)
        d.text((540, 220), concepto, fill="black", font=font)
        d.text((180, 380), f"${cantidad:,.2f}", fill="blue", font=font_big)
        d.text((120, 430), letra + " 00/100 M.N.", fill="black", font=font)

        carpeta_fecha = datetime.now().strftime("%Y-%m-%d")
        ruta = os.path.join(BASE_RECIBOS, carpeta_fecha)
        os.makedirs(ruta, exist_ok=True)

        salida = f"{ruta}/recibo_{folio}.jpg"
        img.save(salida)

        registrar_excel(folio, fecha, nombre, concepto, cantidad)

        return send_file(salida, as_attachment=True)

    # ---------- PLANTILLA HTML CON LOGO Y FORMULARIO CENTRADO ----------
    return render_template_string("""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Recibos</title>
    <link rel="icon" href="/static/icono-recibo.png">
    <style>
        body {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            font-family: Arial, sans-serif;
            margin-top: 50px;
        }
        form {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            background-color: #f9f9f9;
            padding: 20px 30px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        input, button {
            padding: 8px 12px;
            font-size: 16px;
        }
        button {
            cursor: pointer;
        }
        img.logo {
            width: 150px;
            height: 150px;
            margin-bottom: 20px;
        }
        a {
            margin-top: 15px;
            text-decoration: none;
            color: #333;
        }
    </style>
</head>
<body>
    <img class="logo" src="/static/icono-recibo.png" alt="Logo Recibos">
    <h2>Generar Recibo</h2>

    <form method="post">
        <input name="nombre" placeholder="Nombre" required>
        <input name="concepto" placeholder="Concepto" required>
        <input name="cantidad" type="number" step="0.01" placeholder="Cantidad" required>
        <button>Generar Recibo</button>
    </form>

    <a href="/historial">📂 Ver historial</a><br>
    <a href="/excel">📊 Descargar Excel</a>
</body>
</html>
""")

# ---------- HISTORIAL ----------
@app.route("/historial")
def historial():
    recibos = []

    if os.path.exists(BASE_RECIBOS):
        for fecha in sorted(os.listdir(BASE_RECIBOS), reverse=True):
            carpeta = os.path.join(BASE_RECIBOS, fecha)

            # ---------- AGREGAR ESTA LÍNEA ----------
            if not os.path.isdir(carpeta):
                continue  # ignora archivos que no son carpetas (como .DS_Store)
            # -----------------------------------------

            for archivo in sorted(os.listdir(carpeta), reverse=True):
                recibos.append(f"{fecha}/{archivo}")

    return render_template_string("""
    <h2>Historial de Recibos</h2>
    <a href="/">← Volver</a><br><br>
    {% for r in recibos %}
        <a href="/ver/{{r}}" target="_blank">{{r}}</a><br>
    {% endfor %}
    """, recibos=recibos)

# ---------- VER IMAGEN ----------
@app.route("/ver/<path:ruta>")
def ver_recibo(ruta):
    return send_file(os.path.join(BASE_RECIBOS, ruta))

# ---------- EXCEL ----------
@app.route("/excel")
def descargar_excel():
    return send_file(EXCEL_FILE, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)