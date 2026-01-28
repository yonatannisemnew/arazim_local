import base64
import mimetypes
import os
import sys
import json
from dotenv import load_dotenv
from email.message import EmailMessage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

TASKS_FOLDER = os.getenv('TASKS_FOLDER', 'tasks')

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

def get_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def gmail_create_draft_with_attachment(task_data):
  """Create and insert a draft email with attachment.
   Print the returned draft's message and id.
  Returns: Draft object, including draft id and message meta data.

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  creds = get_creds()
  attachment_filename = task_data["file_path"]

  try:
    # create gmail api client
    service = build("gmail", "v1", credentials=creds)
    mime_message = EmailMessage()

    # headers
    mime_message["To"] = "sacha.hallermeier@gmail.com"
    mime_message["Subject"] = "Arazim Print Job"

    # TODO: change to actually print meny copies
    mime_message.set_content(f"copies: {task_data['copies']}")

    # guessing the MIME type
    type_subtype, _ = mimetypes.guess_type(attachment_filename)
    maintype, subtype = type_subtype.split("/")

    with open(attachment_filename, "rb") as fp:
      attachment_data = fp.read()
    mime_message.add_attachment(attachment_data, maintype, subtype)

    encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

    # --- CHANGE 1: structure the body for 'send' (no "message" wrapper) ---
    create_message = {"raw": encoded_message}

    # --- CHANGE 2: call messages.send instead of drafts.create ---
    sent_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f'Draft id: {sent_message["id"]}\n')
    return sent_message
  except HttpError as error:
    print(f"An error occurred: {error}")
    return None


def build_file_part(file):
  """Creates a MIME part for a file.

  Args:
    file: The path to the file to be attached.

  Returns:
    A MIME part that can be attached to a message.
  """
  content_type, encoding = mimetypes.guess_type(file)

  if content_type is None or encoding is not None:
    content_type = "application/octet-stream"
  main_type, sub_type = content_type.split("/", 1)
  if main_type == "text":
    with open(file, "rb"):
      msg = MIMEText("r", _subtype=sub_type)
  elif main_type == "image":
    with open(file, "rb"):
      msg = MIMEImage("r", _subtype=sub_type)
  elif main_type == "audio":
    with open(file, "rb"):
      msg = MIMEAudio("r", _subtype=sub_type)
  else:
    with open(file, "rb"):
      msg = MIMEBase(main_type, sub_type)
      msg.set_payload(file.read())
  filename = os.path.basename(file)
  msg.add_header("Content-Disposition", "attachment", filename=filename)
  return msg

def extract_task_json(task_json_path):
    if not os.path.exists(task_json_path):
        print('Task not found.', file=sys.stderr)
        return None

    try:
        with open(task_json_path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        return data
    except Exception:
        print('Could not read task file.', file=sys.stderr)
        return None


if __name__ == "__main__":
  if (len(sys.argv) != 2):
    print("Usage: python printing_script.py <job_json_path>")
    sys.exit(1)
  task_data = extract_task_json(sys.argv[1])
  if task_data is None:
      sys.exit(1)
  # Send the email with the attachment
  gmail_create_draft_with_attachment(task_data)
  # Clean up old tasks after sending the email
  os.remove(sys.argv[1])