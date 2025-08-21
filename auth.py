import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
TOKEN_FILE = "token.pickle"

def get_authenticated_service():
    creds = None

    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # If no valid token, go through login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("Looking for:", CLIENT_SECRETS_FILE)
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES  # ✅ FIXED HERE
            )
            creds = flow.run_local_server(port=0)

        # Save token for later use
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return creds

# Trigger the flow
if __name__ == "__main__":
    get_authenticated_service()
    print("✅ Authentication successful.")
