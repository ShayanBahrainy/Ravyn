import uuid
import hashlib
import random
import math
import json
import time
from flask import request

from Accounts import Accounts, User, UserPublicFace
from DatabaseHandler import DatabaseHandler
from Notifications import NotificationManager, ViewedManager

class Post:
    ContentPreviewMaxLength = 150
    def __init__(self, id: str, name: str, authorid: int, author: str, authorprofile: str, content: str, comments: list['Comment']=[], score:int=0):
        self.id = id
        self.name = name
        self.author = author
        self.authorprofile = authorprofile
        self.authorid = authorid
        self.content = content
        self.score = score
        self.showmore = len(content) > Post.ContentPreviewMaxLength
        if len(content) > Post.ContentPreviewMaxLength:
            self.contentpreview = self.content[:Post.ContentPreviewMaxLength + 1]
        else:
            self.contentpreview = content
        self.comments = comments
    def set_score(self, score: int=0):
        self.score = score
class RatingManager:
    BestAuthorStatement = """
    SELECT Owner, SUM(Rating) AS TotalRating
    FROM Ratings
    WHERE TimeStamp >= ?
    GROUP BY Owner
    ORDER BY TotalRating DESC
    LIMIT 5;
    """
    BestPostStatement = """
    SELECT ContentID, SUM(Rating) AS TotalRating
    FROM Ratings
    WHERE TimeStamp >= ?
    GROUP BY Owner
    ORDER BY TotalRating DESC
    LIMIT 5;
    """
    TimePeriod = 7 * 24 * 60 * 60
    def __init__(self, dbhandler: DatabaseHandler, db: str, accounts: Accounts):
        self.dbhandler = dbhandler
        self.dbhandler.register_database(db, RatingManager)
        self.accounts = accounts
        with self.dbhandler.get_stateless_connection(RatingManager) as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Ratings (Rater INTEGER, Owner INTEGER, ContentID TEXT, Rating INTEGER, TimeStamp INTEGER, UNIQUE(Rater,ContentID));")
    def make_connection(self):
        return self.dbhandler.get_connection(request, RatingManager)
    def make_rating(self, Rater: User, Post: Post, Rating: int):
        with self.make_connection() as connection:
            cursor = connection.execute("DELETE FROM Ratings WHERE Rater=? AND ContentID=?;",(Rater.id, Post.id))
            cursor.execute("INSERT INTO Ratings (Rater, Owner, ContentID, Rating, TimeStamp) VALUES (?,?,?,?,?);",(Rater.id, Post.authorid, Post.id, Rating, int(time.time())))
    def get_rating(self, Post: Post) -> int:
        connection = self.make_connection()
        cursor = connection.execute("SELECT SUM(Rating) FROM Ratings WHERE CONTENTID=?;",(Post.id,))
        r = cursor.fetchone()[0]
        return r if r else 0
    def __get_best_authors_id__(self, time: int) -> list[int]:
        connection = self.make_connection()
        cursor = connection.execute(RatingManager.BestAuthorStatement, (time,))
        return [AuthorId[0] for AuthorId in cursor.fetchall()]
    def get_best_authors(self) -> list[UserPublicFace]:
        t = int(time.time()) - RatingManager.TimePeriod
        results = []
        for UserId in self.__get_best_authors_id__(t):
            results.append(self.accounts.get_public_face(UserId))
        return results
    def get_best_post(self, time: int) -> int:
        connection = self.make_connection()
        cursor = connection.execute(RatingManager.BestPostStatement, (time,))
        return cursor.fetchone()[1]

