# src/utils/pusher.py

import pusher
import os

# Initialize the client once from environment variables or directly
pusher_client = pusher.Pusher(
  app_id=os.environ.get("PUSHER_APP_ID", "2036351"),
  key=os.environ.get("PUSHER_KEY", "42232516b44bb251e68a"),
  secret=os.environ.get("PUSHER_SECRET", "ffc11c7f96c86b775d45"),
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