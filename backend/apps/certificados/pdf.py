from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ORO = colors.HexColor("#c9a24a")
ORO_CLARO = colors.HexColor("#f1df9a")
CREMA = colors.HexColor("#fbf8f1")
NEGRO = colors.HexColor("#202027")


def _texto_centrado(pdf, texto, y, fuente="Helvetica", tamano=16):
    pdf.setFillColor(NEGRO)
    pdf.setFont(fuente, tamano)
    pdf.drawCentredString(landscape(A4)[0] / 2, y, texto)


def generar_pdf_certificado(certificado):
    salida = BytesIO()
    ancho, alto = landscape(A4)
    pdf = canvas.Canvas(salida, pagesize=(ancho, alto), pageCompression=1)
    pdf.setTitle(f"Certificado {certificado.numero}")

    pdf.setFillColor(CREMA)
    pdf.rect(0, 0, ancho, alto, fill=1, stroke=0)
    pdf.setStrokeColor(ORO)
    pdf.setLineWidth(5)
    pdf.rect(20, 20, ancho - 40, alto - 40, fill=0, stroke=1)
    pdf.setStrokeColor(ORO_CLARO)
    pdf.setLineWidth(1.5)
    pdf.rect(30, 30, ancho - 60, alto - 60, fill=0, stroke=1)

    pdf.setFillColor(ORO_CLARO)
    pdf.setFillAlpha(0.28)
    pdf.circle(25, alto - 20, 130, fill=1, stroke=0)
    pdf.circle(ancho - 10, 15, 120, fill=1, stroke=0)
    pdf.setFillAlpha(0.06)
    pdf.setFont("Helvetica-Bold", 190)
    pdf.drawCentredString(ancho / 2, alto / 2 - 65, "EC")
    pdf.setFillAlpha(1)

    _texto_centrado(pdf, certificado.iglesia.nombre.upper(), alto - 105, "Times-Bold", 22)
    _texto_centrado(pdf, "CERTIFICADO DE GRADUACION", alto - 145, "Times-Bold", 25)
    _texto_centrado(pdf, "ESCUELA DOMINICAL", alto - 182, "Helvetica-Bold", 18)
    pdf.setStrokeColor(ORO)
    pdf.setLineWidth(2)
    pdf.line(ancho / 2 - 250, alto - 175, ancho / 2 - 120, alto - 175)
    pdf.line(ancho / 2 + 120, alto - 175, ancho / 2 + 250, alto - 175)

    _texto_centrado(pdf, "Otorgado a:", alto - 215, "Helvetica-Bold", 13)
    estilo_nombre = ParagraphStyle(
        "nombre", fontName="Times-Italic", fontSize=30, leading=34, alignment=TA_CENTER, textColor=NEGRO
    )
    nombre = Paragraph(certificado.nombre_alumno, estilo_nombre)
    _, alto_nombre = nombre.wrap(ancho - 180, 70)
    nombre.drawOn(pdf, 90, alto - 285 - alto_nombre / 2)
    pdf.setStrokeColor(colors.HexColor("#777777"))
    pdf.setLineWidth(0.8)
    pdf.line(190, alto - 295, ancho - 190, alto - 295)

    texto = (
        f"Por haber concluido satisfactoriamente el {certificado.nivel_cursado} "
        f"de Escuela Dominical, correspondiente al periodo lectivo {certificado.periodo_lectivo}."
    )
    estilo = ParagraphStyle(
        "cuerpo", fontName="Helvetica", fontSize=13, leading=18, alignment=TA_CENTER, textColor=NEGRO
    )
    parrafo = Paragraph(texto, estilo)
    _, alto_parrafo = parrafo.wrap(ancho - 220, 70)
    parrafo.drawOn(pdf, 110, alto - 350 - alto_parrafo)

    _texto_centrado(
        pdf,
        "Instruye al nino en su camino, y aun cuando fuere viejo no se apartara de el.",
        alto - 405,
        "Helvetica-Oblique",
        11,
    )
    _texto_centrado(pdf, "Proverbios 22:6", alto - 425, "Helvetica-BoldOblique", 11)
    fecha = certificado.fecha_graduacion.strftime("%d/%m/%Y")
    _texto_centrado(pdf, f"{certificado.iglesia.nombre.upper()}, {fecha}", alto - 465, "Times-Bold", 12)

    y_firma = 82
    pdf.setStrokeColor(ORO)
    pdf.line(175, y_firma + 28, 355, y_firma + 28)
    pdf.line(ancho - 355, y_firma + 28, ancho - 175, y_firma + 28)
    pdf.setFillColor(NEGRO)
    pdf.setFont("Times-Roman", 12)
    pdf.drawCentredString(265, y_firma + 10, certificado.nombre_pastor)
    pdf.drawCentredString(ancho - 265, y_firma + 10, certificado.nombre_director)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(265, y_firma - 5, "PASTOR")
    pdf.drawCentredString(ancho - 265, y_firma - 5, "DIRECTOR")

    pdf.setFillColor(ORO)
    pdf.circle(92, 95, 42, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(92, 98, certificado.nivel_cursado.upper())
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(92, 82, "NIVEL COMPLETADO")
    pdf.setFillColor(NEGRO)
    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(ancho - 38, 35, certificado.numero)

    if certificado.estado == certificado.Estado.ANULADO:
        pdf.saveState()
        pdf.setFillColor(colors.red)
        pdf.setFillAlpha(0.25)
        pdf.translate(ancho / 2, alto / 2)
        pdf.rotate(25)
        pdf.setFont("Helvetica-Bold", 70)
        pdf.drawCentredString(0, 0, "ANULADO")
        pdf.restoreState()

    pdf.showPage()
    pdf.save()
    salida.seek(0)
    return salida.getvalue()
