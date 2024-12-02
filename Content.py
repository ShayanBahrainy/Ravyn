import sqlite3
import uuid
import hashlib
import random
import math

from Accounts import Accounts, User, UserPublicFace

class Post:
    def __init__(self, id: str, name: str, author: int, authorprofile: str, content: str, comments: list['Comment']=[]):
        self.id = id
        self.name = name
        self.author = author
        self.authorprofile = authorprofile
        self.content = content
        self.comments = comments

class ContentManager:
    MIN_TITLE_LENGTH = 10
    MAX_TITLE_LENGTH = 100
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
                results.append(Post(post[0], post[4], user.name, user.profileimage, post[3]))
        return results
    def get_post(self, id: str) -> Post:
        if not self.validate_post_for_showing(id):
            return
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT ID, TITLE, OWNER, BODY FROM Posts WHERE ID=?;",(id,))
            r = cursor.fetchone()
        user = self.accounts.get_public_face(r[2])
        return Post(r[0], r[1], user.name, user.profileimage, r[3])
    
    def create_post(self, title: str, body: str, user_id: int) -> str | bool:
        if len(body) < ContentManager.MIN_BODY_LENGTH:
            return "Body too short"
        if len(title) < ContentManager.MIN_TITLE_LENGTH:
            return "Title too short"
        if len(title) > ContentManager.MAX_TITLE_LENGTH:
            return "Title too long"
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
class Comment:
    def __init__(self, id: str, content: str, owner: UserPublicFace, postid: str):
        self.id = id
        self.content = content
        self.owner = owner
        self.postid = postid
class CommentManager:
    MinimumCommentLength = 10
    MAX_FEED_LENGTH = 100
    def __init__(self, db: str, contentmanager: ContentManager):
        self.contentmanager = contentmanager
        self.db = db
        with self.make_connection() as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Comments (PostID TEXT, CommentID TEXT, OWNER INTEGER, BODY TEXT);")
    def add_comment(self, Post: Post, Owner: User, Text: str) -> str:
        if len(Text) < CommentManager.MinimumCommentLength:
            return "Comment is too short."
        with self.make_connection() as connection:
            id = str(uuid.uuid4())
            connection.execute("INSERT INTO Comments (PostID, CommentID, OWNER, BODY) VALUES (?,?,?,?);",(Post.id, id, Owner.id, Text,))
        return 'Success!'
    def get_comments(self, postid: str) -> list[Comment]:
        comments = []
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT * FROM Comments WHERE PostID=?;",(postid,))
            results = cursor.fetchall()
            for comment in results:
                PostId, CommentID, Owner, Body = comment
                Owner = self.contentmanager.accounts.get_public_face(Owner)
                comments.append(Comment(CommentID, Body, Owner, PostId))
        return comments
    def get_feed(self, postid: str) -> list[Comment]:
        comments = []
        with self.make_connection() as connection:
            r = connection.execute("SELECT COUNT(*) FROM Comments WHERE PostID=?;",(postid,))
            count = r.fetchone()[0]
            if count == 0:
                return []
            offset = math.floor(random.random() * count) 
            if count < CommentManager.MAX_FEED_LENGTH:
                offset = 0
            r = connection.execute("SELECT * FROM Comments WHERE PostID=? LIMIT ? OFFSET ?;",(postid, ContentManager.MAX_FEED_LENGTH, offset))
            results = r.fetchall()
            for comment in results:
                PostId, CommentID, Owner, Body = comment
                Owner = self.contentmanager.accounts.get_public_face(Owner)
                comments.append(Comment(CommentID, Body, Owner, PostId))
        return comments
    def get_comment(self, commentid: str) -> None | Comment:
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT EXISTS(SELECT 1 FROM Comments WHERE CommentID=?);",(commentid,))
            result = cursor.fetchone()
            if result != (1,):
                return
            cursor = connection.execute("SELECT * FROM Comments WHERE CommentID=?;",(commentid,))
            result = cursor.fetchone()
        postid, commentid, owner, content = result
        owner = self.contentmanager.accounts.get_public_face(owner)
        return Comment(commentid, content, owner, postid)
    def delete_comment(self, Comment: Comment):
        with self.make_comment() as connection:
            connection.execute("DELETE FROM Comments WHERE CommentID=?;",(Comment.id))
    def make_connection(self):
        return sqlite3.connect(self.db)
class ReportManager:
    MAX_FEED_LENGTH = 25
    def __init__(self, db: str, contentmanager: ContentManager, commentmanager: CommentManager):
        self.db = db
        self.contentmanager = contentmanager
        self.commentmanager = commentmanager
        #In DB, type 0 means post, type 1 means comment
        with self.make_connection() as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Reports (CONTENTID TEXT, TYPE INTEGER, USERID INTEGER);")

    def clear_reports(self, ContentID: str, typ: int) -> None:
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Reports WHERE CONTENTID=? AND TYPE=?;",(ContentID,typ))

    def takedown(self, ContentID: str, typ: int) -> bool:
        Content = self.get_content(ContentID, typ)
        if type(Content) == Post:
            self.contentmanager.delete_post(Content.id)
        if type(Content) == Comment:
            self.commentmanager.delete_comment(Content)
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Reports WHERE CONTENTID=? AND TYPE=?;", (Content.id,typ))
    @staticmethod
    def Convert_Type_To_Int(obj: Post | Comment) -> int:
        if isinstance(obj, type):
            if obj == Post:
                return 0
            if obj == Comment:
                return 1 
        if type(obj) == Post:
            return 0
        if type(obj) == Comment:
            return 1
    @staticmethod
    def Convert_Int_To_Type(integ: int):
        if integ == 0:
            return Post
        if integ == 1:
            return Comment
    def make_report(self, content: Post | Comment, user: User):
        Type = ReportManager.Convert_Type_To_Int(content)
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT EXISTS(SELECT 1 FROM Reports WHERE USERID=? AND CONTENTID=? AND Type=?);",(user.id,content.id,Type))
            result = cursor.fetchone()
            if result == (1,):
                return False
            cursor = connection.execute("INSERT INTO Reports (CONTENTID,TYPE,USERID) VALUES (?,?,?);", (content.id, Type, user.id))
        return True
    def get_type_by_id(self, contentid: str):
        if self.commentmanager.get_comment(contentid):
            return Comment
        return Post
    def make_connection(self):
        return sqlite3.connect(self.db)
    def get_report_count(self, content: Post | Comment) -> int:
        Type = ReportManager.Convert_Type_To_Int(content)
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT COUNT(*) FROM Reports WHERE CONTENTID=? AND Type=?;",(content.id,Type))
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
            r = connection.execute("SELECT CONTENTID, USERID FROM Reports GROUP BY CONTENTID LIMIT ? OFFSET ?;",(ContentManager.MAX_FEED_LENGTH, offset))
            reports = r.fetchall()
            for report in reports:
                content = self.contentmanager.get_post(report[0])
                if content:
                    results.append(Report(content, self.get_report_count(content)))
        return results
    def get_content(self, contentid: str, typ: int) -> Post | Comment:
        Type = ReportManager.Convert_Int_To_Type(typ)
        if Type == Post:
            return self.contentmanager.get_post(contentid)
        if Type == Comment:
            return self.commentmanager.get_comment(contentid)
class Report:
    def __init__(self, post: Post, reportquantity: int):
        self.post = post
        self.reportquantity = reportquantity