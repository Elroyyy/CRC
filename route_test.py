import requests

# Brevo API settings
BREVO_API_KEY = "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"       # Replace with your API key
SENDER_EMAIL = "elroypushparajah@gmail.com" # Your verified Brevo sender
RECIPIENT_EMAIL = "elroypushparajah@gmail.com"  # Your test email

# Email content
subject = "Test Email from Brevo API"
body = """
Hello,

This is a test email sent using Brevo API (no SMTP).

Best regards,
Your Application
"""

# Send email
try:
    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        },
        json={
            "sender": {"name": "My App", "email": SENDER_EMAIL},
            "to": [{"email": RECIPIENT_EMAIL}],
            "subject": subject,
            "textContent": body
        }
    )

    if response.status_code in [200, 201, 202]:
        print("✅ Email sent successfully!")
    else:
        print(f"❌ Failed to send email. Status code: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Error sending email: {e}")
