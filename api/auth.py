import secrets
import hashlib
import base64
from os import environ
import urllib.parse
import webbrowser
import requests
from datetime import datetime, timedelta
from database import DatabaseManager

class Authenticator:
    '''
    Handles authentication with the Spotify API.
    Create an instance and call `request_tokens` to get
    and access and refresh tokens.
    --- 
    # Variables
    ## Static
    - `BASE_URL`: The base url where all auth related endpoints are
    - `AUTH_URL`: The url to send the authentication request to.
    - `TOKEN_URL`: The url to request the access and refresh tokens.
    - `REDIRECT_URI`: The url to redirect to after the authentication is complete.
    - `SCOPES`: The permissions required.
    ## Members
    - `client_secret`: The uuid of the Spotify app.
    - `code_verifier`: The code used to verify the PKCE challenge.
    - `auth_code`: The code used to request the access and refresh tokens.
    - `access_token`: The access token used to authenticate against the Spotify API
    - `refresh_token`: The token used to refresh the access token. 
    '''
    BASE_URL: str = "https://accounts.spotify.com/"
    AUTH_URL: str = BASE_URL + "authorize/?"
    TOKEN_URL: str = BASE_URL + "api/token"

    REDIRECT_URI: str = "http://localhost:8888/callback"
    SCOPES: str = "user-read-playback-state playlist-read-private user-read-currently-playing"
    
    client_secret: str
    code_verifier: str
    auth_code: str | None
    access_token: str | None
    expiry_time: datetime | None
    refresh_token: str | None

    def __init__(self, refresh_token: str | None = None) -> None:
        """
        If `refresh_token` is passed the Authenticator will try to get an access token without the need of having to login.
        Otherwise, `request_auth_code` and `request_access_token` must be called in that order.
        """
        client_secret = environ.get("client_secret")

        if not client_secret:
            raise KeyError("No client id set. Create a .env file with the 'client_secret' key. This must be your Spotify app's client secret.")

        self.client_secret = client_secret
        self.code_verifier = Authenticator._generate_random_string(64)
        self.refresh_token = refresh_token

        if self.refresh_token:
            self.refresh_tokens()

    def request_access_token(self, redirected_url: str):
        """
        Prompts for user login and stores the access and refresh tokens in the Authenticator
        ---
        # Params
        - `redirected_url`: Since Spotify provides the user authorization code through a redirect uri parameter it needs 
        to be manually input in the program. Here it is parsed and extracted from the url.
        """
        
        query = urllib.parse.urlsplit(redirected_url).query
        params = urllib.parse.parse_qs(query)

        error = params.get("error")
        if error:
            raise PermissionError(f"Login failed: {error}")
        
        auth_code = params.get("code")[0] if params else None

        if not auth_code:
            raise KeyError("No authentication code found in the url")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        body = {
            "client_id": self.client_secret,
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": Authenticator.REDIRECT_URI,
            "code_verifier": self.code_verifier

        }

        res_dict = dict(requests.post(Authenticator.TOKEN_URL, headers=headers, params=body).json())
        
        error = res_dict.get("error")
        error_desc = res_dict.get("error_description")

        if error:
            raise PermissionError(f"Unable to retrieve access token: {error} ({error_desc})")

        access_token = res_dict.get("access_token")
        refresh_token = res_dict.get("refresh_token")
        
        expires_in = int(res_dict.get("expires_in"))
        expiry_time = datetime.now() + timedelta(seconds=expires_in)

        if access_token and refresh_token:
            self.access_token = access_token
            self.expiry_time = expiry_time
            self.refresh_token = refresh_token

            with DatabaseManager() as db:
                db.set_refresh_token(refresh_token)

    def request_auth_code(self):
        """
        Requests the auth code necessary to get the access and refresh tokens. 
        This must be called before `request_access_token` to get the redirect uri.
        """
        hashed = Authenticator._sha256(self.code_verifier)
        code_challenge = Authenticator._base64_urlencode(hashed)

        # todo: add state parameter
        params = {
            "client_id": self.client_secret,
            "response_type": "code",
            "redirect_uri": Authenticator.REDIRECT_URI,
            "scope": Authenticator.SCOPES,
            "code_challenge_method": "S256",
            "code_challenge": code_challenge
        }
        
        url = Authenticator.AUTH_URL + urllib.parse.urlencode(params)
        webbrowser.open(url)

    def refresh_tokens(self):
        """
        Call this function when the access token has been invalidated
        and a new one is required.
        """
        params  = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_secret
        }

        headers = {
            'Content-Type': "application/x-www-form-urlencoded"
        }

        res = dict(requests.post(Authenticator.TOKEN_URL, params=params, headers=headers).json())

        error = res.get("error")
        error_desc = res.get("error_description")

        if error:
            raise PermissionError(f"Unable to refresh access token: {error} ({error_desc})")

        access_token = res.get("access_token")
        refresh_token = res.get("refresh_token")

        if access_token and refresh_token:
            self.refresh_token = refresh_token
            self.access_token = access_token
         
            with DatabaseManager() as db:
                db.set_refresh_token(refresh_token)

    def is_token_valid(self) -> bool:
        """
        Returns true if the current access token is still valid
        """
        if self.access_token and self.expiry_time:
            return self.expiry_time - datetime.now() < timedelta(seconds=10)
        return False

    def _generate_random_string(length: int):
        possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        return ''.join(secrets.choice(possible) for _ in range(length))

    def _sha256(input: str):
        return hashlib.sha256(input.encode("ascii")).digest()
    
    def _base64_urlencode(input: str):
        return base64.urlsafe_b64encode(input).decode("ascii").replace("=", '').replace("/+", '-').replace("/", '_')

import unittest

class AuthenticatorTests(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        from dotenv import load_dotenv

        load_dotenv()        

        super().__init__(methodName)

    def test_valid_request_auth_token(self):
        auth = Authenticator()

        auth.request_auth_code()
        auth_url = input("Input the redirect url: ")

        (access_token, refresh_token) = auth.request_access_token(auth_url)

        self.assertIsNotNone(access_token, "Access Token doesn't exist")
        self.assertIsNotNone(refresh_token, "Refresh token doesn't exist")

    def test_request_token_cancel(self):
        auth = Authenticator()

        with self.assertRaises(PermissionError):
            auth.request_access_token("localhost:8888/callback?error=InvalidCredentials")


if __name__ == "__main__":
    unittest.main()
