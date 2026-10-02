def upcoming_events(events, today):
    return [event for event in events if event["date"] >= today]
