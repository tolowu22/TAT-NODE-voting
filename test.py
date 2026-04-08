import smtplib

# 1. Put your actual sender email address inside the quotes
sender_email = "toluwaniolowu@gmail.com"

# 2. Put your 16-letter Google App Password inside the quotes (NO SPACES!)
sender_password = "fmuydqezbwplbeaw"

try:
    print(f"1. Attempting to connect to Google with {sender_email}...")
    
    # We are using Port 587 (TLS), which is the standard for modern email
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    print("2. Server responded. Securing connection...")
    
    server.starttls()
    print("3. Connection secured. Attempting login...")
    
    server.login(sender_email, sender_password)
    print("\n✅ SUCCESS! Google accepted your credentials. You can send emails!")
    
    server.quit()
    
except Exception as e:
    print(f"\n❌ FAILED. The connection was rejected. Here is why:")
    print(f"{e}")