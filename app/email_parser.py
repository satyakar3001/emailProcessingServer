import re 
import pandas as pd 
import os 

class EmailParser:
    def __init__(self,excel_path="incident_log.xlsx"):
        self.excel_path = excel_path
    
    def parse_email(self,email_body: str)->dict:
        #Normalize escaped line breaks if needed
        if "\\n" in email_body:
            email_body = email_body.encode().decode('unicode_escape')
        
        #Extract key-value pairs using regex
        matches = re.findall(r"^\s*(.+?):\s*(.+$)", email_body, re.MULTILINE)
        parsed_data = {key.strip().lower(): value.strip() for key, value in matches}
        return parsed_data
    
    def append_to_excel(self,parsed_data: dict):
        df = pd.DataFrame([parsed_data])
        
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

    
email_content = """Organization Name: Bitzer
Trigger name: CITRIX PVS Service up
Process name: SoapServer.exe
Process ID: 3992
User name: BITZER\\s00228
Session ID: 0
Computer name: DESON01057
Incident timestamp (UTC +2 W. Europe Standard Time): 8/27/2025 8:29:21 AM
"""
parser = EmailParser()
parser.process_email(email_content)