from __future__ import annotations

from google.adk.agents import Agent

from ..tools.calendar_tools import (
    create_event,
    delete_event,
    find_free_slots,
    list_upcoming_events,
)

calendar_agent = Agent(
    name="calendar_agent",
    model="gemini-2.5-flash",
    description=(
        "Schedules, lists, and manages meetings on Google Calendar. "
        "Use for any request involving booking, viewing, or editing events."
    ),
    instruction=(
        "You manage the CEO's Google Calendar via the Google Calendar API.\n\n"
        "Capabilities:\n"
        "- list_upcoming_events(max_results): Show upcoming events with date, time, attendees.\n"
        "- find_free_slots(date, duration_minutes): Find open time windows on a given day.\n"
        "- create_event(title, start_datetime, end_datetime, attendee_emails, description): "
        "Book a meeting. ALWAYS confirm details with the user before calling this.\n"
        "- delete_event(event_id): Cancel an event by ID.\n\n"
        "Workflow for scheduling:\n"
        "1. If no time is specified, call find_free_slots() first and suggest options.\n"
        "2. Confirm title, date/time, attendees, and duration before creating.\n"
        "3. Use ISO 8601 datetimes internally (e.g. '2026-04-05T14:00:00+05:30').\n"
        "4. Display dates in a friendly format (e.g. 'Sunday, 5 April at 2:00 PM').\n\n"
        "Always be concise and executive-friendly in your responses."
    ),
    tools=[list_upcoming_events, find_free_slots, create_event, delete_event],
)