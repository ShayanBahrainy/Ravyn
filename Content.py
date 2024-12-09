import sqlite3
import uuid
import hashlib
import random
import math
import json

from Accounts import Accounts, User, UserPublicFace
from Notifications import NotificationManager

class Post:
    ContentPreviewMaxLength = 150
    def __init__(self, id: str, name: str, authorid: int, author: str, authorprofile: str, content: str, comments: list['Comment']=[]):
        self.id = id
        self.name = name
        self.author = author
        self.authorprofile = authorprofile
        self.authorid = authorid
        self.content = content
        self.showmore = len(content) > Post.ContentPreviewMaxLength
        if len(content) > Post.ContentPreviewMaxLength:
            self.contentpreview = self.content[:Post.ContentPreviewMaxLength + 1]
        else:
            self.contentpreview = content
        self.comments = comments
class ContentManager:
    MIN_TITLE_LENGTH = 10
    MAX_TITLE_LENGTH = 100
    MIN_BODY_LENGTH = 100
    MAX_FEED_LENGTH = 10
    MAX_SEARCH_RESULTS = 10
    def __init__(self, db, accounts: Accounts):
        self.db = db
        self.accounts = accounts
        with self.make_connection() as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Posts (ID TEXT, VIEWS INTEGER, OWNER INTEGER, BODY TEXT, TITLE TEXT);")
    
    def make_connection(self):
        return sqlite3.connect(self.db)
    def search(self, query: str, commentmanager: 'CommentManager'):
        SearchResults = []
        with self.make_connection() as connection:
            sqlitequery = "%" + query + "%"
            cursor = connection.execute("SELECT COUNT(*) FROM Posts WHERE BODY like ? or TITLE like ?;",(sqlitequery, sqlitequery))
            count = cursor.fetchone()[0]
            offset = math.floor(random.random() * count)
            if count < ContentManager.MAX_SEARCH_RESULTS:
                offset = 0
            cursor = connection.execute("SELECT * FROM Posts WHERE BODY like ? OR TITLE like ? LIMIT ? OFFSET ?;",(sqlitequery,sqlitequery,ContentManager.MAX_SEARCH_RESULTS,offset))
            results = cursor.fetchall()
        for result in results:
            ID, VIEWS, OWNER, BODY, TITLE = result
            SearchResult = {}
            SearchResult["URL"] = "/post/" + ID
            SearchResult["TITLE"] = TITLE
            SearchResults.append(SearchResult)
        data = {}
        data["Results"] = SearchResults.__add__(commentmanager.__search__(query))
        return json.dumps(data)
    def get_title(self, ID: str):
        with self.make_connection() as connection:
            r = connection.execute("SELECT Title FROM Posts WHERE ID=?;",(ID,))
            title = r.fetchone()
        if not (title == (0,) or title  == None):
            return title[0]
        return False
    
    @staticmethod
    def hash(text: str):
        return str(hashlib.sha256(text.encode()).digest())
    
    def validate_post_for_showing(self, id: str):
        with self.make_connection() as connection:
            r = connection.execute("SELECT EXISTS(SELECT 1 FROM Posts WHERE ID=?);",(id, ))
        if r.fetchone() == (1,):
            return True
        return False
    
    def get_feed(self):
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
                results.append(Post(post[0], post[4], user.id, user.name, user.profileimage, post[3]))
        return results
    def get_post(self, id: str):
        if not self.validate_post_for_showing(id):
            return
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT ID, TITLE, OWNER, BODY FROM Posts WHERE ID=?;",(id,))
            r = cursor.fetchone()
        user = self.accounts.get_public_face(r[2])
        return Post(r[0], r[1], user.id, user.name, user.profileimage, r[3])
    
    def create_post(self, title: str, body: str, user_id: int):
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
    MAX_SEARCH_RESULTS = 10
    def __init__(self, db: str, contentmanager: ContentManager, notificationmanager: NotificationManager):
        self.contentmanager = contentmanager
        self.notificationmanager = notificationmanager
        self.db = db
        with self.make_connection() as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Comments (PostID TEXT, CommentID TEXT, OWNER INTEGER, BODY TEXT);")
    def __search__(self, query: str):
        "ContentManager uses this to search comments, too. Returns list of relevant comments"
        SearchResults = []
        with self.make_connection() as connection:
            sqlitequery = "%" + query + "%"
            cursor = connection.execute("SELECT COUNT(*) FROM Comments WHERE BODY like ?;",(sqlitequery,))
            count = cursor.fetchone()[0]
            offset = math.floor(random.random() * count)
            if count < CommentManager.MAX_SEARCH_RESULTS:
                offset = 0
            cursor = connection.execute("SELECT * FROM Comments WHERE BODY like ? LIMIT ? OFFSET ?;",(sqlitequery,CommentManager.MAX_SEARCH_RESULTS,offset))
            results = cursor.fetchall()
        for result in results:
            PostID, CommentID, OWNER, BODY = result
            SearchResult = {}
            SearchResult["URL"] = "/post/" + PostID + "/?showComment=" + CommentID + "#" + CommentID
            index = BODY.lower().index(query.lower())
            startindex = index - 25
            endindex = index + 25
            if startindex < 0:
                0
            if endindex > len(BODY) - 1:
                endindex = len(BODY) - 1
            SearchResult["TITLE"] = BODY[startindex:endindex]
            SearchResults.append(SearchResult)
        return SearchResults
    def add_comment(self, Post: Post, Owner: User, Text: str) -> bool | str:
        if len(Text) < CommentManager.MinimumCommentLength:
            return "Comment is too short."
        with self.make_connection() as connection:
            id = str(uuid.uuid4())
            connection.execute("INSERT INTO Comments (PostID, CommentID, OWNER, BODY) VALUES (?,?,?,?);",(Post.id, id, Owner.id, Text,))
        self.notificationmanager.__add_comment__(Post.authorid,id)
        return True
    def get_comments(self, postid: str):
        comments = []
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT * FROM Comments WHERE PostID=?;",(postid,))
            results = cursor.fetchall()
            for comment in results:
                PostId, CommentID, Owner, Body = comment
                Owner = self.contentmanager.accounts.get_public_face(Owner)
                comments.append(Comment(CommentID, Body, Owner, PostId))
        return comments
    def get_feed(self, postid: str, start_at: str=None):
        "If start_at is given, comment feed will start at given comment."
        comments = []
        with self.make_connection() as connection:
            if start_at != None and self.get_comment(start_at) != None:
                cursor = connection.execute("SELECT rowid,* from Comments WHERE PostID=? AND CommentID=?;",(postid,start_at,))
                result = cursor.fetchone()
                offset, POSTID, COMMENTID, OWNER, BODY = result
                OWNER = self.contentmanager.accounts.get_public_face(OWNER)
                comments.append(Comment(COMMENTID,BODY,OWNER,POSTID))
            r = connection.execute("SELECT COUNT(*) FROM Comments WHERE PostID=?;",(postid,))
            count = r.fetchone()[0]
            if count == 0:
                return []
            if not start_at:
                offset = math.floor(random.random() * count) 
                if count < CommentManager.MAX_FEED_LENGTH:
                    offset = 0
            r = connection.execute("SELECT * FROM Comments WHERE PostID=? LIMIT ? OFFSET ?;",(postid, CommentManager.MAX_FEED_LENGTH, offset))
            results = r.fetchall()
            for comment in results:
                PostId, CommentID, Owner, Body = comment
                Owner = self.contentmanager.accounts.get_public_face(Owner)
                comments.append(Comment(CommentID, Body, Owner, PostId))
        return comments
    def get_comment(self, commentid: str):
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
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Comments WHERE CommentID=?;",(Comment.id,))
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

    def clear_reports(self, ContentID: str, typ: int):
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Reports WHERE CONTENTID=? AND TYPE=?;",(ContentID,typ))

    def takedown(self, ContentID: str, typ: int):
        Content = self.get_content(ContentID, typ)
        if type(Content) == Post:
            self.contentmanager.delete_post(Content.id)
        if type(Content) == Comment:
            self.commentmanager.delete_comment(Content)
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Reports WHERE CONTENTID=? AND TYPE=?;", (Content.id,typ))
    @staticmethod
    def Convert_Type_To_Int(obj: Post | Comment):
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
    def get_report_count(self, content: Post | Comment):
        Type = ReportManager.Convert_Type_To_Int(content)
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT COUNT(*) FROM Reports WHERE CONTENTID=? AND Type=?;",(content.id,Type))
            return cursor.fetchone()[0]
    def get_feed(self):
        results = []
        with self.make_connection() as connection:
            r = connection.execute("SELECT COUNT(*) FROM Reports;")
            count = r.fetchone()[0]
            if count == 0:
                return []
            
            offset = math.floor(random.random() * count) 
            if count < ReportManager.MAX_FEED_LENGTH:
                offset = 0
            r = connection.execute("SELECT CONTENTID, USERID FROM Reports GROUP BY CONTENTID LIMIT ? OFFSET ?;",(ReportManager.MAX_FEED_LENGTH, offset))
            reports = r.fetchall()
            for report in reports:
                typ = self.get_type_by_id(report[0])
                if typ == Post:
                    content = self.contentmanager.get_post(report[0])
                if typ == Comment:
                    content = self.commentmanager.get_comment(report[0])
                if content:
                    results.append(Report(content, self.get_report_count(content)))
        return results
    def get_content(self, contentid: str, typ: int):
        Type = ReportManager.Convert_Int_To_Type(typ)
        if Type == Post:
            return self.contentmanager.get_post(contentid)
        if Type == Comment:
            return self.commentmanager.get_comment(contentid)
class Report:
    def __init__(self, content: Post | Comment, reportquantity: int):
        self.content = content
        self.typ = ReportManager.Convert_Type_To_Int(content)
        self.reportcontent = content.name if type(content) == Post else content.content
        self.reportquantity = reportquantity