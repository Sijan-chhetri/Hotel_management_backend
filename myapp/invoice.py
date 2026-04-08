from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.files.base import ContentFile
from .models import Invoice


from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from . checkout import calculate_total_amount_in_paisa
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from django.core.files.base import ContentFile
from datetime import timedelta
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from django.core.files.base import ContentFile
from datetime import timedelta
from decimal import Decimal  # Import Decimal for precise arithmetic

def generate_invoice_pdf(invoice):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.platypus import Table, TableStyle
    from decimal import Decimal

    buffer = BytesIO()
    p = pdf_canvas.Canvas(buffer, pagesize=A4)
    W, H = A4

    # ── Palette ──
    DARK       = colors.HexColor("#111827")
    ACCENT     = colors.HexColor("#1a2500")
    LIME       = colors.HexColor("#d4e87a")
    LIME_LIGHT = colors.HexColor("#f5ffd6")
    GRAY_DARK  = colors.HexColor("#374151")
    GRAY_MID   = colors.HexColor("#6b7280")
    GRAY_LIGHT = colors.HexColor("#f3f4f6")
    BORDER     = colors.HexColor("#e5e7eb")
    WHITE      = colors.white
    BLACK      = colors.HexColor("#111827")

    margin_x = 18 * mm
    margin_y = 15 * mm

    # ── White background ──
    p.setFillColor(WHITE)
    p.rect(0, 0, W, H, fill=True, stroke=0)

    # ── Top accent bar (thin lime) ──
    p.setFillColor(LIME)
    p.rect(0, H - 2.5 * mm, W, 2.5 * mm, fill=True, stroke=0)

    # ── Header ──
    header_top = H - 2.5 * mm - 8 * mm

    # Left: Hotel branding
    # Icon box
    p.setFillColor(DARK)
    p.roundRect(margin_x, header_top - 12 * mm, 12 * mm, 12 * mm, 2 * mm, fill=True, stroke=0)
    p.setFillColor(LIME)
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(margin_x + 6 * mm, header_top - 7.5 * mm, "H")

    p.setFillColor(DARK)
    p.setFont("Helvetica-Bold", 15)
    p.drawString(margin_x + 15 * mm, header_top - 6 * mm, "THE HMS")
    p.setFillColor(GRAY_MID)
    p.setFont("Helvetica", 8)
    p.drawString(margin_x + 15 * mm, header_top - 10.5 * mm, "Hotel Management System")

    # Right: INVOICE title
    p.setFillColor(DARK)
    p.setFont("Helvetica-Bold", 28)
    p.drawRightString(W - margin_x, header_top - 5 * mm, "INVOICE")
    p.setFillColor(GRAY_MID)
    p.setFont("Helvetica", 8.5)
    p.drawRightString(W - margin_x, header_top - 10.5 * mm, f"Invoice No: #{invoice.id}")

    # ── Horizontal rule under header ──
    y = header_top - 16 * mm
    p.setStrokeColor(BORDER)
    p.setLineWidth(0.8)
    p.line(margin_x, y, W - margin_x, y)

    # ── Bill To + Invoice Details (two columns) ──
    y -= 6 * mm
    col_right = W / 2 + 10 * mm

    def label(text, x, ypos):
        p.setFillColor(GRAY_MID)
        p.setFont("Helvetica", 7.5)
        p.drawString(x, ypos, text.upper())

    def value(text, x, ypos, bold=False, size=9.5):
        p.setFillColor(DARK)
        p.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        p.drawString(x, ypos, str(text))

    def rvalue(text, x, ypos, bold=False, size=9.5):
        p.setFillColor(DARK)
        p.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        p.drawRightString(x, ypos, str(text))

    # Bill To
    label("Bill To", margin_x, y)
    y -= 5 * mm
    value(invoice.booking.guest.name, margin_x, y, bold=True, size=11)
    y -= 5 * mm
    value(invoice.booking.guest.email or "—", margin_x, y)
    y -= 4.5 * mm
    value(invoice.booking.guest.phone or "—", margin_x, y)
    y -= 4.5 * mm
    value(f"Doc: {invoice.booking.guest.doc_type.upper()} · {invoice.booking.guest.doc_number}", margin_x, y)

    # Invoice details (right column)
    detail_y = y + 18 * mm  # reset to same start
    details = [
        ("Invoice Date",    invoice.generated_on.strftime("%B %d, %Y") if invoice.generated_on else "—"),
        ("Booking Ref",     f"#{invoice.booking.booking_id}"),
        ("Check-in",        invoice.check_in_date.strftime("%B %d, %Y")),
        ("Check-out",       invoice.check_out_date.strftime("%B %d, %Y")),
        ("Payment Method",  invoice.payment_type.title()),
    ]
    for lbl, val in details:
        label(lbl, col_right, detail_y)
        rvalue(val, W - margin_x, detail_y)
        detail_y -= 5 * mm

    # ── Horizontal rule ──
    y -= 6 * mm
    p.setStrokeColor(BORDER)
    p.line(margin_x, y, W - margin_x, y)

    # ── Stay summary bar ──
    y -= 5 * mm
    nights = (invoice.check_out_date - invoice.check_in_date).days or 1
    bar_h = 14 * mm
    p.setFillColor(GRAY_LIGHT)
    p.roundRect(margin_x, y - bar_h, W - 2 * margin_x, bar_h, 2 * mm, fill=True, stroke=0)

    third = (W - 2 * margin_x) / 3
    stay_items = [
        ("Room", f"{invoice.room.room_type.title()} · {invoice.room.room_id}"),
        ("Duration", f"{nights} Night{'s' if nights != 1 else ''}"),
        ("Rate / Night", f"Rs {float(invoice.room.rate):,.0f}"),
    ]
    for i, (lbl, val) in enumerate(stay_items):
        sx = margin_x + i * third + 5 * mm
        p.setFillColor(GRAY_MID)
        p.setFont("Helvetica", 7)
        p.drawString(sx, y - 5 * mm, lbl.upper())
        p.setFillColor(DARK)
        p.setFont("Helvetica-Bold", 9.5)
        p.drawString(sx, y - 10 * mm, val)

    y -= bar_h + 8 * mm

    # ── Items table ──
    # Table header
    col_widths = [85 * mm, 22 * mm, 28 * mm, 28 * mm]
    table_w = sum(col_widths)
    table_x = margin_x

    # Header row background
    p.setFillColor(DARK)
    p.rect(table_x, y - 7 * mm, table_w, 7 * mm, fill=True, stroke=0)
    headers = ["Description", "Qty", "Unit Price", "Amount"]
    x_pos = table_x
    for i, (h, cw) in enumerate(zip(headers, col_widths)):
        p.setFillColor(WHITE)
        p.setFont("Helvetica-Bold", 8)
        if i == 0:
            p.drawString(x_pos + 3 * mm, y - 4.5 * mm, h)
        else:
            p.drawRightString(x_pos + cw - 3 * mm, y - 4.5 * mm, h)
        x_pos += cw

    y -= 7 * mm

    # Room row
    rate = Decimal(str(invoice.room.rate))
    room_charge = rate * nights

    def table_row(ypos, desc, qty, unit, amount, shade=False):
        row_h = 8 * mm
        if shade:
            p.setFillColor(colors.HexColor("#fafafa"))
            p.rect(table_x, ypos - row_h, table_w, row_h, fill=True, stroke=0)
        # bottom border
        p.setStrokeColor(BORDER)
        p.setLineWidth(0.4)
        p.line(table_x, ypos - row_h, table_x + table_w, ypos - row_h)

        p.setFillColor(DARK)
        p.setFont("Helvetica", 9)
        p.drawString(table_x + 3 * mm, ypos - 5 * mm, desc)
        p.drawRightString(table_x + col_widths[0] + col_widths[1] - 3 * mm, ypos - 5 * mm, str(qty))
        p.drawRightString(table_x + col_widths[0] + col_widths[1] + col_widths[2] - 3 * mm, ypos - 5 * mm, unit)
        p.setFont("Helvetica-Bold", 9)
        p.drawRightString(table_x + table_w - 3 * mm, ypos - 5 * mm, amount)
        return ypos - row_h

    y = table_row(y, f"{invoice.room.room_type.title()} Room — {invoice.room.room_id}", nights, f"Rs {float(rate):,.0f}", f"Rs {float(room_charge):,.0f}", shade=False)

    # Order rows
    orders = invoice.booking.orders.all()
    total_items = Decimal(0)
    for i, order in enumerate(orders):
        price    = Decimal(str(order.item.price))
        qty      = order.quantity
        subtotal = price * qty
        total_items += subtotal
        y = table_row(y, order.item.name, qty, f"Rs {float(price):,.0f}", f"Rs {float(subtotal):,.0f}", shade=(i % 2 == 0))
        if y < 50 * mm:
            p.showPage()
            p.setFillColor(WHITE)
            p.rect(0, 0, W, H, fill=True, stroke=0)
            y = H - 20 * mm

    # ── Totals block (right-aligned) ──
    total_amount = room_charge + total_items
    totals_x = W - margin_x - 70 * mm
    totals_w = 70 * mm

    y -= 5 * mm

    def total_row(ypos, label_txt, amount_txt, highlight=False):
        row_h = 7 * mm
        if highlight:
            p.setFillColor(DARK)
            p.roundRect(totals_x, ypos - row_h, totals_w, row_h, 1.5 * mm, fill=True, stroke=0)
            p.setFillColor(LIME)
            p.setFont("Helvetica-Bold", 11)
            p.drawString(totals_x + 4 * mm, ypos - 4.8 * mm, label_txt)
            p.drawRightString(totals_x + totals_w - 4 * mm, ypos - 4.8 * mm, amount_txt)
        else:
            p.setStrokeColor(BORDER)
            p.setLineWidth(0.4)
            p.line(totals_x, ypos - row_h, totals_x + totals_w, ypos - row_h)
            p.setFillColor(GRAY_MID)
            p.setFont("Helvetica", 8.5)
            p.drawString(totals_x + 4 * mm, ypos - 4.5 * mm, label_txt)
            p.setFillColor(DARK)
            p.setFont("Helvetica-Bold", 8.5)
            p.drawRightString(totals_x + totals_w - 4 * mm, ypos - 4.5 * mm, amount_txt)
        return ypos - row_h - 1 * mm

    y = total_row(y, "Room Charges", f"Rs {float(room_charge):,.0f}")
    if total_items > 0:
        y = total_row(y, "Food & Beverage", f"Rs {float(total_items):,.0f}")
    y -= 2 * mm
    y = total_row(y, "TOTAL DUE", f"Rs {float(total_amount):,.0f}", highlight=True)

    # ── Payment status badge ──
    y -= 8 * mm
    badge_w = 32 * mm
    p.setFillColor(LIME_LIGHT)
    p.setStrokeColor(LIME)
    p.setLineWidth(0.8)
    p.roundRect(margin_x, y - 7 * mm, badge_w, 7 * mm, 1.5 * mm, fill=True, stroke=1)
    p.setFillColor(ACCENT)
    p.setFont("Helvetica-Bold", 8)
    p.drawCentredString(margin_x + badge_w / 2, y - 4.5 * mm, f"PAID · {invoice.payment_type.upper()}")

    # ── Notes / Thank you ──
    y -= 12 * mm
    p.setStrokeColor(BORDER)
    p.setLineWidth(0.6)
    p.line(margin_x, y, W - margin_x, y)
    y -= 5 * mm
    p.setFillColor(GRAY_MID)
    p.setFont("Helvetica-Oblique", 8.5)
    p.drawString(margin_x, y, "Thank you for choosing The HMS. We hope to welcome you again soon.")

    # ── Footer ──
    footer_y = margin_y + 4 * mm
    p.setStrokeColor(BORDER)
    p.setLineWidth(0.6)
    p.line(margin_x, footer_y + 5 * mm, W - margin_x, footer_y + 5 * mm)
    p.setFillColor(GRAY_MID)
    p.setFont("Helvetica", 7.5)
    p.drawString(margin_x, footer_y, "The HMS · Hotel Management System")
    p.drawRightString(W - margin_x, footer_y, f"Invoice #{invoice.id}  ·  {invoice.generated_on.strftime('%B %d, %Y') if invoice.generated_on else ''}")

    p.showPage()
    p.save()

    buffer.seek(0)
    file_name = f"invoice_{invoice.booking.booking_id}.pdf"
    invoice.invoice_pdf.save(file_name, ContentFile(buffer.read()), save=False)
    buffer.close()
    invoice.total_amount = total_amount
    invoice.save()







