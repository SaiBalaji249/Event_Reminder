import os
import io
import requests
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle

file_id = os.environ.get("FILE_ID")
email_id = os.environ.get("EMAIL_ID")
email_id_password = os.environ.get("EMAIL_ID_PASSWORD")


# Link to export the first sheet as CSV
csv_url = f"https://docs.google.com/spreadsheets/d/{file_id}/gviz/tq?tqx=out:csv"


response = requests.get(csv_url)
if response.status_code != 200:
    print("Failed to download CSV:", response.status_code)
    exit()

df = pd.read_csv(io.StringIO(response.text))

def get_today_events(df):
    today = datetime.now().strftime('%d-%m')
    today_events = []

    for index, row in df.iterrows():
        date_val = row.get('date', None)
        if pd.isnull(date_val):
            continue  # Skip if date is missing
        try:
            date_str = str(date_val).strip()
            if len(date_str) >= 5 and date_str[:5] == today:
                name = str(row.get('name', '')).strip()
                event = str(row.get('event', '')).strip()
                today_events.append([name, event, date_str])
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            continue

    return today_events
 
    
def generate_pdf(data, filename="today_events.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []

    # Get today's date
    today_date = datetime.now().strftime('%d-%m-%Y')

    # Define a custom heading style (centered, bold, large)
    title_style = ParagraphStyle(
        name="TitleStyle",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold"
    )

    # Add heading with date
    heading = Paragraph(f"Today's Event List - {today_date}", title_style)
    elements.append(heading)
    elements.append(Spacer(1, 12))  # Add space below heading

    # Add header row + data
    table_data = [["NAME", "EVENT", "DATE"]] + data

    # Create table with column widths
    table = Table(table_data, colWidths=[150, 200, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 12),  # Increased font size
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

def send_email_events(df, email_id, email_id_password):
    today_email_events = get_today_events(df)
    print(today_email_events)
    # Generate the PDF table
    pdf_filename = "today_events.pdf"
    generate_pdf(today_email_events, pdf_filename)

    # Create email
    msg = MIMEMultipart()
    msg['Subject'] = "Today Events List Just Reminding"
    msg['From'] = email_id
    msg['To'] = email_id

    # Attach message body
    if today_email_events:
        msg.attach(MIMEText("Attached is today's events in PDF format.", "plain"))
        # Attach PDF file
        with open(pdf_filename, "rb") as file:
            part = MIMEApplication(file.read(), Name=pdf_filename)
            part['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            msg.attach(part)
    else:
        msg.attach(MIMEText("No events today.", "plain"))

    

    # Send the email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_id, email_id_password)
            server.send_message(msg)
        print("Email with PDF sent successfully.")
    except Exception as e:
        print("Error sending email:", e)
    finally:
        # Clean up the file
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)

if __name__ == "__main__":
    send_email_events(df, email_id, email_id_password)
