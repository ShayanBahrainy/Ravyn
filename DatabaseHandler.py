from flask import Request, request 
import sqlite3
import datetime

class DatabaseHandler:
    def __init__(self):
        self.contexts = {}
        self.model = {}
        self.db_locations = {}
    def register_database(self, db: str, Class: type):
        if self.model.__contains__(Class):
            return
        self.model[db] = None
        self.db_locations[Class] = db
    def get_stateless_connection(self, Class: type):
        return sqlite3.connect(self.db_locations[Class])
    def get_connection(self, request: Request, Class: type) -> sqlite3.Connection:
        request = request._get_current_object()
        if not self.contexts.__contains__(request):
            self.contexts[request] = self.model.copy()
        db_location = self.db_locations[Class]
        if self.contexts[request][db_location] == None:
            self.contexts[request][db_location] = sqlite3.connect(self.db_locations[Class])
        return self.contexts[request][db_location]
    def request_finished(self, request):
        if self.contexts.__contains__(request):
            for connection in self.contexts[request].values():
                if connection:
                    connection.close()
