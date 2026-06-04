from spotipy.oauth2 import SpotifyOAuth

# Your Spotify app credentials
CLIENT_ID = '8fc500f7e0854d93ba651782de551259'
CLIENT_SECRET = '44365a61a7a446a2a68144b5f262f646'
REDIRECT_URI = 'http://127.0.0.1:8888/callback'  # Should match what's in your Spotify dev dashboard
SCOPE = 'user-library-read playlist-read-private user-read-playback-state user-modify-playback-state playlist-read-private'  # Add more scopes if needed

def main():
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=None,  # Don't use a cache for this test, or use '.cache' to save it
        show_dialog=True
    )

    # Step 1: Get the auth URL and print it
    auth_url = sp_oauth.get_authorize_url()
    print("??  Go to the following URL in your browser:\n")
    print(auth_url)

    while True:
	    # Step 2: Get the code from user
        code = input("\n?? Paste the URL you were redirected to, or just the code parameter: ").strip()
        if code != "":
            break

    # Support both full URL and just the code
    if "code=" in code:
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(code)
        code = urlparse.parse_qs(parsed.query).get("code", [None])[0]

    if not code:
        print("? No code found. Exiting.")
        return

    # Step 3: Exchange code for tokens
    token_info = sp_oauth.get_access_token(code, as_dict=True)

    print("\n? Access token obtained!")
    print("Access Token:", token_info['access_token'])
    print("Refresh Token:", token_info['refresh_token'])
    print("Expires At:", token_info['expires_at'])

    # (Optional) Save token_info to a file for future use
    with open("token_info.json", "w") as f:
        import json
        json.dump(token_info, f)
        print("?? Token saved to token_info.json")

if __name__ == "__main__":
    main()
