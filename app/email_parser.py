import re 
import pandas as pd 
import os 
from control_parse import EmailData

class EmailParser:
    def __init__(self,excel_path="incident_log.xlsx"):
        self.excel_path = excel_path
    
    def parse_email(self,email: dict)->dict:
        #Normalize escaped line breaks if needed
        email_body = email.get("content","")
        if "\\n" in email_body:
            email_body = email_body.encode().decode('unicode_escape')
        
        #Extract key-value pairs using regex
        matches = re.findall(r"^\s*(.+?):\s*(.+$)", email_body, re.MULTILINE)
        parsed_data = {key.strip().lower(): value.strip() for key, value in matches}

        lines = [l.strip() for l in email_body.splitlines() if l.strip()]
    
        primary_reason = None
        for i, line in enumerate(lines):
            # skip until we find first line with ":" (marks start of key-values)
            if ":" in line:
                break
            # store last non-empty non-key:value line before key-values start
            if ":" not in line:
                primary_reason = line
    
        parsed_data["primary_reason"] = primary_reason
        return parsed_data
        # # Extract the "primary reason" (first non-empty line that is not key:value)
        # for line in email_body.splitlines():
        #     line = line.strip()
        #     if line and ":" not in line:   # skip blank lines & key:value lines
        #         parsed_data["primary_reason"] = line
        #         break
        # else:
        #     parsed_data["primary_reason"] = None  # fallback if not found
    
        # return parsed_data
    
    # def parse_email(self,email: str)->dict:
    #     #Normalize escaped line breaks if needed
    #     # email_body = email.get("content","")
    #     email_body = email
    #     if "\\n" in email_body:
    #         email_body = email_body.encode().decode('unicode_escape')
        
    #     #Extract key-value pairs using regex
    #     matches = re.findall(r"^\s*(.+?):\s*(.+$)", email_body, re.MULTILINE)
    #     parsed_data = {key.strip().lower(): value.strip() for key, value in matches}
    #     return parsed_data
    
    def append_to_excel(self,parsed_data: dict):
        df = pd.DataFrame([parsed_data])
        print("df columns:",df.columns.tolist())
        if 'resource name' in df.columns:
            df.rename(columns={'resource name':'computer name'},inplace=True) 
        
        if os.path.exists(self.excel_path):
            existing_df = pd.read_excel(self.excel_path)

            #Add missing columns to existing df
            for col in df.columns:
                if col not in existing_df.columns:
                    existing_df[col] = None
            # Add missing columns to new row
            for col in existing_df.columns:
                if col not in df.columns:
                    df[col] = None
            updated_df = pd.concat([existing_df,df],ignore_index=True)
        
        else:
            updated_df = df
        
        updated_df.to_excel(self.excel_path,index=False)

        
    def process_email(self,email_body: str):
        parsed_data = self.parse_email(email_body)
        self.append_to_excel(parsed_data)

    
# email_content = """Organization Name: Bitzer\nTrigger name: CITRIX PVS Service up\nProcess name: SoapServer.exe\nProcess ID: 3992\nUser name: BITZER\\s00228\nSession ID: 0\nComputer name: DESON01057\nIncident timestamp (UTC +2 W. Europe Standard Time): 8/27/2025 8:29:21 AM
# """
# email_content = """This is an automated alert from ControlUp, which you requested to receive\nusing an incident trigger.\n\nOne of your managed computers has disconnected from monitoring\n\nOrganization name: Bitzer\n\nTrigger name: CITRIX Machines Computer Down ROT TS ROT\n\nComputer name: DEROT04430\n\nDisconnect reason: ControlUp Agent unreachable.\n\nIncident timestamp (UTC +2 W. Europe Standard Time): 8/26/2025 3:42:33 PM\n\nIn order to contigure which e-mail alerts you receive, please open\nControlUp and edit the settings for the bigger specified above\n', 'received_date': 'Wed, 03 Sep 2025 14:51:10 +0530"""
# email_parser = EmailData("D:/WebAssembly/emailProcessingServer/app/control_email/ControlUp alert mail - Machine down - Machine DERTOT04430.blitzer.biz is down (ControlUp Agent Unreacha.eml")
email_parser = EmailData("D:/WebAssembly/emailProcessingServer/app/control_email/ControlUp alert mail - Advance Trigger - Machine DERT0686.blitzer.biz.eml")
email_content = email_parser.extract_email()
parser = EmailParser()
parser.process_email(email_content)