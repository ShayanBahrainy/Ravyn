import datetime
from flask import *
import os
import sqlite3
import requests

from Accounts import Accounts
from Content import ContentManager, Post, ReportManager, CommentManager, Comment, RatingManager

from oauthlib.oauth2 import WebApplicationClient

from DatabaseHandler import DatabaseHandler
from Notifications import NotificationManager, ViewedManager


with open("Data/Client.id") as f:
    GOOGLE_CLIENT_ID = f.read().strip()
with open("Data/Client.secret") as f:
    GOOGLE_CLIENT_SECRET = f.read().strip()
DEVELOPMENT = bool(os.environ.get("RAVYN_DEVELOPMENT_MODE"))

GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
BETA_ACCOUNTS = None
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

databasehandler = DatabaseHandler()

accounts = Accounts(databasehandler, "Data/Accounts.db", "Data/admin.txt", BETA_ACCOUNTS)
ratingmanager = RatingManager(databasehandler, "Data/Posts.db", accounts)
viewmanager = ViewedManager(databasehandler, "Data/Viewed.db")
contentmanager = ContentManager(databasehandler, "Data/Posts.db", accounts, viewmanager, ratingmanager)
notificationmanager = NotificationManager(databasehandler, "Data/Notifications.db")
commentmanager = CommentManager(databasehandler, "Data/Posts.db", contentmanager, notificationmanager)
reportmanager = ReportManager(databasehandler, "Data/Reports.db", contentmanager, commentmanager, ratingmanager)
client = WebApplicationClient(GOOGLE_CLIENT_ID)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["TEMPLATE_AUTO_RELOAD"] = True
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024

@app.route("/")
def index():
    if request.cookies.__contains__("AUTH"):
        user = accounts.is_logged_in(request.cookies["AUTH"])
        if user:
            notificationcount = notificationmanager.get_notification_count(user)
            if notificationcount > 8:
                notificationcount = "9+"
            if notificationcount == 0:
                notificationcount = None
            return render_template("index.html", feed=contentmanager.get_feed(user),notificationcount=notificationcount,user=user)
    return render_template("index.html",username=False, feed=contentmanager.get_feed())
@app.route("/post/<PostID>/uplift/",methods=["POST"])
def uplift(PostID):
    if request.cookies.__contains__("AUTH"):
        user = accounts.is_logged_in(request.cookies["AUTH"])
        if not user:
            return abort(403)
        post = contentmanager.get_post(PostID)
        if not post:
            return abort(404)
        ratingmanager.make_rating(user, post, 1)
        return 'Success!'
    return abort(401)
@app.route("/post/<PostID>/downshift/",methods=["POST"])
def downshift(PostID):
    if request.cookies.__contains__("AUTH"):
        user = accounts.is_logged_in(request.cookies["AUTH"])
        if not user:
            return abort(403)
        post = contentmanager.get_post(PostID)
        if not post:
            return abort(404)
        ratingmanager.make_rating(user, post, -1)
        return 'Success!'
    return abort(401)
@app.route("/notifications/")
def notification_index():
    if request.cookies.__contains__("AUTH"):
        user = accounts.is_logged_in(request.cookies["AUTH"])
        if user:
            data = notificationmanager.get_feed(user, commentmanager, contentmanager)
            response = Response(data, content_type="application/json")
            return response
    return abort(403)
@app.route("/notifications/clear/<ContentID>", methods=["POST"])
def clear_notification(ContentID):
    if request.cookies.__contains__("AUTH"):
        user = accounts.is_logged_in(request.cookies["AUTH"])
        if user:
            notificationmanager.clear_notification(user, ContentID)
            return 'Success!'
    return abort(403) 
@app.route("/profile/<UserID>")
def profile_page(UserID):
    user = accounts.get_public_face(UserID)
    if not user:
        abort(404)
    content_counts = contentmanager.get_content_count(user, commentmanager)
    page = request.args.get("page",0)
    try:
        page = int(page)
    except:
        page = 0
    posts = contentmanager.get_posts(user, page)
    return render_template("profile.html",User=user,content_counts=content_counts,posts=posts)
@app.route("/post/", methods=["GET","POST"])
def newPostPage():
    if not request.cookies.__contains__("AUTH"):
        return redirect("/")
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user:
        return redirect("/")
    if request.method == "GET":
        return render_template("new_post.html")
    if request.method == "POST":
        if not request.form.__contains__("Body"):
            return redirect("new_post.html",failReason="No body!")
        if not request.form.__contains__("Title"):
            return render_template("new_post.html",failReason="No title!")
        image = None
        if "AttachedImage" in request.files:
            image = request.files["AttachedImage"]
        result = contentmanager.create_post(request.form["Title"], request.form["Body"], user.id, image)
        if not result.success:
            return render_template("new_post.html", failReason=result.message)
        else:
            return redirect("/post/" + result.message)
@app.route("/report/<ContentID>", methods=["POST"])
def report(ContentID):
    if not request.cookies.__contains__("AUTH"):
        return abort(401)
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user:
        return abort(403)
    typ = reportmanager.get_type_by_id(ContentID)
    if typ == Post:
        content = contentmanager.get_post(ContentID)
    if typ == Comment:
        content = commentmanager.get_comment(ContentID)
    if not content:
        return abort(404)
    return str(reportmanager.make_report(content, user))
