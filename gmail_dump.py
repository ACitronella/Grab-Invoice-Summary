import os.path
import json
import base64
from tqdm import tqdm

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

TOKEN_FILE = "credentials/token.json"
CREDENTIALS_FILE = "credentials/credentials.json"
OUTPUT_FILE = "data/messages.json"

def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8000)
        # Save the credentials for the next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        message_api = service.users().messages()
        search_results = message_api.list(
            userId="me", maxResults=500, q='from:no-reply@grab.com subject:"Your Grab E-Receipt"'
        ).execute()
        messages = search_results.get("messages", [])
        print(f"Found {len(messages)} messages")

        message_processed_list = []
        for m in tqdm(messages, desc="Downloading emails"):
            try:
                message_id = m.get("id", None)
                if message_id is None:
                    print("message_id is None")
                    continue
                message_obj = message_api.get(userId="me", id=message_id).execute()
                
                parts = message_obj["payload"].get("parts", [])
                message_obj_jsonify = {
                    "date": message_obj["internalDate"],
                    "payload": [base64.urlsafe_b64decode(p["body"]["data"].encode()).decode() for p in parts if p["body"]["size"] > 0]
                }
                message_processed_list.append(message_obj_jsonify)
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                message_processed_list.append({})
                

        with open(OUTPUT_FILE, "w") as f:
            json.dump(message_processed_list, f)

    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
