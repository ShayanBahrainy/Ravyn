import json
import sqlite3

import Content
import Accounts


class NotificationManager:
    MaxFeedLength = 20
    MaxTitleLength = 50
    def __init__(self, db: str):
        self.db = db
        with self.make_connection() as connection:
            connection.execute("pragma journal_mode=wal;")
            connection.execute("CREATE TABLE IF NOT EXISTS Notifications (USERID INTEGER, TYPE TEXT, CONTENTID TEXT);")

    def make_connection(self):
        return sqlite3.connect(self.db)
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
