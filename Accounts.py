import sqlite3
import os
from flask import request
from DatabaseHandler import DatabaseHandler

class User:
    def __init__(self, accounts: 'Accounts', id, username, email, picture, cookie):
        self.accounts = accounts
        self.username = username
        self.email = email
        self.picture = picture
        self.id = id
        self.cookie = cookie
        self.admin = email in accounts.admin_emails
    def logout(self):
        del self.accounts[self.cookie]
class UserPublicFace:
    "Public Facing User Object"
    def __init__(self, name: str, profileimage: str, id: int):
        self.name = name
        self.id = id
        self.profileimage = profileimage
class Accounts:
    def __init__(self, dbhandler: DatabaseHandler, db: str, admin_file: str, beta_users: os.PathLike=None):
        "IF beta_users is passed, beta user emails will be loaded from text file and no one else can sign in."
        self.dbhandler = dbhandler
        self.dbhandler.register_database(db, Accounts)
        with dbhandler.get_stateless_connection(Accounts) as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Accounts (ID INTEGER, USERNAME TEXT, EMAIL TEXT, PICTURE TEXT);")
        self.transactionstack = []
        self.userobjects = {}
        with open(admin_file) as f:
            self.admin_emails = f.read().split("\n")
        if beta_users:
            with open(beta_users) as f:
                self.beta_users = f.read().split("\n")
    def get_public_face(self, id):
        "Returns tuple where first object is account's username, second is picture url."
        with self.make_connection() as connection:
            r = connection.execute("SELECT USERNAME,PICTURE,ID FROM Accounts WHERE ID = ?;", (id,))
            result = r.fetchone()
            if result:
                return UserPublicFace(result[0],result[1],result[2])
        print(connection)
        return False
    def make_connection(self):
        return self.dbhandler.get_connection(request, Accounts)
    def create_account(self, ID, USERNAME, EMAIL, PICTURE): 
        with self.make_connection() as connection:   
            connection.execute("INSERT INTO Accounts (ID, USERNAME, EMAIL, PICTURE) VALUES (?,?,?,?);",(ID,USERNAME,EMAIL,PICTURE,))
        cookie = self.create_cookie()
        self.userobjects[cookie] = User(self, ID, USERNAME, EMAIL, PICTURE, cookie)
        return cookie 
    def logout(self, cookie):
        del self.userobjects[cookie]
    def login(self, unique_id, users_name, users_email, picture):
        if hasattr(self, "beta_users") and users_email not in self.beta_users:
            return False
        with self.make_connection() as connection:
            r = connection.execute('SELECT EXISTS(SELECT 1 FROM Accounts WHERE ID=?);', (unique_id,))
        if r.fetchone() == (1,):
            cookie = self.create_cookie()
            self.userobjects[cookie] = User(self, unique_id, users_name, users_email, picture, cookie)
            return cookie
        else:
            return self.create_account(unique_id, users_name, users_email, picture)
    def create_cookie(self):
        cookie = str(os.urandom(64))
        while self.userobjects.__contains__(cookie):
            cookie = str(os.urandom(64))
        return cookie
    def is_logged_in(self, auth_cookie):
        if self.userobjects.__contains__(auth_cookie):
            return self.userobjects[auth_cookie]
        else:
            return False
