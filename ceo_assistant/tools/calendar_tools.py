from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES       = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID  = os.environ.get("GOOGLE_CALENDAR_ID", "primary")


def _get_calendar_service():
    """Build a Calendar API service using OAuth2 refresh token."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ.get("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    )
    return build("calendar", "v3", credentials=creds)


def list_upcoming_events(max_results: int = 10) -> str:
    """List the next N upcoming calendar events.

    Args:
        max_results: Maximum number of events to return (default 10).

    Returns:
        A formatted string listing upcoming events.
    """
    try:
        svc = _get_calendar_service()
        now = datetime.now(timezone.utc).isoformat()
        result = (
            svc.events()
            .list(
                calendarId=CALENDAR_ID,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = result.get("items", [])
        if not events:
            return "No upcoming events found."
        lines = []
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date", "?"))
            attendees = ", ".join(
                a.get("email", "") for a in e.get("attendees", [])
            ) or "No attendees"
            lines.append(f"- [{start}] {e.get('summary', 'No title')} | {attendees}")
        return "\n".join(lines)
    except Exception as ex:
        return f"Failed to list events: {ex}"


def find_free_slots(
    date: str,
    duration_minutes: int = 60,
    working_hours_start: int = 9,
    working_hours_end: int = 18,
) -> str:
    """Find free time slots on a given date.

    Args:
        date: Date in YYYY-MM-DD format.
        duration_minutes: Required slot duration in minutes (default 60).
        working_hours_start: Start of working day in 24h (default 9).
        working_hours_end: End of working day in 24h (default 18).

    Returns:
        List of available time slots.
    """
    try:
        svc = _get_calendar_service()
        day_start = f"{date}T{working_hours_start:02d}:00:00Z"
        day_end   = f"{date}T{working_hours_end:02d}:00:00Z"
        body = {"timeMin": day_start, "timeMax": day_end, "items": [{"id": CALENDAR_ID}]}
        freebusy = svc.freebusy().query(body=body).execute()
        busy     = freebusy["calendars"][CALENDAR_ID]["busy"]

        slots  = []
        cursor = datetime.fromisoformat(day_start.replace("Z", "+00:00"))
        end_of_day = datetime.fromisoformat(day_end.replace("Z", "+00:00"))
        delta  = timedelta(minutes=duration_minutes)

        for b in busy:
            bs = datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
            be = datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
            while cursor + delta <= bs:
                slots.append(f"{cursor.strftime('%H:%M')} – {(cursor + delta).strftime('%H:%M')}")
                cursor += delta
            cursor = max(cursor, be)

        while cursor + delta <= end_of_day:
            slots.append(f"{cursor.strftime('%H:%M')} – {(cursor + delta).strftime('%H:%M')}")
            cursor += delta

        if not slots:
            return f"No free {duration_minutes}-min slots on {date}."
        return f"Free {duration_minutes}-min slots on {date}:\n" + "\n".join(f"- {s}" for s in slots)
    except Exception as ex:
        return f"Failed to check availability: {ex}"


def create_event(
    title: str,
    start_datetime: str,
    end_datetime: str,
    attendee_emails: Optional[str] = None,
    description: Optional[str] = None,
) -> str:
    """Create a new calendar event.

    Args:
        title: Event title/summary.
        start_datetime: ISO 8601 start (e.g. '2026-04-05T14:00:00Z').
        end_datetime: ISO 8601 end datetime.
        attendee_emails: Comma-separated attendee emails (optional).
        description: Event description or agenda (optional).

    Returns:
        Confirmation with event link, or error message.
    """
    try:
        svc = _get_calendar_service()
        attendees = (
            [{"email": e.strip()} for e in attendee_emails.split(",")]
            if attendee_emails else []
        )
        body = {
            "summary":     title,
            "description": description or "",
            "start":       {"dateTime": start_datetime},
            "end":         {"dateTime": end_datetime},
            "attendees":   attendees,
            "reminders":   {"useDefault": True},
        }
        event = svc.events().insert(calendarId=CALENDAR_ID, body=body).execute()
        return f"Event created: {event.get('htmlLink', 'no link')} (ID: {event['id']})"
    except Exception as ex:
        return f"Failed to create event: {ex}"


def delete_event(event_id: str) -> str:
    """Delete a calendar event by its ID.

    Args:
        event_id: The Google Calendar event ID.

    Returns:
        Confirmation or error message.
    """
    try:
        svc = _get_calendar_service()
        svc.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
        return f"Event {event_id} deleted successfully."
    except Exception as ex:
        return f"Failed to delete event: {ex}"
