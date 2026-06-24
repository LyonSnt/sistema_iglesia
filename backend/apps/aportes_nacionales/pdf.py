from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generar_pdf_recibo_aporte(aporte):
    salida = BytesIO()
    ancho, alto = A4
    pdf = canvas.Canvas(salida, pagesize=A4, pageCompression=1)

    margen = 54
    y = alto - margen

    pdf.setStrokeColor(colors.HexColor("#0f172a"))
    pdf.setLineWidth(1.2)
    pdf.rect(margen, margen, ancho - (margen * 2), alto - (margen * 2), stroke=1, fill=0)

    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margen + 24, y - 24, "Recibo de aporte nacional")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(ancho - margen - 24, y - 20, aporte.numero_recibo)
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(colors.HexColor("#475569"))
    pdf.drawRightString(ancho - margen - 24, y - 36, f"Fecha de pago: {aporte.fecha_pago:%Y-%m-%d}")

    y -= 84
    pdf.setStrokeColor(colors.HexColor("#cbd5e1"))
    pdf.line(margen + 24, y, ancho - margen - 24, y)

    y -= 34
    _fila(pdf, margen + 24, y, "Iglesia filial", f"{aporte.iglesia.codigo} - {aporte.iglesia.nombre}")
    y -= 28
    _fila(pdf, margen + 24, y, "Periodo", f"{aporte.anio}-{aporte.mes:02d}")
    y -= 28
    _fila(pdf, margen + 24, y, "Referencia de pago", aporte.referencia_pago)
    y -= 28
    _fila(pdf, margen + 24, y, "Registrado por", _nombre_usuario(aporte.registrado_pago_por))

    y -= 44
    pdf.setFillColor(colors.HexColor("#f8fafc"))
    pdf.rect(margen + 24, y - 72, ancho - (margen * 2) - 48, 94, stroke=0, fill=1)
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margen + 42, y, "Detalle del aporte")

    y -= 28
    _monto(pdf, margen + 42, y, "Base de calculo", aporte.monto_base)
    _monto(pdf, margen + 220, y, "Porcentaje", aporte.porcentaje, sufijo="%")
    _monto(pdf, margen + 360, y, "Monto pagado", aporte.monto_aporte)

    y -= 86
    pdf.setFillColor(colors.HexColor("#475569"))
    pdf.setFont("Helvetica", 9)
    observacion = aporte.observacion or "Sin observacion"
    pdf.drawString(margen + 24, y, f"Observacion: {observacion[:120]}")

    pdf.setFillColor(colors.HexColor("#64748b"))
    pdf.drawString(margen + 24, margen + 24, "Documento generado por Ecclesia.")
    pdf.drawRightString(ancho - margen - 24, margen + 24, "Recibo emitido sin reutilizacion de numero.")

    pdf.showPage()
    pdf.save()
    return salida.getvalue()


def _fila(pdf, x, y, etiqueta, valor):
    pdf.setFillColor(colors.HexColor("#64748b"))
    pdf.setFont("Helvetica", 9)
    pdf.drawString(x, y + 12, etiqueta)
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x, y, str(valor or "-"))


def _monto(pdf, x, y, etiqueta, valor, sufijo=""):
    pdf.setFillColor(colors.HexColor("#64748b"))
    pdf.setFont("Helvetica", 9)
    pdf.drawString(x, y + 18, etiqueta)
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.setFont("Helvetica-Bold", 14)
    prefijo = "" if sufijo else "$ "
    pdf.drawString(x, y, f"{prefijo}{valor:.2f}{sufijo}")


def _nombre_usuario(usuario):
    if usuario is None:
        return "-"
    nombre = usuario.get_full_name().strip()
    return nombre or usuario.username
