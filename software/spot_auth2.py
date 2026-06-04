from spotipy.oauth2 import SpotifyOAuth
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse
import json

# Your Spotify app credentials
CLIENT_ID = '8fc500f7e0854d93ba651782de551259'
CLIENT_SECRET = '44365a61a7a446a2a68144b5f262f646'
REDIRECT_URI = 'http://127.0.0.1:8888/callback'  # Must match dashboard
SCOPE = 'user-library-read playlist-read-private user-read-playback-state user-modify-playback-state playlist-read-private'

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles Spotify OAuth redirect requests."""
    code = None

    def do_GET(self):
        parsed = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(parsed.query)
        if "code" in params:
            OAuthCallbackHandler.code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Success!</h1><p>You can close this window now.</p></body></html>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing code parameter.")

def wait_for_auth_code(port=8888):
    """Start temporary local server and wait for Spotify callback with code."""
    server = HTTPServer(("localhost", port), OAuthCallbackHandler)
    while OAuthCallbackHandler.code is None:
        server.handle_request()
    return OAuthCallbackHandler.code

def main():
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=None,  # Use ".cache" if you want persistence
        show_dialog=True
    )

    # Step 1: Get auth URL
    auth_url = sp_oauth.get_authorize_url()
    print("?? Go to the following URL in your browser:\n")
    print(auth_url)

    # Step 2: Start local server and wait for redirect
    print("\n? Waiting for authentication redirect...")
    code = wait_for_auth_code(port=8888)

    # Step 3: Exchange code for token
    token_info = sp_oauth.get_access_token(code, as_dict=True)

    print("\n? Access token obtained!")
    print("Access Token:", token_info['access_token'])
    print("Refresh Token:", token_info['refresh_token'])
    print("Expires At:", token_info['expires_at'])

    # Save token info for reuse
    with open("token_info.json", "w") as f:
        json.dump(token_info, f, indent=2)
        print("?? Token saved to token_info.json")

if __name__ == "__main__":
    main()
