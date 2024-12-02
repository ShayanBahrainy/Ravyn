from flask import *
import os
import sqlite3
import requests

from Accounts import Accounts
from Content import ContentManager, ReportManager, CommentManager

from oauthlib.oauth2 import WebApplicationClient


with open("Client.id") as f:
    GOOGLE_CLIENT_ID = f.read()
with open("Client.secret") as f:
    GOOGLE_CLIENT_SECRET = f.read()
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
BETA_ACCOUNTS = "BETA_ACCOUNTS.txt"
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

accounts = Accounts("Accounts.db", "admin.txt", BETA_ACCOUNTS)
contentmanager = ContentManager("Posts.db", accounts)
commentmanager = CommentManager("Posts.db", contentmanager)
reportmanager = ReportManager("Reports.db", contentmanager, commentmanager)
client = WebApplicationClient(GOOGLE_CLIENT_ID)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1000 * 1000
app.config['UPLOAD_FOLDER'] = "Papers"
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

@app.route("/")
def index():
    if request.cookies.__contains__("AUTH"):
        user = accounts.is_logged_in(request.cookies["AUTH"])
        if user:
            return render_template("index.html",username=user.username, picture=user.picture, feed=contentmanager.get_feed(),admin=user.admin)
    return render_template("index.html",username=False, feed=contentmanager.get_feed())

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
        r = contentmanager.create_post(request.form["Title"], request.form["Body"], user.id)
        if type(r) != str:
            return redirect("/")
        return render_template("new_post.html", failReason=r)
@app.route("/report/<PostID>", methods=["POST"])
def report(PostID):
    if not request.cookies.__contains__("AUTH"):
        return redirect("/")
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user:
        return abort(403)
    post = contentmanager.get_post(PostID)
    if not post:
        return abort(404)
    return str(reportmanager.make_report(post, user))
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
    return commentmanager.add_comment(Post, user, request.json["Comment"])
@app.route("/admin/console/")
def admin_console():
    if not request.cookies.__contains__("AUTH"):
        return redirect("/")
    user = accounts.is_logged_in(request.cookies["AUTH"])
    if not user or not user.admin:
        return redirect("/")
    feed = reportmanager.get_feed()
    return render_template("admin_console.html", reports=feed)

@app.route("/post/<PostID>")
def LoadPaper(PostID):
    post = contentmanager.get_post(PostID)
    if not post:
        return "Not Found!" 
    return render_template("post_view.html", post=post, PostID=PostID, Comments=commentmanager.get_feed(PostID))

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
    
@app.route("/privacy-policy")
def privacypolicy():
    return privacypolicy

@app.route("/tos")
def tos():
    return tos
@app.errorhandler(requests.exceptions.ConnectionError)
def backend_connection_error():
    return 
app.run(port=443,ssl_context="adhoc", debug=False)