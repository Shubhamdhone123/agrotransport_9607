from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
from django.utils.safestring import mark_safe
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas

from .models import customer, Booking, ContactQuery

# ---------------- Contact Admin ----------------
@admin.register(ContactQuery)
class ContactQueryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_filter = ('created_at',)
# ---------------- Watermark Function ----------------
def add_watermark(canvas_obj, doc):
    """Add watermark to each page"""
    canvas_obj.saveState()
    # PAID watermark
    canvas_obj.setFillColor(colors.HexColor('#f0f0f0'), alpha=0.3)
    canvas_obj.setFont('Helvetica-Bold', 60)
    canvas_obj.translate(letter[0]/2, letter[1]/2)
    canvas_obj.rotate(45)
    canvas_obj.drawCentredString(0, 0, 'PAID')
    canvas_obj.restoreState()
    
    # Add footer with timestamp
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor('#666666'))
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.drawCentredString(letter[0]/2, 0.5*inch, 
                                 f"Generated on {timezone.now().strftime('%d-%m-%Y %H:%M:%S')}")
    canvas_obj.restoreState()

# ---------------- PDF Generation ----------------
def generate_pdf_receipt(booking):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        topMargin=0.5*inch, 
        bottomMargin=0.75*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )
    story = []
    styles = getSampleStyleSheet()
    
    # --- Header Section with Accent Bar ---
    accent_table = Table([['']], colWidths=[7*inch])
    accent_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#003366')),
        ('LINEBELOW', (0,0), (-1,-1), 8, colors.HexColor('#0066cc')),
    ]))
    story.append(accent_table)
    story.append(Spacer(1, 0.2*inch))
    
    # --- Logo Placeholder (uncomment if you have a logo) ---
    from reportlab.platypus import Image
    import os
    logo_path = 'static/images/logo2.png'
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
        story.append(logo)
        story.append(Spacer(1, 0.1*inch))
    
    # --- Title ---
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=32,
        leading=36,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#003366'),
        fontName='Helvetica-Bold',
        spaceAfter=5
    )
    story.append(Paragraph("PAYMENT RECEIPT", title_style))
    
    # Subtitle
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20
    )
    story.append(Paragraph("Official Payment Confirmation", subtitle_style))
    
    # --- Company Info ---
    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Normal'],
        fontSize=13,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#003366'),
        fontName='Helvetica-Bold'
    )
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#555555')
    )
    
    story.append(Paragraph("AGRO TRANSPORT SOLUTION", company_style))
    story.append(Paragraph("Pimpalgaon Likha-431511", contact_style))
    story.append(Paragraph("+91 9834460866", contact_style))
    story.append(Spacer(1, 0.4*inch))
    
    # --- Receipt Status Badge ---
    status_data = [[f'✓ PAID - {booking.amount}']]
    status_table = Table(status_data, colWidths=[4*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 16),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 0.3*inch))
    
    # --- Section Header Style ---
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.white,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        leftIndent=10
    )
    
    # --- Receipt Details Table ---
    receipt_data = [
        [Paragraph('CUSTOMER INFORMATION', section_header_style), ''],
    ]
    
    # Customer Information
    customer_info = [
        ['Receipt Date', timezone.now().strftime('%d-%m-%Y %H:%M:%S')],
        ['Booking ID', f'#{booking.id}'],
        ['Customer Name', booking.user.name],
        ['Email', booking.user.email],
        ['Phone', str(booking.user.number)],
    ]
    receipt_data.extend(customer_info)
    
    # Booking Details
    receipt_data.append([Paragraph('BOOKING DETAILS', section_header_style), ''])
    
    booking_info = [
        ['Pickup Location', booking.pickup],
        ['Delivery Location', booking.delivery],
        ['Goods Type', booking.goodtype.title()],
        ['Vehicle Type', booking.vehicletype.title()],
        ['Pickup Date', booking.pickupdate.strftime('%d-%m-%Y')],
        ['Distance', f'{booking.distance} km'],
    ]
    receipt_data.extend(booking_info)
    
    # Payment Summary
    receipt_data.append([Paragraph('PAYMENT SUMMARY', section_header_style), ''])
    receipt_data.append(['Total Amount Paid', f'{booking.amount}'])
    
    table = Table(receipt_data, colWidths=[2.5*inch, 4*inch])
    
    # Enhanced table styling
    table_style = TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        
        # Section headers styling
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
        ('SPAN', (0,0), (-1,0)),
        ('TOPPADDING', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        
        ('BACKGROUND', (0,6), (-1,6), colors.HexColor('#003366')),
        ('SPAN', (0,6), (-1,6)),
        ('TOPPADDING', (0,6), (-1,6), 10),
        ('BOTTOMPADDING', (0,6), (-1,6), 10),
        
        ('BACKGROUND', (0,13), (-1,13), colors.HexColor('#003366')),
        ('SPAN', (0,13), (-1,13)),
        ('TOPPADDING', (0,13), (-1,13), 10),
        ('BOTTOMPADDING', (0,13), (-1,13), 10),
        
        # Amount row special styling
        ('BACKGROUND', (0,14), (-1,14), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0,14), (0,14), 'Helvetica-Bold'),
        ('FONTNAME', (1,14), (1,14), 'Helvetica-Bold'),
        ('FONTSIZE', (0,14), (-1,14), 13),
        ('TEXTCOLOR', (1,14), (1,14), colors.HexColor('#28a745')),
    ])
    
    # Alternate row colors
    for i in range(1, len(receipt_data)):
        if i not in [0, 6, 13, 14]:
            if i % 2 == 0:
                table_style.add('BACKGROUND', (0,i), (-1,i), colors.HexColor('#f8f9fa'))
            else:
                table_style.add('BACKGROUND', (0,i), (-1,i), colors.white)
    
    table.setStyle(table_style)
    story.append(table)
    story.append(Spacer(1, 0.4*inch))
    
    # --- Divider Line ---
    divider = Table([['']], colWidths=[7*inch])
    divider.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 2, colors.HexColor('#0066cc')),
    ]))
    story.append(divider)
    story.append(Spacer(1, 0.2*inch))
    
    # --- Footer Messages ---
    footer_title = ParagraphStyle(
        'FooterTitle',
        parent=styles['Normal'],
        fontSize=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#003366'),
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        leading=14
    )
    
    story.append(Paragraph("Thank you for choosing Agro Transport Solution!", footer_title))
    story.append(Paragraph("This is a digitally generated receipt and does not require a signature.", footer_style))
    story.append(Paragraph("For any queries, please contact us at +91 9834460866", footer_style))
    
    # Build PDF with watermark
    doc.build(story, onFirstPage=add_watermark, onLaterPages=add_watermark)
    buffer.seek(0)
    return buffer


