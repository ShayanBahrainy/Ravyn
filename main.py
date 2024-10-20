from flask import Flask
import os

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template()

@app.route("/privacy-policy")
def privacypolicy():
    return privacypolicy

@app.route("/tos")
def tos():
    return tos

app.run(port=443)