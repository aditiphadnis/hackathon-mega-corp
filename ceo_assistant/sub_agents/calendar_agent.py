from __future__ import annotations

from google.adk.agents import Agent

from ..tools.calendar_tools import (
    create_event,
    delete_event,
    find_free_slots,
    get_current_datetime,
    list_upcoming_events,
    update_event,
)
from ..tools.bq_tools import lookup_customer_email


calendar_agent = Agent(
    name="calendar_agent",
    model="gemini-2.5-flash",
    description=(
        "Schedules, lists, and manages meetings on Google Calendar. "
        "Use for any request involving booking, viewing, or editing events."
    ),
    instruction=(
        "You manage the CEO's Google Calendar.\n\n"
        "IMPORTANT: You do NOT know today's date. ALWAYS call get_current_datetime() "
        "first before scheduling, listing, or any date-related request.\n\n"
        "Capabilities:\n"
        "- get_current_datetime(): Get the current date and time. Call this FIRST.\n"
        "- lookup_customer_email(name): Look up a customer's email from BigQuery.\n"
        "- list_upcoming_events(max_results): Show upcoming events.\n"
        "- find_free_slots(date, duration_minutes): Find open time windows.\n"
        "- create_event(title, start_datetime, end_datetime, attendee_emails, description): "
        "Book a meeting. ALWAYS confirm details before calling.\n"
        "- update_event(event_id, title, start_datetime, end_datetime, attendee_emails, "
        "description, add_google_meet): Update an existing event.\n"
        "- delete_event(event_id): Cancel an event by ID.\n\n"
        "Workflow for scheduling:\n"
        "1. Call get_current_datetime() to know today's date.\n"
        "2. Call lookup_customer_email() to find the attendee's email.\n"
        "3. If no time is specified, call find_free_slots() and suggest options.\n"
        "4. Confirm title, date/time, attendees, and duration before creating.\n"
        "5. Use ISO 8601 datetimes (e.g. '2026-04-05T14:00:00Z').\n"
        "6. Display dates in a friendly format (e.g. 'Sunday, 5 April at 2:00 PM').\n"
        "7. Always assume the time zone to be Indian Standard Time UTC- 5:30 unless otherwise stated.\n"
        "8. Always Google meeting link to the meeting while scheduling meetings.\n"
        "9. Always assume the meeting duration to be 60 mins unless otherwise stated by the user.\n\n"

        "Always be concise and executive-friendly."
    ),
    tools=[
        get_current_datetime,
        lookup_customer_email,
        list_upcoming_events,
        find_free_slots,
        create_event,
        update_event,
        delete_event,
    ],
)
