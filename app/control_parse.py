import email
from email import policy
from email.parser import BytesParser

class EmailData:
    def __init__(self,email_path: str ):
        self.email_path = email_path
    
    def extract_email(self)->dict:
        with open(self.email_path,'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)
        
        email_id = msg['Message-ID']
        sender = msg['From']
        recipient = msg['To']
        subject = msg['Subject']
        received_date = msg['Date']
        # for part in msg.walk():
        #     content_type = part.get_content_type()
        #     content_disposition = part.get_content_disposition()

        #     if content_disposition == "attachment":
        #         filename = part.get_filename()
        #         data = part.get_payload(decode=True)
        #         with open(filename, "wb") as f:
        #             f.write(data)
        #         print(f"Saved attachment: {filename}")

        #     elif content_type == "text/plain":
        #         print("Plain Text Body:\n", part.get_content())
        
        #     elif content_type == "text/html":
        #         print("HTML Body:\n", part.get_content())
        
        # Get email body
        if msg.is_multipart():
            parts = msg.iter_parts()
            for part in parts:
                if part.get_content_type() == 'text/plain':
                    content = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                    break
            else:
                content = ""
        else:
            content = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='replace')
        
        return {
            "email_id": email_id,
            "sender": sender,
            "recipient": recipient,
            "subject": subject,
            "content": content,
            "received_date": received_date
        }
    
email_data = EmailData("D:/WebAssembly/emailProcessingServer/app/control_email/ControlUp alert mail - Machine down - Machine DERTOT04430.blitzer.biz is down (ControlUp Agent Unreacha.eml")
print(email_data.extract_email())