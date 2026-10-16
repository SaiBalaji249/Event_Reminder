
import os
import html
import pandas as pd
import smtplib

from datetime import datetime
from zoneinfo import ZoneInfo
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from datetime import datetime, timedelta


# Gmail credentials (set these as environment variables)
email_id = ""
email_id_password = ""


# Google Sheets CSV URL
csv_url = (
    "https://docs.google.com/spreadsheets/d/"
    "1QDYgBxgcTcYC0tc_BlgVU4Yq8vJOMcfz/export?format=csv"
)

# Get today's events from Google Sheets data
# def get_today_events(df):
#     now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
#     today = (now_ist + timedelta(days = 1)).strftime("%d-%m")

#     today_events = []

#     for _, row in df.iterrows():
#         name = str(row["name"]).strip() if pd.notna(row["name"]) else ""
#         event = str(row["event"]).strip() if pd.notna(row["event"]) else ""
#         date = str(row["date"]).strip() if pd.notna(row["date"]) else ""

#         if not date:
#             continue

#         try:
#             event_date = pd.to_datetime(
#                 date, dayfirst=True, errors="raise"
#             ).strftime("%d-%m")
#         except (ValueError, TypeError):
#             continue

#         if event_date == today:
#             today_events.append([name, event, date])

#     return today_events


def get_tomorrow_events(df):
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))

    # Get tomorrow's day and month
    tomorrow = (now_ist + timedelta(days=1)).strftime("%d-%m")

    tomorrow_events = []

    for _, row in df.iterrows():
        name = str(row["name"]).strip() if pd.notna(row["name"]) else ""
        event = str(row["event"]).strip() if pd.notna(row["event"]) else ""
        date = str(row["date"]).strip() if pd.notna(row["date"]) else ""

        if not date:
            continue

        try:
            event_date = pd.to_datetime(
                date, dayfirst=True, errors="raise"
            ).strftime("%d-%m")
        except (ValueError, TypeError):
            continue

        # Compare only day and month, ignoring year
        if event_date == tomorrow:
            tomorrow_events.append([name, event, date])

    return tomorrow_events



# Create HTML email body
def create_email_body(events):
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    tomorrow_date = (now_ist + timedelta(days = 1)).strftime("%d-%m-%Y")

    if not events:
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Tomorrow's Event Reminder: {tomorrow_date}</h2>
            <p>There are no events scheduled for today.</p>
        </body>
        </html>
        """

    rows = ""

    for name, event, date in events:
        rows += f"""
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">
                {html.escape(name)}
            </td>
            <td style="padding: 10px; border: 1px solid #ddd;">
                {html.escape(event)}
            </td>
            <td style="padding: 10px; border: 1px solid #ddd;">
                {html.escape(date)}
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">

        <h2>Tomorrow's Event List: {tomorrow_date}</h2>

        <p>Here are the events scheduled for today:</p>

        <table style="
            border-collapse: collapse;
            width: 100%;
            max-width: 700px;
            text-align: left;
        ">
            <thead>
                <tr style="background-color: #eeeeee;">
                    <th style="padding: 10px; border: 1px solid #ddd;">
                        NAME
                    </th>
                    <th style="padding: 10px; border: 1px solid #ddd;">
                        EVENT
                    </th>
                    <th style="padding: 10px; border: 1px solid #ddd;">
                        DATE
                    </th>
                </tr>
            </thead>

            <tbody>
                {rows}
            </tbody>
        </table>

        <p>Have a great day!</p>

    </body>
    </html>
    """


# Send today's events through email
def send_email_events(df, email_id, email_id_password):
    tomorrow_events = get_tomorrow_events(df)

    # Create email
    msg = MIMEMultipart()
    msg["Subject"] = (
        "Tomorrow's Events Reminder"
        if tomorrow_events
        else "No Events Tomorrow"
    )
    msg["From"] = email_id
    msg["To"] = email_id

    # Attach only the HTML body
    html_body = create_email_body(tomorrow_events)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Send email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(email_id, email_id_password)
            server.send_message(msg)

        print(
            f"Email sent successfully. "
            f"Events found: {len(tomorrow_events)}"
        )

    except Exception as e:
        print(f"Error sending email: {e}")


# Main execution
if __name__ == "__main__":
    try:
        # Fetch Google Sheets data
        df = pd.read_csv(csv_url)

        # Validate required columns
        required_columns = {"name", "event", "date"}

        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValueError(
                f"Missing required Google Sheets columns: {missing}"
            )

        send_email_events(df, email_id, email_id_password)

    except Exception as e:
        print(f"Error reading Google Sheets or running reminder: {e}")

