#!/usr/bin/python
"""Script to fetch email from outlook."""
import win32com.client
import pythoncom
import datetime
LAST_RUN_FILE = "last_run.txt"


def extract(count):
    """Get emails from outlook."""
    items = []

    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        print("Outlook COM object available")
    except pythoncom.com_error as e:
        print("COM error:", e)

    # outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    print("Accounts available in Outlook:")
    for store in namespace.Stores:
        print(" -", store.DisplayName)

    # outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = namespace.GetDefaultFolder(6) 
     # "6" refers to the inbox
    messages = inbox.Items
    message = messages.GetFirst()
    i = 0
    while message:
        try:
            msg = dict()
            msg["Subject"] = getattr(message, "Subject", "<UNKNOWN>")
            msg["SentOn"] = getattr(message, "SentOn", "<UNKNOWN>")
            msg["EntryID"] = getattr(message, "EntryID", "<UNKNOWN>")
            msg["Sender"] = getattr(message, "Sender", "<UNKNOWN>")
            msg["Size"] = getattr(message, "Size", "<UNKNOWN>")
            msg["Body"] = getattr(message, "Body", "<UNKNOWN>")
            items.append(msg)
        except Exception as ex:
            print("Error processing mail", ex)
        i += 1
        if i < count:
            message = messages.GetNext()
        else:
            return items

    return items
def get_inbox(account_name):
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")

    for store in namespace.Stores:
        if store.DisplayName == account_name:
            inbox = store.GetDefaultFolder(6)  # 6 = Inbox
            return inbox
    raise Exception(f"Account '{account_name}' not found")

def extract_data(account_name, n=5):
    inbox = get_inbox(account_name)
    # outlook = win32com.client.Dispatch("Outlook.Application")
    # namespace = outlook.GetNamespace("MAPI")

    # # 6 = Inbox
    # inbox = namespace.GetDefaultFolder(6)
    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)  # newest first

    count = min(n, messages.Count)  # avoid out of range

    # for i, msg in enumerate(messages[:n]):
    for i in range(count):
        msg = messages.Item(i+1)
        try:
            print(f"\n--- Mail {i+1} ---")
            print(f"From: {msg.SenderName}")
            print(f"Subject: {msg.Subject}")
            print(f"Received: {msg.ReceivedTime}")
            print(f"Body: {msg.Body[:200]}...")  # print first 200 chars
        except Exception as e:
            print(f"Error reading message {i+1}: {e}")
def get_new_since_last_run():
    # Load last run time
    try:
        with open(LAST_RUN_FILE, "r") as f:
            last_run = datetime.datetime.fromisoformat(f.read().strip())
    except FileNotFoundError:
        last_run = datetime.datetime.now() - datetime.timedelta(days=1)

    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    inbox = namespace.Folders.Item("vaibhavsinghal2000@outlook.com").Folders["Inbox"]

    # Restrict by ReceivedTime
    restriction = f"[ReceivedTime] >= '{last_run.strftime('%m/%d/%Y %H:%M:%S')}'"
    messages = inbox.Items.Restrict(restriction)
    messages.Sort("[ReceivedTime]", True)

    for msg in messages:
        print(f"New Mail -> {msg.Subject} from {msg.SenderName} at {msg.ReceivedTime}")

    # Update last run time
    with open(LAST_RUN_FILE, "w") as f:
        f.write(datetime.datetime.now().isoformat())


def show_message(items):
    """Show the messages."""
    items.sort(key=lambda tup: tup["SentOn"])
    for i in items:
        print(i["SentOn"], i["Subject"])


def main():
    """Fetch and display top message."""
    items = extract(5)
    show_message(items)


if __name__ == "__main__":
    # extract_data(5)
    # main()
    # extract_data("vaibhavsinghal1@outlook.com", 5)
    get_new_since_last_run()