from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Invoice, Payment, Booking
from .serializers import InvoiceSerializer




class GenerateInvoiceView(APIView):
    def post(self, request):
        booking_id = request.data.get("booking_id")
        payment_id = request.data.get("payment_id")
        hotel_id = request.user.id

        if not booking_id or not payment_id:
            return Response({"error": "Missing booking ID or payment ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure the booking belongs to the authenticated hotel
        booking = get_object_or_404(Booking, booking_id=booking_id, room__hotel_id=hotel_id)
        payment = get_object_or_404(Payment, id=payment_id, booking__room__hotel_id=hotel_id)
        room = booking.room

        #  Check if invoice already exists
        existing_invoice = Invoice.objects.filter(booking=booking, payment=payment).first()
        if existing_invoice:
            serializer = InvoiceSerializer(existing_invoice)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Calculate full amount in paisa and convert to rupees
        total_amount = calculate_total_amount_in_paisa(booking) / 100

        invoice = Invoice.objects.create(
            booking=booking,
            payment=payment,
            room=room,
            check_in_date=booking.check_in_date,
            check_out_date=booking.check_out_date,
            payment_type=payment.payment_type,
            room_type=room.room_type,
            total_amount=total_amount
        )

        generate_invoice_pdf(invoice)

        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def get(self, request):
        invoice_id = request.query_params.get("invoice_id")
        booking_id = request.query_params.get("booking_id")
        hotel_id = request.user.id

        if invoice_id:
            # Filter by hotel
            invoice = get_object_or_404(Invoice, id=invoice_id, booking__room__hotel_id=hotel_id)
            serializer = InvoiceSerializer(invoice)
            response_data = serializer.data
            response_data["invoice_pdf_url"] = request.build_absolute_uri(invoice.invoice_pdf.url) if invoice.invoice_pdf else None
            return Response(response_data, status=status.HTTP_200_OK)

        elif booking_id:
            # Filter by hotel
            invoices = Invoice.objects.filter(
                booking__booking_id=booking_id,
                booking__room__hotel_id=hotel_id
            ).select_related('booking', 'booking__guest', 'booking__room', 'room', 'payment')
            serializer = InvoiceSerializer(invoices, many=True)
            invoices_data = serializer.data
            for invoice_data, invoice in zip(invoices_data, invoices):
                invoice_data["invoice_pdf_url"] = request.build_absolute_uri(invoice.invoice_pdf.url) if invoice.invoice_pdf else None
            return Response(invoices_data, status=status.HTTP_200_OK)

        # Fetch all invoices for this hotel only
        invoices = Invoice.objects.filter(
            booking__room__hotel_id=hotel_id
        ).select_related(
            'booking', 'booking__guest', 'booking__room', 'room', 'payment'
        )
        serializer = InvoiceSerializer(invoices, many=True)
        invoices_data = serializer.data

        # Add PDF URLs to each invoice
        for invoice_data, invoice in zip(invoices_data, invoices):
            invoice_data["invoice_pdf_url"] = request.build_absolute_uri(invoice.invoice_pdf.url) if invoice.invoice_pdf else None

        return Response(invoices_data, status=status.HTTP_200_OK)
