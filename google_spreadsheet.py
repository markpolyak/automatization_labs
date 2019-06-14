import gspread
from oauth2client.service_account import ServiceAccountCredentials


class SpreadSheet:
    def __init__(self, json_keyfile, name):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile, scope)
        connection = gspread.authorize(credentials)
        self._spreadsheet = connection.open(name)

    def get_worksheet(self, name):
        return self._spreadsheet.worksheet(name)
