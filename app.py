from flask import Flask, request, send_file, render_template_string
from PIL import Image, ImageDraw, ImageFont
from num2words import num2words
from datetime import datetime

app = Flask(__name__)

PLANTILLA = "plantilla.jpg"
FOLIO_FILE = "folio.txt"
FONT = "fonts/AmericanTypewriter.ttc"

def obtener_folio():
    try:
        with open(FOLIO_FILE, "r") as f:
            num = int(f.read())
    except:
        num = 0
    num += 1
    with open(FOLIO_FILE, "w") as f:
        f.write(str(num))
    return f"RE-{str(num).zfill(4)}"

@app.route("/", methods=["GET", "POST"])
def generar():
    if request.method == "POST":
        nombre = request.form["nombre"]
        concepto = request.form["concepto"]
        cantidad = float(request.form["cantidad"])

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
        d.text((150, 430), letra + " 00/100 M.N.", fill="black", font=font)

        salida = f"recibo_{folio}.jpg"
        img.save(salida)

        return send_file(salida, as_attachment=True)

    # 🔽 AQUÍ VA EL HTML (FORMULARIO + BOTÓN WHATSAPP)
    return render_template_string("""
    <h2>Generar Recibo</h2>

    <form method="post">
        Nombre:<br><input name="nombre"><br><br>
        Concepto:<br><input name="concepto"><br><br>
        Cantidad:<br><input name="cantidad" type="number" step="0.01"><br><br>

        <button type="submit">Generar Recibo</button>
    </form>

    <br><br>

    <!-- BOTÓN WHATSAPP -->
    <a href="https://wa.me/?text=Hola,%20te%20envío%20tu%20recibo."
       target="_blank"
       style="
          background:#25D366;
          color:white;
          padding:12px 20px;
          text-decoration:none;
          border-radius:6px;
          font-weight:bold;
          display:inline-block;
       ">
       📲 Enviar por WhatsApp
    </a>
    """)

# 🔴 ESTO SIEMPRE VA AL FINAL
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