class ContentManager:
    MIN_TITLE_LENGTH = 10
    MAX_TITLE_LENGTH = 100
    MIN_BODY_LENGTH = 100
    MAX_FEED_LENGTH = 10
    MAX_SEARCH_RESULTS = 10
    ProfilePostsLength = 20
    FeedQuery = """
    SELECT * FROM Posts WHERE ID NOT IN ({bindings}) ORDER BY TIME DESC LIMIT ? OFFSET ?;
    """
    def __init__(self, dbhandler: DatabaseHandler, db: str, accounts: Accounts, viewmanager: ViewedManager, ratingmanager: RatingManager):
        self.dbhandler = dbhandler
        self.dbhandler.register_database(db, ContentManager)
        self.accounts = accounts
        self.viewmanager = viewmanager
        self.ratingmanager = ratingmanager
        with dbhandler.get_stateless_connection(ContentManager) as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Posts (ID TEXT, TIME INTEGER, OWNER INTEGER, BODY TEXT, TITLE TEXT);")
    
    def make_connection(self):
        return self.dbhandler.get_connection(request, ContentManager)
    def get_content_count(self, User: User | UserPublicFace, commentmanager: 'CommentManager') -> dict:
        connection = self.make_connection()
        cursor = connection.execute("SELECT COUNT(*) FROM Posts WHERE OWNER=?;",(User.id,))
        post_count = cursor.fetchone()[0]
        count = {
            "posts" : post_count,
            "comments" : commentmanager.get_comment_count(User)
        }
        return count
    def get_posts(self, User: User | UserPublicFace, Page: int):
        connection = self.make_connection()
        offset = ContentManager.ProfilePostsLength * Page
        limit = ContentManager.ProfilePostsLength
        cursor = connection.execute("SELECT * FROM Posts WHERE OWNER=? LIMIT ? OFFSET ?;",(User.id,limit,offset))
        results =  []
        for postdata in cursor.fetchall():
            user = self.accounts.get_public_face(postdata[2])
            post = Post(postdata[0], postdata[4], user.id, user.name, user.profileimage, postdata[3])
            post.set_score(self.ratingmanager.get_rating(post))
            results.append(post)
        return results
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
        data["Results"] = SearchResults.__add__(commentmanager.search(query))
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
    
    def get_feed(self, User: User=None):
        results = []
        with self.make_connection() as connection:
            r = connection.execute("SELECT COUNT(*) FROM Posts;")
            count = r.fetchone()[0]
            if count == 0:
                return []
            
            offset = math.floor(random.random() * count) 
            if count < ContentManager.MAX_FEED_LENGTH:
                offset = 0
            ids = self.viewmanager.has_viewed_ids(User) if User else ()
            r = connection.execute(ContentManager.FeedQuery.format(bindings=', '.join(['?'] * len(ids))),ids + (ContentManager.MAX_FEED_LENGTH, offset))
            posts = r.fetchall()
            ids = tuple([post[0] for post in posts])
            if User and len(posts) < ContentManager.MAX_FEED_LENGTH:
                r = connection.execute(ContentManager.FeedQuery.format(bindings=', '.join(['?'] * len(ids))),ids + (ContentManager.MAX_FEED_LENGTH, offset))
            posts += r.fetchall()
            for postdata in posts:
                user = self.accounts.get_public_face(postdata[2])
                post = Post(postdata[0], postdata[4], user.id, user.name, user.profileimage, postdata[3])
                post.set_score(self.ratingmanager.get_rating(post))
                results.append(post)
        return results
    def get_post(self, id: str):
        if not self.validate_post_for_showing(id):
            return
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT ID, TITLE, OWNER, BODY FROM Posts WHERE ID=?;",(id,))
            r = cursor.fetchone()
        user = self.accounts.get_public_face(r[2])
        post = Post(r[0], r[1], user.id, user.name, user.profileimage, r[3])
        post.set_score(self.ratingmanager.get_rating(post))
        return post
    def create_post(self, title: str, body: str, user_id: int):
        if len(body) < ContentManager.MIN_BODY_LENGTH:
            return [False, "Body too short"]
        if len(title) < ContentManager.MIN_TITLE_LENGTH:
            return [False,"Title too short"]
        if len(title) > ContentManager.MAX_TITLE_LENGTH:
            return [False, "Title too long"]
        with self.make_connection() as connection:
            r = connection.execute("SELECT EXISTS(SELECT 1 FROM Posts WHERE BODY = ?);", (body,))
            if r.fetchone() == (1,):
                return "Post already exists"
            id = str(uuid.uuid4())
            r = connection.execute("INSERT INTO Posts (ID, TIME, OWNER, BODY, TITLE) VALUES (?,?,?,?,?);", (id, int(time.time()), user_id, body, title,))
        return [True,id]
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
    def __init__(self, dbhandler: DatabaseHandler, db: str, contentmanager: ContentManager, notificationmanager: NotificationManager):
        self.contentmanager = contentmanager
        self.notificationmanager = notificationmanager
        self.dbhandler = dbhandler
        dbhandler.register_database(db, CommentManager)
        with dbhandler.get_stateless_connection(CommentManager) as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Comments (PostID TEXT, CommentID TEXT, OWNER INTEGER, BODY TEXT);")
    def search(self, query: str):
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
    def get_comment_count(self, User: User | UserPublicFace) -> int:
        connection = self.make_connection()
        cursor = connection.execute("SELECT COUNT(*) FROM Comments WHERE OWNER=?;",(User.id,))
        return cursor.fetchone()[0]
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
        self.notificationmanager.delete_comment(Comment)
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Comments WHERE CommentID=?;",(Comment.id,))
    def delete_post_comments(self, PostID: str):
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Comments WHERE PostID=?;",(PostID,))
    def make_connection(self):
        return self.dbhandler.get_connection(request, CommentManager)
class ReportManager:
    MAX_FEED_LENGTH = 25
    def __init__(self, dbhandler: DatabaseHandler, db: str, contentmanager: ContentManager, commentmanager: CommentManager):
        self.dbhandler = dbhandler
        dbhandler.register_database(db, ReportManager)
        self.contentmanager = contentmanager
        self.commentmanager = commentmanager
        #In DB, type 0 means post, type 1 means comment
        with dbhandler.get_stateless_connection(ReportManager) as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Reports (CONTENTID TEXT, TYPE INTEGER, USERID INTEGER);")

    def clear_reports(self, ContentID: str, typ: int):
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Reports WHERE CONTENTID=? AND TYPE=?;",(ContentID,typ))

    def takedown(self, ContentID: str, typ: int):
        Content = self.get_content(ContentID, typ)
        if type(Content) == Post:
            self.contentmanager.delete_post(Content.id)
            self.commentmanager.delete_post_comments(Content.id)
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
        return self.dbhandler.get_connection(request, ReportManager)
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
    MaxReportContent = 50
    def __init__(self, content: Post | Comment, reportquantity: int):
        self.content = content
        self.typ = ReportManager.Convert_Type_To_Int(content)
        self.reportcontent = content.name if type(content) == Post else content.content
        if len(self.reportcontent) > Report.MaxReportContent:
            self.reportcontent = self.reportcontent[:Report.MaxReportContent + 1]
        self.reportcontent.replace("\n","")
        self.reportquantity = reportquantity