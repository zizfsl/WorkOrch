from googleapiclient.discovery import build
import datetime

try:
    from auth import get_credentials
except ModuleNotFoundError:
    from workorch.auth import get_credentials

def get_upcoming_events(max_results: int = 10) -> str:
    """
    Fetch the user's upcoming events from Google Calendar.
    Returns a formatted string of the next few events.
    """
    creds = get_credentials()
    if not creds:
        return "You must log in with Google first. Please tell me to 'log in with google'."

    # Build the service
    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    
    try:
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=max_results, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return "No upcoming events found in your Google Calendar."

        output = ["📅 Your upcoming events:"]
        for event in events:
            # Parse datetime nicely if possible, or just print it
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            # Format datetime
            if "T" in start:
                dt = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
                # Simplified formatting: e.g. 'Apr 03 at 08:30 PM'
                formatted_start = dt.strftime("%b %d at %I:%M %p")
            else:
                formatted_start = start
                
            summary = event.get('summary', 'Busy (No title)')
            output.append(f"- {formatted_start}: {summary}")
            
        return "\n".join(output)
    except Exception as e:
        return f"Failed to fetch calendar events: {str(e)}"

def get_unread_emails(max_results: int = 5) -> str:
    """
    Fetch the subjects of the user's most recent unread emails in Gmail.
    Returns a formatted string of the unread emails.
    """
    creds = get_credentials()
    if not creds:
        return "You must log in with Google first. Please tell me to 'log in with google'."

    # Build the service
    service = build('gmail', 'v1', credentials=creds)

    try:
        results = service.users().messages().list(
            userId='me', q="is:unread -category:promotions -category:social", maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])

        if not messages:
            return "Inbox Zero! You have no unread emails right now."

        output = [f"📧 Your {len(messages)} most recent unread emails:"]
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'From']
            ).execute()
            
            headers = msg_data.get('payload', {}).get('headers', [])
            subject = "No Subject"
            sender = "Unknown Sender"
            
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                elif header['name'] == 'From':
                    sender = header['value']
                    # Clean up sender string (usually "Name <email>")
                    if '<' in sender:
                        sender = sender.split('<')[0].strip()
                    
            output.append(f"- From **{sender}**: {subject}")
            
        return "\n".join(output)
    except Exception as e:
        return f"Failed to fetch emails: {str(e)}"
