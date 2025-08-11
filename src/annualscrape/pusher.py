# src/annualscrape/pusher.py

import pusher
import os

# Initialize the client once from environment variables or directly
pusher_client = pusher.Pusher(
  app_id=os.environ.get("PUSHER_APP_ID", "2034338"),
  key=os.environ.get("PUSHER_KEY", "751b3a6004a16ab6fa2d"),
  secret=os.environ.get("PUSHER_SECRET", "87a117c07a4abf3a2098"),
  cluster=os.environ.get("PUSHER_CLUSTER", "ap1"),
  ssl=True
)

def send_pusher_notification(channel: str, event: str, data: dict):
    """
    Helper function to send a Pusher notification.
    """
    try:
        pusher_client.trigger(channel, event, data)
        print(f"✅ Pusher notification sent to channel '{channel}' with event '{event}': {data}")
    except Exception as e:
        print(f"❌ Error sending Pusher notification: {e}")