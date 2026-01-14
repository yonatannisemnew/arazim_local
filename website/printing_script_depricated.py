import sys 
import email
import smtplib


SEND_ADDR = "WE NEED TO CREATE AN EMAIL FOR THIS!!!" # TODO: create email
SEND_PASS = "EMAIL PASSWORD HERE"  # TODO: email password
RECV_ADDR = "RECEIVER EMAIL HERE"  # TODO: receiver email
SMTP_PORT = 587  # Common SMTP port for TLS


def send_email(abs_file_path: str, send_addr: str=SEND_ADDR, recv_addr: str=RECV_ADDR, password: str=SEND_PASS):
    message = email.message.EmailMessage()
    message["From"] = send_addr
    message["To"] = recv_addr
    message["Subject"] = "File to print"
    with open(abs_file_path, "rb") as f:
        file_data = f.read()
        message.add_attachment(file_data, subtype=f"{abs_file_path.split(".")[-1]}", filename=os.path.basename(abs_file_path))
    
    try:
        with smtplib.SMTP(recv_addr, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(send_addr, password)
            server.send_message(message)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print("Usage: python printing_script.py <absolute_file_path>")
        sys.exit(1)
    abs_file_path = args[1]
    send_email(abs_file_path)
    sys.exit(0)