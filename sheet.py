import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from datetime import datetime

# from config import sheet_id

from threading import Lock

gsheet_lock = Lock()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GSheet:
    def __init__(self, sheet_id=None):
        self.sheet_id = sheet_id

        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        service = build('sheets', 'v4', credentials=creds)
        self.sheet = service.spreadsheets()
    
    def compose_range(self, sheet_name, row_count, start_row=2, start_col = 'A'):
        return f'{sheet_name}!{start_col}{start_row}:{start_row + row_count - 1}'
    
    def update(self, value: list, range_name: str, sheet_id=None):
        dt_string = datetime.now().strftime("%Y/%m/%d %H:%M:%S PST")
        if not sheet_id:
            sheet_id = self.sheet_id
        body = {
            'values': value
        }
        with gsheet_lock:
            try:

                self.sheet.values().update(
                    spreadsheetId=sheet_id, 
                    range = range_name.split('!')[0]+'!A1',
                    body = {'values': [[f'Last updated at {dt_string}']]},
                    valueInputOption='USER_ENTERED'
                ).execute()
                result = self.sheet.values().update(
                    spreadsheetId=sheet_id, 
                    range=range_name, 
                    body=body,
                    valueInputOption='USER_ENTERED'
                ).execute()
                return result.get('updatedCells')
            except:
                return 0

    def insert(self, value: list, range, sheet_id=None, shiftDimension='ROWS'):
        if not sheet_id:
            sheet_id = self.sheet_id
        with gsheet_lock:
            try:
                body = {
                    'requests': [
                        {
                            'insertRange': {
                                'range':range,
                                'shiftDimension': shiftDimension
                            }
                        },
                        {
                            'updateCells': {
                                'rows': [
                                    {'values': [{'userEnteredValue': {'stringValue':v}} for v in row]} for row in value
                                ],
                                'range': range,
                                'fields': '*'
                            }
                        }
                    ]
                }
                # print(body)
                request = self.sheet.batchUpdate(spreadsheetId=sheet_id, body=body)
                result = request.execute()
                return result
            except:
                pass
        # return self.update(value, 'Logs!2:2', sheet_id)

if __name__ == "__main__":
    sheet = GSheet()
    header = ['Hash', 'score', '0']
    cbs = [
        ['aaa', 20, '-']
    ]
    range_name = sheet.compose_range('challenges', len(cbs) + 1, 2)
    print(sheet.update([header, *cbs], range_name, sheet_id="----"))
    sheet.insert([['INFO','This is logs!']], {'sheetId':1493803901, "startRowIndex": 1, 'endRowIndex': 2}, sheet_id="---")