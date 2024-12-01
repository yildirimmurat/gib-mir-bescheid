import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get email credentials and other configurations from the .env file
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "Your Requested Product Information")
SEARCH_URL = os.getenv("SEARCH_URL")
USER_URL = os.getenv("USER_URL")
SEND_DELTA_DAYS = int(os.getenv("SEND_DELTA_DAYS", 30))  # Default to 30 days

# Helper function to read recipients and their last email date
def get_recipients(filename="recipients.txt"):
    recipients = []
    try:
        with open(filename, "r") as f:
            for line in f.readlines():
                email, last_sent = line.strip().split(",")
                last_sent_date = datetime.strptime(last_sent, "%Y-%m-%d")
                recipients.append((email, last_sent_date))
    except FileNotFoundError:
        pass
    return recipients

# Write recipients and their last sent date back to the file
def update_recipients(recipients, filename="recipients.txt"):
    with open(filename, "w") as f:
        for email, last_sent in recipients:
            f.write(f"{email},{last_sent.strftime('%Y-%m-%d')}\n")

# Check if the recipient needs an email
def should_send_email(last_sent_date):
    return datetime.now() - last_sent_date > timedelta(days=SEND_DELTA_DAYS)

# Send email to a single recipient
def send_email(recipient, user_url):
    try:
        # Create the email message
        message = MIMEMultipart()
        message["From"] = EMAIL_USER
        message["To"] = recipient
        message["Subject"] = EMAIL_SUBJECT
        
        body = f"Hello,\n\nHere is the search link you requested: {user_url}\n\nBest regards"
        message.attach(MIMEText(body, "plain"))

        # Set up the SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Start TLS encryption
        server.login(EMAIL_USER, EMAIL_PASSWORD)

        # Send the email
        server.sendmail(EMAIL_USER, recipient, message.as_string())
        server.quit()
        
        print(f"Email sent successfully to {recipient}")
        return True

    except Exception as e:
        print(f"Error sending email to {recipient}: {e}")
        return False

# Check if there are any products in the search results
def fetch_search_results(search_url):
    try:
        response = requests.get(search_url)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            if 'products' in data and len(data['products']) > 0:
                return True
            else:
                print("No products found in the search results.")
                return False
        else:
            print(f"Error fetching data: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error fetching data: {e}")
        return False

# Main function
def main():
    # Fetch search results and only send email if results exist
    if fetch_search_results(SEARCH_URL):
        # Get the list of recipients and their last sent date
        recipients = get_recipients()

        # Send email to each recipient if necessary
        updated_recipients = []
        for recipient, last_sent in recipients:
            if should_send_email(last_sent):
                # Send email
                if send_email(recipient, USER_URL):
                    # Update last sent date if email is sent
                    updated_recipients.append((recipient, datetime.now()))
            else:
                updated_recipients.append((recipient, last_sent))

        # Save the updated recipients with new timestamps
        update_recipients(updated_recipients)
    else:
        print("No products found. No email sent.")

if __name__ == "__main__":
    main()
