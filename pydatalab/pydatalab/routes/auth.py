from typing import Dict, Callable

from requests_oauthlib import OAuth2Session
from flask import session, redirect, request

from pydatalab.config import CONFIG


def login():
    redirect_uri = CONFIG["HOST"] + "/callback"
    github = OAuth2Session(CONFIG["GITHUB_OAUTH_CLIENT_ID"], redirect_uri=redirect_uri)
    auth_url, state = github.authorization_url(CONFIG["GITHUB_OAUTH_BASE_URL"])
    session["oauth_state"] = state
    return redirect(auth_url)


def oauth_callback():
    github = OAuth2Session(CONFIG["GITHUB_OAUTH_CLIENT_ID"], state=session["oauth_state"])
    token = github.fetch_token(
        CONFIG["GITHUB_OAUTH_TOKEN_URL"],
        client_secret=CONFIG["GITHUB_OAUTH_CLIENT_SECRET"],
        authorization_response=request.url,
    )
    session["oauth_token"] = token

    return jsonify(github.get("https://api.github.com/user").json())


ENDPOINTS: Dict[str, Callable] = {
    "/login/": login,
    "/oauth-callback/": oauth_callback,
}
