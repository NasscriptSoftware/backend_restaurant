import io
import requests
from datetime import timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import inch
from twilio.rest import Client
from django.conf import settings
from django.utils import timezone


def default_time_period():
    return timezone.now() + timedelta(days=30)


def generate_order_pdf(order):
    buffer = io.BytesIO()
    
    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Set up styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']

    # Add restaurant logo
    p.drawInlineImage("https://cdn-icons-png.flaticon.com/256/261/261192.png", 50, height - 100, width=100, height=80)

    # Add restaurant name and contact
    p.setFont("Helvetica-Bold", 20)
    p.drawString(180, height - 50, "Your Restaurant Name")
    p.setFont("Helvetica", 10)
    p.drawString(180, height - 65, "123 Restaurant St, City, Country")
    p.drawString(180, height - 80, "Phone: (123) 456-7890")

    # Add a horizontal line
    p.line(50, height - 110, width - 50, height - 110)

    # Order details
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 140, f"Order #{order.id}")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 160, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(50, height - 175, f"Billed by: {order.customer.username}")
    p.drawString(50, height - 190, f"Status: {order.get_status_display()}")

    # Create a table for order items
    data = [['Item', 'Quantity', 'Price', 'Total']]
    for item in order.items.all():
        data.append([
            item.dish.name, 
            str(item.quantity), 
            f"${item.dish.price:.2f}", 
            f"${item.quantity * item.dish.price:.2f}"
        ])
    
    # Add total row
    data.append(['', '', 'Total:', f"${order.total_amount:.2f}"])

    table = Table(data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    # Draw the table on the PDF
    table.wrapOn(p, width, height)
    table.drawOn(p, 50, height - 500)

    # Add a thank you message
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, 50, "Thank you for your order! We hope you enjoy your meal.")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    return buffer


def shorten_url(long_url):
    # Using TinyURL as an example. You might want to use a different service or implement your own.
    response = requests.get(f"http://tinyurl.com/api-create.php?url={long_url}")
    return response.text.strip()


def send_sms(to_number, message):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    try:
        message = client.messages.create(
            body=message,
            from_=f"whatsapp:{settings.TWILIO_PHONE_NUMBER}",
            to=to_number
        )
        return True
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return False
