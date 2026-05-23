import urllib.request
import json
import os

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "phase3_synthesis", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()

DOC_ID = os.environ.get("GOOGLE_DOC_ID")
BASE_URL = os.environ.get("RAILWAY_API_BASE")
RECIPIENT_EMAIL = os.environ.get("DRAFT_EMAIL_TO")
INPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "phase3_synthesis", "output", "pulse_note.md")

def post_json(endpoint, payload):
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTPError on {url}: {e.code} - {e.read().decode('utf-8')}")
        raise

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found at {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    print("Appending to Google Doc...")
    append_res = post_json("/append_to_doc", {
        "doc_id": DOC_ID,
        "content": markdown_content
    })
    print("Append Response:", append_res)

    print("Creating email draft...")
    doc_link = f"https://docs.google.com/document/d/{DOC_ID}/edit"
    email_body = f"Hello,\n\nThe latest Weekly Pulse Note has been appended to the Google Doc:\n{doc_link}\n\nBest regards,\nAutomated Pipeline"
    email_subject = "New Weekly Pulse Note Generated"
    
    draft_res = post_json("/create_email_draft", {
        "to": RECIPIENT_EMAIL,
        "subject": email_subject,
        "body": email_body
    })
    print("Draft Response:", draft_res)
    print("\nPhase 4 Integration Successful!")

if __name__ == "__main__":
    main()
