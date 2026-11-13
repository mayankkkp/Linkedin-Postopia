import os
import webbrowser
import urllib.parse
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI")
SCOPES = "openid profile w_member_social"

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        code = params.get("code", [None])[0]
        
        if code:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authentication successful! You can close this window.")
            
            # Exchange code for token
            token_url = "https://www.linkedin.com/oauth/v2/accessToken"
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            }
            response = requests.post(token_url, data=data)
            token_data = response.json()
            
            if "access_token" in token_data:
                print(f"\n✅ ACCESS TOKEN: {token_data['access_token']}")
                print("\nSave this token in your .env file as LINKEDIN_ACCESS_TOKEN")
                # We also need the person URN
                headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                userinfo = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers).json()
                print(f"✅ PERSON URN: urn:li:person:{userinfo['sub']}")
                print("Save this in .env as LINKEDIN_PERSON_URN")
            else:
                print("Error getting token:", token_data)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authentication failed.")
        
        # Stop server after handling
        raise SystemExit

def main():
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(SCOPES)}"
    )
    print(f"Opening browser for authentication...")
    print(f"If it doesn't open, go to: {auth_url}")
    webbrowser.open(auth_url)
    
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    print("Waiting for callback on http://localhost:8080...")
    server.serve_forever()

if __name__ == "__main__":
    main()