# ---------------- Booking Admin ----------------
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'pickup', 'delivery', 'amount',
        'booking_status_colored', 'payment_status_colored',
        'driver_name', 'pickupdate', 'paid_at'
    ]
    list_display_links = ['id', 'user']
    list_filter = ['payment_status', 'booking_status', 'pickupdate', 'goodtype']
    search_fields = ['user__name', 'user__email', 'pickup', 'delivery', 'driver_name']
    readonly_fields = ['paid_at', 'last_location_update', 'driver_share_link', 'current_gps']

    fieldsets = (
        ('Customer Information', {'fields': ('user',)}),
        ('Booking Details', {
            'fields': ('pickup', 'delivery', 'goodtype', 'vehicletype',
                       'pickupdate', 'distance', 'amount', 'special_notes', 'estimated_delivery')
        }),
        ('Payment Information', {'fields': ('payment_status', 'paid_at')}),
        ('🚛 Delivery Tracking — Send Link to Driver', {
            'fields': ('booking_status', 'driver_name', 'driver_phone',
                       'driver_share_link', 'current_gps', 'last_location_update'),
            'description': (
                '1️⃣ Enter driver name & phone below. '
                '2️⃣ Copy the "Driver Tracking Link" and send to driver via WhatsApp. '
                '3️⃣ Driver opens it on their phone → location updates automatically. '
                '4️⃣ Set Booking Status to "In Transit" and Save.'
            ),
        }),
    )

    # Colored Booking Status
    def booking_status_colored(self, obj):
        colors_map = {
            'confirmed':  ('#3b82f6', '📋 Confirmed'),
            'in_transit': ('#f59e0b', '🚛 In Transit'),
            'delivered':  ('#10b981', '✅ Delivered'),
            'cancelled':  ('#ef4444', '❌ Cancelled'),
        }
        color, label = colors_map.get(obj.booking_status, ('#999', obj.booking_status))
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, label
        )
    booking_status_colored.short_description = 'Delivery Status'

    # Copyable driver tracking link shown in admin
    def driver_share_link(self, obj):
        if not obj.driver_share_key:
            return 'Save the booking first to generate link'
        link = f'/driver/{obj.id}/{obj.driver_share_key}/'
        return format_html(
            '<div style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:12px; max-width:600px;">'
            '<p style="color:#94a3b8;font-size:12px;margin-bottom:6px;">📱 Send this link to the driver via WhatsApp:</p>'
            '<code style="color:#f59e0b;font-size:13px;word-break:break-all;">{}</code>'
            '<br><br>'
            '<a href="{}" target="_blank" style="background:#f59e0b;color:#1e293b;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:12px;">'
            '🔗 Open Link (Test)</a>'
            '</div>',
            link, link
        )
    driver_share_link.short_description = '📱 Driver Tracking Link (Send via WhatsApp)'

    # Current GPS coords display
    def current_gps(self, obj):
        if obj.driver_lat and obj.driver_lng:
            gmaps_url = f'https://www.google.com/maps?q={obj.driver_lat},{obj.driver_lng}'
            return format_html(
                '<span style="font-family:monospace;color:#fbbf24;">Lat: {} | Lng: {}</span> &nbsp;'
                '<a href="{}" target="_blank" style="color:#60a5fa;font-size:12px;">🗺 View on Google Maps</a>',
                round(obj.driver_lat, 6), round(obj.driver_lng, 6), gmaps_url
            )
        return mark_safe(
    '<span style="color:#475569;">No GPS data yet — waiting for driver to start sharing</span>'
)
    current_gps.short_description = '📍 Current Driver GPS (Live)'

    # Colored Payment Status
    def payment_status_colored(self, obj):
        if obj.payment_status == 'paid':
           return mark_safe(
            '<span style="color:#10b981;font-weight:bold;">✓ Paid</span>'
        )
        return mark_safe(
        '<span style="color:#f59e0b;font-weight:bold;">⏳ Pending</span>'
    )
    payment_status_colored.short_description = 'Payment'

    # On save: send PDF when payment changes to paid; send email when status → in_transit
    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Booking.objects.get(pk=obj.pk)

            # Payment confirmed → send PDF receipt
            if old_obj.payment_status == 'pending' and obj.payment_status == 'paid':
                obj.paid_at = timezone.now()
                try:
                    pdf_buffer = generate_pdf_receipt(obj)
                    subject = "Payment Confirmation & Booking Receipt"
                    message = (
                        f"Dear {obj.user.name},\n\n"
                        f"Your payment has been confirmed successfully!\n"
                        f"Booking ID: #{obj.id}\nAmount: ₹{obj.amount}\n\n"
                        f"Please find attached receipt."
                    )
                    email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [obj.user.email])
                    email.attach(f'receipt_booking_{obj.id}.pdf', pdf_buffer.getvalue(), 'application/pdf')
                    email.send(fail_silently=True)
                except Exception as e:
                    print("Error sending PDF/email:", e)

            # Delivery started → send tracking email
            if old_obj.booking_status != 'in_transit' and obj.booking_status == 'in_transit':
                try:
                    from django.core.mail import send_mail as _send
                    # Use NGROK_URL from settings if available, else fall back to localhost
                    base_url = f"https://{settings.NGROK_URL}" if hasattr(settings, 'NGROK_URL') else "http://127.0.0.1:8000"
                    tracking_url = f"{base_url}/track/{obj.id}/"
                    driver_link  = f"{base_url}/driver/{obj.id}/{obj.driver_share_key}/"
                    subject = "🚛 Your Delivery Has Started! Track Live"
                    message = (
                        f"Dear {obj.user.name},\n\n"
                        f"Great news! Your goods are now on the way.\n\n"
                        f"Booking ID: #{obj.id}\n"
                        f"Route: {obj.pickup} → {obj.delivery}\n"
                        f"Driver: {obj.driver_name or 'Assigned'}\n"
                        f"Driver Phone: {obj.driver_phone or 'N/A'}\n\n"
                        f"Track your delivery live here:\n{tracking_url}\n\n"
                        f"Or login to your dashboard at AgroTransport.\n\n"
                        f"Thank you for choosing AgroTransport!"
                    )
                    _send(subject, message, settings.EMAIL_HOST_USER, [obj.user.email])
                except Exception as e:
                    print("Error sending transit email:", e)

        super().save_model(request, obj, form, change)

# ---------------- Customer Admin ----------------
admin.site.register(customer)