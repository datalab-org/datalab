from typing import Dict, Callable
import functools

from requests_oauthlib import OAuth2Session
from flask import session, redirect, request, jsonify, url_for

from pydatalab.config import CONFIG
from pydatalab.logger import logged_route
from pydatalab.mongo import flask_mongo

DEFAULT_OAUTH = "github"


@logged_route
def login():
    redirect_uri = request.url.replace("login", "oauth-callback")
    provider = CONFIG.OAUTH_PROVIDERS[DEFAULT_OAUTH]
    if "oauth_provider" in request.args:
        provider = CONFIG.OAUTH_PROVIDERS.get(request.args["oauth_provider"], provider)

    oauth = OAuth2Session(provider.client_id, redirect_uri=redirect_uri)
    auth_url, state = oauth.authorization_url(provider.base_url)
    session["oauth_state"] = state
    session["oauth_provider"] = provider.name
    return redirect(auth_url)


@logged_route
def oauth_callback():
    provider = CONFIG.OAUTH_PROVIDERS[session["oauth_provider"]]
    oauth = OAuth2Session(provider.client_id, state=session["oauth_state"])

    token = oauth.fetch_token(
        provider.token_url,
        client_secret=provider.client_secret,
        authorization_response=request.url,
    )
    session["oauth_token"] = token
    session["authenticated"] = True

    if session["oauth_provider"] == "github":
        identity = {"github_username": oauth.get("https://api.github.com/user").json()["login"]}
    elif session["oauth_provider"] == "orcid_sandbox":
        identity = {"orcid": oauth.get("https://sandbox.orcid.org/user").json()["login"]}
        
    user = lookup_user(identity)

    return redirect(request.args.get("next", url_for("profile")))


def lookup_user(identity):
    return flask_mongo.db.users.find_one(identity)


@logged_route
def profile():
    provider = CONFIG.OAUTH_PROVIDERS[session["oauth_provider"]]
    oauth = OAuth2Session(provider.client_id, token=session["oauth_token"])
    return jsonify(oauth.get("https://api.github.com/user").json())


def requires_authentication(func):
    @functools.wraps(func)
    def f(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login", next=request.url))
        return func(*args, **kwargs)

    return f



ENDPOINTS: Dict[str, Callable] = {
    "/login/": login,
    "/oauth-callback/": oauth_callback,
    "/profile/": profile,
}