import os
import uuid

from ml import ml

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import request
from flask import Flask, render_template, redirect, url_for, session
from dotenv import load_dotenv
from flask_oauthlib.client import OAuth

load_dotenv()

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get('SECRET_KEY')  # Replace with your secret key

# Set up OAuth for Spotify
oauth = OAuth(app)
spotify = oauth.remote_app(
    "spotify",
    consumer_key=os.environ.get('CLIENT_ID'),
    consumer_secret=os.environ.get('CLIENT_SECRET'),
    base_url="https://api.spotify.com/v1/",
    request_token_url=None,
    access_token_url="https://accounts.spotify.com/api/token",
    authorize_url="https://accounts.spotify.com/authorize",
)

# Routes
@app.route("/")
def home():
    if "spotify_token" in session:
        # Render home page if authenticated
        return render_template("home.html")
    else:
        # Redirect to login page if not authenticated
        return render_template("login.html")

@app.route("/name", methods=["POST"])
def name():
    # artists_line_up = request.form["artists_line_up"]
    playlist_uri = request.form["playlist_uri"]
    # req_name = request.form["name"]
    # print(one, two, three)
    # os.system('python ml.py {} {}'.format(req_name, playlist_uri))
    ml(playlist_uri)
    return render_template("name.html", playlist_uri = playlist_uri)#, recommendations = 'NA')

@app.route("/login")
def login():
    # Generate a unique state value
    state = str(uuid.uuid4())
    # Store the state value in the session
    session["state"] = state
    return spotify.authorize(callback=url_for("authorized", _external=True), state=state)

@app.route("/logout")
def logout():
    session.pop("spotify_token", None)
    return redirect(url_for("home"))


@app.route("/authorized")
def authorized():
    print("Authorizing...")
    resp = spotify.authorized_response()
    if resp is None:
        # Redirect to login page if authorization failed
        return redirect(url_for("login"))
    # Verify the state value to ensure it's not a forgery attack
    if session.get("state") != request.args.get("state"):
        return "Invalid state parameter", 401
    # Remove the state value from the session
    session.pop("state", None)
    print("access_token: ", resp["access_token"])
    session["spotify_token"] = (resp["access_token"], "")
    # return redirect(url_for("home"))

    try:
        os.remove('.cache')
    except OSError as e:
        pass

    scope = ["user-library-read",'user-top-read']
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=os.environ.get('CLIENT_ID'), \
        client_secret=os.environ.get('CLIENT_SECRET'), redirect_uri='http://localhost:5555/authorized'))
    results = sp.current_user_playlists(limit=50)
    playlists=[]
    for item in results['items']:
        playlists.append({'name':item['name'],'uri':item['uri']})
    return render_template("index.html",data=playlists)


@spotify.tokengetter
def get_spotify_oauth_token():
    return session.get("spotify_token")

if __name__ == "__main__":
    app.run(host="localhost", port=5555, debug=os.environ.get('DEBUG'))
