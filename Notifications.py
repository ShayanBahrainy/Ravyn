import json
import sqlite3
from flask import request
import Content
import Accounts
from DatabaseHandler import DatabaseHandler

InsertOrIncreaseViewCountQuery = """UPDATE Viewed
SET count = count + 1
WHERE USERID = ? AND CONTENTID = ?;

INSERT INTO Viewed (USERID, CONTENTID)
VALUES (?, ?)
WHERE NOT EXISTS (SELECT 1 FROM Viewed WHERE USERID = ? AND CONTENID=?);"""

class ViewedManager:
    def __init__(self, dbhandler: DatabaseHandler, db: str):
        self.dbhandler = dbhandler
        dbhandler.register_database(db, ViewedManager)
        with dbhandler.get_stateless_connection(ViewedManager) as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Viewed (USERID INTEGER, CONTENTID TEXT, TIMES INTEGER); ")
    def make_connection(self):
        return self.dbhandler.get_connection(request, ViewedManager)
    def viewed(self, User: 'Accounts.User', Post: 'Content.Post'):
        print(str(User) + " viewed " + str(Post))
        with self.make_connection() as conenction:
            conenction.execute(InsertOrIncreaseViewCountQuery, (User.id, Post.id, User.id, Post.id, User.id, Post.id))
    def has_viewed(self, User: 'Accounts.User', Post: 'Content.Post') -> int:
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT Times FROM Viewed WHERE USERID=? AND CONTENTID=?;",(User.id, Post.id))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return 0
    def has_viewed_many(self):
        pass

class NotificationManager:
    MaxFeedLength = 20
    MaxTitleLength = 50
    def __init__(self, dbhandler: DatabaseHandler, db: str):
        self.dbhandler = dbhandler
        dbhandler.register_database(db, NotificationManager)
        with dbhandler.get_stateless_connection(NotificationManager) as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Notifications (USERID INTEGER, TYPE TEXT, CONTENTID TEXT);")

    def make_connection(self):
        return self.dbhandler.get_connection(request, NotificationManager)
    def delete_comment(self, Comment: 'Content.Comment'):
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Notifications WHERE CONTENTID=?;",(Comment.id,))
    def __add_comment__(self, UserID: int, CommentID: str):
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT EXISTS (SELECT * FROM Notifications WHERE USERID=? AND CONTENTID=?);",(UserID, CommentID))
            if cursor.fetchone() == (1,):
                return 
            connection.execute("INSERT INTO Notifications (USERID, TYPE, CONTENTID) VALUES (?, ?, ?);", (UserID, "Comment", CommentID))
        
    def get_notification_count(self, User: 'Accounts.User') -> int:
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT COUNT(*) FROM Notifications WHERE USERID=?;",(User.id,))
            return cursor.fetchone()[0]
        
    def get_feed(self, User: 'Accounts.User', CommentManager: 'Content.CommentManager') -> str:
        Feed = []
        with self.make_connection() as connection:
            cursor = connection.execute("SELECT * FROM Notifications WHERE USERID=? LIMIT ?;",(User.id,NotificationManager.MaxFeedLength))
            results = cursor.fetchall()
            for notification in results:
                USERID, TYPE, CONTENTID = notification
                if TYPE != "Comment":
                    continue
                Comment = CommentManager.get_comment(CONTENTID)
                Result = {}
                Result["HREF"] = "/post/" + Comment.postid + "/?showComment=" + Comment.id
                Result["ID"] = Comment.id
                if len(Comment.content) < NotificationManager.MaxTitleLength:
                    Result["TITLE"] = Comment.content
                else: 
                    Result["TITLE"] = Comment.content[:NotificationManager.MaxTitleLength + 1] + "..."
                Feed.append(Result)
        Data = {}
        Data["Notifications"] = Feed
        return json.dumps(Data)
    def clear_notification(self, User: 'Accounts.User', ContentID: str):
        with self.make_connection() as connection:
            connection.execute("DELETE FROM Notifications WHERE USERID=? AND CONTENTID=?;",(User.id, ContentID))
