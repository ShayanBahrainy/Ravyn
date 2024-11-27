import sqlite3
import uuid
import hashlib
import random
import math

from werkzeug.datastructures.file_storage import FileStorage
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from Accounts import Accounts, User

class Post:
    def __init__(self, id, name, author, authorprofile, content):
        self.id = id
        self.name = name
        self.author = author
        self.authorprofile = authorprofile
        self.content = content

class ContentManager:
    MIN_TITLE_LENGTH = 15
    MIN_BODY_LENGTH = 100
    MAX_FEED_LENGTH = 10
    def __init__(self, db, accounts: Accounts):
        self.db = db
        self.accounts = accounts
        with self.make_connection() as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Posts (ID TEXT, VIEWS INTEGER, OWNER INTEGER, BODY TEXT, TITLE TEXT);")
    
    def make_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db)
    
    def get_title(self, ID: str) -> str | bool:
        with self.make_connection() as connection:
            r = connection.execute("SELECT Title FROM Posts WHERE ID=?;",(ID,))
            title = r.fetchone()
        if not (title == (0,) or title  == None):
            return title[0]
        return False
    
    @staticmethod
    def hash(text: str) -> str:
        return str(hashlib.sha256(text.encode()).digest())
    
    def validate_post_for_showing(self, id: str):
        with self.make_connection() as connection:
            r = connection.execute("SELECT EXISTS(SELECT 1 FROM Posts WHERE ID=?);",(id, ))
        if r.fetchone() == (1,):
            return True
        return False
    
    def get_feed(self) -> list[Post]:
        results = []
        with self.make_connection() as connection:
            r = connection.execute("SELECT COUNT(*) FROM Posts;")
            count = r.fetchone()[0]
            if count == 0:
                return []
            
            offset = math.floor(random.random() * count) 
            if count < ContentManager.MAX_FEED_LENGTH:
                offset = 0
            r = connection.execute("SELECT * FROM Posts LIMIT ? OFFSET ?;",(ContentManager.MAX_FEED_LENGTH, offset))
            posts = r.fetchall()
            for post in posts:
                user = self.accounts.get_public_face(post[2])
                results.append(Post(post[0], post[4], user[0], user[1], post[3]))
        return results

    def get_post(self, id: str) -> Post:
        if not self.validate_post_for_showing(id):
            return
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT ID, TITLE, OWNER, BODY FROM Posts WHERE ID=?;",(id,))
            r = cursor.fetchone()
        public_face = self.accounts.get_public_face(r[2])
        return Post(r[0], r[1], public_face[0], public_face[1], r[3])
    def create_post(self, title: str, body: str, user_id: int) -> str | bool:
        #Check if PDF is safe to save.

        if len(body) < ContentManager.MIN_BODY_LENGTH:
            return "Body too short"
        if len(title) < ContentManager.MIN_TITLE_LENGTH:
            return "Title too short"
        
        with self.make_connection() as connection:
            r = connection.execute("SELECT EXISTS(SELECT 1 FROM Posts WHERE BODY = ?);", (body,))
            if r.fetchone() == (1,):
                return "Post already exists"
            id = str(uuid.uuid4())
            r = connection.execute("INSERT INTO Posts (ID, VIEWS, OWNER, BODY, TITLE) VALUES (?,?,?,?,?);", (id, 0, user_id, body, title,))
        return True
    def delete_post(self, id: str):
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Posts WHERE ID=?;",(id,))
class ReportManager:
    MAX_FEED_LENGTH = 25
    def __init__(self, db: str, contentmanager: ContentManager):
        self.db = db
        self.contentmanager = contentmanager
        with self.make_connection() as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Reports (POSTID TEXT, USERID INTEGER);")

    def clear_reports(self, PostID: str) -> None:
        with self.make_connection() as connection:
            cursor = connection.execute("DELETE FROM Reports WHERE POSTID=?;",(PostID,))
    def takedown_post(self, PostID: str) -> bool:
        self.contentmanager.delete_post(PostID)
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Reports WHERE POSTID=?;", (PostID,))
    def make_report(self, post: Post, user: User):
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT EXISTS(SELECT 1 FROM Reports WHERE USERID=? AND POSTID=?);",(user.id,post.id))
            result = cursor.fetchone()
            if result == (1,):
                return False
            cursor = connection.execute("INSERT INTO Reports (POSTID,USERID) VALUES (?,?);", (post.id, user.id))
        return True
    def make_connection(self):
        return sqlite3.connect(self.db)
    def get_report_count(self, post: Post) -> int:
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT COUNT(*) FROM Reports WHERE POSTID=?;",(post.id,))
            return cursor.fetchone()[0]
    def get_feed(self) -> list[Post]:
        results = []
        with self.make_connection() as connection:
            r = connection.execute("SELECT COUNT(*) FROM Reports;")
            count = r.fetchone()[0]
            if count == 0:
                return []
            
            offset = math.floor(random.random() * count) 
            if count < ReportManager.MAX_FEED_LENGTH:
                offset = 0
            r = connection.execute("SELECT POSTID, USERID FROM Reports GROUP BY POSTID LIMIT ? OFFSET ?;",(ContentManager.MAX_FEED_LENGTH, offset))
            reports = r.fetchall()
            for report in reports:
                print(report[0])
                post = self.contentmanager.get_post(report[0])
                results.append(Report(post, self.get_report_count(post)))
        return results
class Report:
    def __init__(self, post: Post, reportquantity: int):
        self.post = post
        self.reportquantity = reportquantity