@app.route("/report/clear/<ContentID>",methods=["POST"])
def clear_report(ContentID):
    if not request.cookies.__contains__("AUTH"):
        return abort(403)
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user or not user.admin:
        return abort(403)
    typ = ReportManager.Convert_Type_To_Int(reportmanager.get_type_by_id(ContentID))
    reportmanager.clear_reports(ContentID, typ)
    return 'Success!'

@app.route("/report/delete/<ContentID>", methods=["POST"])
def delete_because_report(ContentID):
    if not request.cookies.__contains__("AUTH"):
        return abort(403)
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user or not user.admin:
        return abort(403)
    typ = ReportManager.Convert_Type_To_Int(reportmanager.get_type_by_id(ContentID))
    reportmanager.takedown(ContentID, typ)
    return 'Success!'
@app.route("/comment/<PostID>",methods=["POST"])
def comment_index(PostID):
    if not request.cookies.__contains__("AUTH"):
        return abort(403)
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user:
        return abort(403)
    assert request.content_type == "application/json", "Incorrect Content Type!"
    assert request.json["Comment"], "No comment submitted!"
    Post = contentmanager.get_post(PostID)
    if not Post:
        return abort(404)
    result = commentmanager.add_comment(Post, user, request.json["Comment"])
    if result:
        return 'Success!'
    else:
        return Response("Comment too short?",status=422)
@app.route("/admin/console/")
def admin_console():
    if not request.cookies.__contains__("AUTH"):
        return redirect("/")
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user or not user.admin:
        return redirect("/")
    feed = reportmanager.get_feed()
    return render_template("admin_console.html", reports=feed,type=type,str=str)
@app.route("/admin/announcement/",methods=["GET","POST"])
def admin_announcement():
    if not request.cookies.__contains__("AUTH"):
        return redirect("/")
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user or not user.admin:
        return redirect("/")
    if request.method == "GET":
        return render_template("admin_announce.html")
    data = request.get_json()
    result = notificationmanager.new_announcement(accounts, contentmanager, data["PostID"],data["Users"])
    return result
@app.route("/admin/user/<UserID>/",methods=["POST"])
def verify_user(UserID):
    if not request.cookies.__contains__("AUTH"):
        return abort(401)
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user or not user.admin:
        return abort(401)
    check_user = accounts.get_public_face(UserID)
    if not check_user:
        return abort(404)
    data = {}
    data["Username"] = check_user.name.capitalize()
    return json.dumps(data)
@app.route("/admin/post/<PostID>/",methods=["POST"])
def verify_post(PostID):
    if not request.cookies.__contains__("AUTH"):
        return abort(401)
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user or not user.admin:
        return abort(401)
    check_post = contentmanager.get_post(PostID)
    if not check_post:
        return abort(404)
    data = {}
    data["PostName"] = check_post.name
    data["Author"] = check_post.author
    data["PostID"] = check_post.id
    return json.dumps(data)
@app.route("/admin/leaderboard/")
def leaderboard():
    if not request.cookies.__contains__("AUTH"):
        return abort(401)
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user or not user.admin:
        return abort(401)
    return render_template("admin_leaderboard.html",Winners=ratingmanager.get_best_authors())
@app.route("/search/<Query>")
def search_index(Query):
    return contentmanager.search(Query, commentmanager)

@app.route("/post/<PostID>/")
def LoadPost(PostID):
    post = contentmanager.get_post(PostID)
    if not post:
        return "Not Found!" 
    #0 = No Comment Attempted, #1 = Fail, #2 Success
    commentSuccess = 0
    if request.args.get("commentSuccess") != None:
        if request.args.get("commentSuccess") == "True":
            commentSuccess = 2
        else:
            commentSuccess = 1
    Comments = commentmanager.get_feed(PostID,start_at=request.args.get("showComment"))
    if request.cookies.__contains__("AUTH"):
       user = accounts.is_logged_in(request.cookies["AUTH"])
       if user:
           viewmanager.viewed(user, post) 
    return render_template("post_view.html", post=post, PostID=PostID, Comments=Comments, commentSuccess=commentSuccess)
@app.route("/post/<PostID>/image/")
def serve_image(PostID):
    post = contentmanager.get_post(PostID)
    if not post:
        return "Not Found!" 
    if not request.cookies.__contains__("AUTH"):
       return abort(401)
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user:
        return abort(403)
    return send_from_directory("./Data/Images/", PostID + ".webp")
@app.route("/login/")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "google-auth",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/google-auth")
def googleauth():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = client.prepare_token_request(
    token_endpoint,
    authorization_response=request.url,
    redirect_url=request.base_url,
    code=code
)
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        cookie = accounts.login(unique_id, users_name, users_email, picture)
        if not cookie:
            return "User is not in beta test!", 403
        r = make_response(redirect("/"))
        r.set_cookie("AUTH", cookie)
        return r
    else:
        return "User email not available or not verified by Google.", 400

@app.teardown_request
def teardown(response):
    databasehandler.request_finished(request)

@app.route("/privacy-policy")
def privacypolicy():
    return privacypolicy

@app.route("/tos")
def tos():
    return tos
@app.errorhandler(requests.exceptions.ConnectionError)
def backend_connection_error():
    return 

if DEVELOPMENT:
    app.run(port=443,ssl_context="adhoc", debug=True)
