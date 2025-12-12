import time
import uuid
from threading import Thread
from supabase import create_client, Client
from config import *
from datetime import datetime, timezone


class NetworkManager:
    def __init__(self, player):
        self.player = player
        self.PLAYER_ID = str(uuid.uuid4())
        self.PLAYER_NAME = f"Player_{self.PLAYER_ID[:8]}"
        self.other_players = {}
        self.remote_cannonballs = {}  # Track remote cannonballs by ID
        self.running = True
        # Connection state tracking
        self.connected = False
        self.last_connection_attempt = 0
        self.connection_retry_interval = 2.0  # Start with 2 second retry interval
        self.max_retry_interval = 30.0  # Maximum retry interval of 30 seconds
        self.consecutive_failures = 0

        self.supabase = None
        self._attempt_connection()
        Thread(target=self._network_loop, daemon=True).start()
        Thread(target=self._cannonball_loop, daemon=True).start()
        print("Network threads started")
        self.seen_uuids = []  # this counts what chats have already been loaded

    def _attempt_connection(self):
        """Attempt to establish connection to Supabase"""
        try:
            current_time = time.time()
            # Only attempt reconnection if enough time has passed since last attempt
            if current_time - self.last_connection_attempt >= self.connection_retry_interval:
                self.last_connection_attempt = current_time

                if not self.supabase:
                    self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

                # Test connection with a simple query
                self.supabase.table("players").select("count", count="exact").execute()

                self.connected = True
                self.consecutive_failures = 0
                self.connection_retry_interval = 2.0  # Reset retry interval on success
                print("✓ Connected to Supabase")
                return True

        except Exception as e:
            self.connected = False
            self.consecutive_failures += 1
            # Exponential backoff for retry interval
            self.connection_retry_interval = min(
                self.max_retry_interval,
                2.0 * (1.5 ** min(self.consecutive_failures, 8))
            )
            print(f"✗ Connection attempt failed: {e}")
            print(f"Will retry in {self.connection_retry_interval:.1f} seconds")

        return False

    def new_chat(self, item_data: dict):
        try:
            new_uuid = str(uuid.uuid4())
            item_data["id"] = new_uuid
            response = self.supabase.from_("chat").insert(item_data).execute()
            if response.data:
                print(f"Successfully added item with ID: {new_uuid}")
                return response.data
            else:
                print(f"Error adding item: {response.error}")
                return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def get_chats(self):
        try:
            response = self.supabase.table("chat").select("*").execute()
            indx = 0
            if response.data:
                for row in response.data:
                    uuid = row["id"]
                    msg = row["msg"]
                    if uuid not in self.seen_uuids:  # if it hasn't been loaded yet than
                        self.seen_uuids.append(uuid)
                        indx += 1
                        print(f"{msg}")
                print(f"Successfully retrieved chats: {indx}")
            elif response.error:
                print(f"Error deleting rows: {response.error}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def delete_chat_history(self):
        try:
            response = self.supabase.table("chat").delete().neq("id",
                                                                "00000000-0000-0000-0000-000000000000").execute()  # delete rows where id is not equal to empty uuid format
            if response.data:
                print(f"Successfully deleted all rows from table '{'chat'}'.")
                print(f"Deleted data: {response.data}")
            elif response.error:
                print(f"Error deleting rows: {response.error}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def create_cannonball(self, cannonball_data):
        """Send a cannonball to Supabase"""
        try:
            if not self.connected or not self.supabase:
                return None

            # Add player_id to cannonball data
            cannonball_data["player_id"] = self.PLAYER_ID

            response = self.supabase.table("cannonballs").insert(cannonball_data).execute()
            if response.data:
                print(f"Cannonball created: {response.data[0]['id']}")
                return response.data[0]['id']
        except Exception as e:
            print(f"Error creating cannonball: {e}")
        return None

    def _cannonball_loop(self):
        """Background thread to fetch and update remote cannonballs"""
        last_fetch = 0.0

        while self.running:
            try:
                if not self.connected or not self.supabase:
                    time.sleep(0.1)
                    continue

                now = time.time()

                # Fetch new cannonballs every 100ms
                if now - last_fetch >= 0.1:
                    # Get cannonballs created in the last 1.5 seconds (buffer for network latency)
                    cutoff_dt = datetime.fromtimestamp(now - 1.5, tz=timezone.utc)
                    resp = self.supabase.table("cannonballs") \
                        .select("*") \
                        .gt("created_at", cutoff_dt.isoformat()) \
                        .neq("player_id", self.PLAYER_ID) \
                        .execute()

                    if hasattr(resp, 'data'):
                        new_cannonballs = {}
                        for cb_data in resp.data:
                            cb_id = cb_data.get("id")
                            if cb_id not in self.remote_cannonballs:
                                # Create new remote cannonball
                                from cannonball import CannonBall
                                try:
                                    # Calculate age of cannonball
                                    created_at = float(cb_data.get("created_at", now))
                                    age = now - created_at

                                    # Skip if too old
                                    if age > 5.0:  # Skip cannonballs older than lifetime
                                        continue

                                    cannonball = CannonBall.from_dict(cb_data)
                                    # Set initial age based on when it was created
                                    cannonball.age = age

                                    new_cannonballs[cb_id] = {
                                        "cannonball": cannonball,
                                        "created_at": created_at,
                                        "player_id": cb_data.get("player_id"),
                                        "received_at": now
                                    }
                                    print(
                                        f"New remote cannonball from {cb_data.get('player_id', 'unknown')} (age: {age:.2f}s)")
                                except Exception as e:
                                    print(f"Error creating remote cannonball: {e}")

                        # Update dictionary with new cannonballs
                        self.remote_cannonballs.update(new_cannonballs)

                    last_fetch = now

                # Cleanup old cannonballs
                cleanup_time = now - 6.0  # Slightly more than lifetime
                to_remove = []
                for cb_id, cb_info in self.remote_cannonballs.items():
                    if cb_info["created_at"] < cleanup_time:
                        to_remove.append(cb_id)

                for cb_id in to_remove:
                    del self.remote_cannonballs[cb_id]

                # Update existing cannonballs
                for cb_info in self.remote_cannonballs.values():
                    cb = cb_info["cannonball"]
                    if cb.age < cb.lifetime:
                        # Update age based on real time
                        cb.age = now - cb_info["created_at"]

                time.sleep(0.01)

            except Exception as e:
                print(f"Cannonball loop error: {e}")
                time.sleep(0.5)

    def get_remote_cannonballs(self):
        """Get list of remote cannonball objects"""
        return [info["cannonball"] for info in self.remote_cannonballs.values()]

    def _network_loop(self):
        last_send = 0.0
        last_fetch = 0.0
        while self.running:
            now = time.time()

            # If not connected, attempt reconnection
            if not self.connected:
                self._attempt_connection()
                time.sleep(0.1)  # Short sleep to prevent busy-waiting
                continue

            try:
                if now - last_send >= SEND_INTERVAL:
                    data = {
                        "player_id": self.PLAYER_ID,
                        "player_name": self.PLAYER_NAME,
                        "x": float(self.player.x),
                        "y": float(self.player.y),
                        "rotation": float(self.player.rotation),
                        "updated_at": float(now)
                    }
                    if self.supabase:
                        self.supabase.table("players").upsert(data, on_conflict="player_id").execute()
                        last_send = now

                if now - last_fetch >= FETCH_INTERVAL:
                    cutoff = now - 10.0
                    resp = self.supabase.table("players").select("*").gt("updated_at", cutoff).execute()
                    rows = getattr(resp, "data", None) or resp

                    for player_data in rows:
                        try:
                            pid = player_data.get("player_id")
                            if not pid or pid == self.PLAYER_ID:
                                continue

                            px = float(player_data.get("x", 0.0))
                            py = float(player_data.get("y", 0.0))
                            prot = float(player_data.get("rotation", 0.0))
                            ts = float(player_data.get("updated_at", time.time()))
                            pname = player_data.get("player_name", "Unknown")

                            dx = px - self.player.x
                            dy = py - self.player.y
                            dist = (dx * dx + dy * dy) ** 0.5

                            if dist <= VISIBLE_RADIUS:
                                if pid not in self.other_players:
                                    self.other_players[pid] = {
                                        "name": pname,
                                        "state": {"x": px, "y": py, "rot": prot, "vx": 0.0, "vy": 0.0, "vrot": 0.0},
                                        "target": {"x": px, "y": py, "rot": prot, "vx": 0.0, "vy": 0.0, "vrot": 0.0},
                                        "history": []
                                    }

                                hist = self.other_players[pid]["history"]
                                hist.append({"x": px, "y": py, "rot": prot, "ts": ts})
                                hist.sort(key=lambda s: s["ts"])
                                if len(hist) > MAX_HISTORY:
                                    hist[:] = hist[-MAX_HISTORY:]
                        except Exception:
                            continue
                    last_fetch = now

                # if we reached here without exception, mark connection healthy
                self.connected = True

                time.sleep(0.01)
            except Exception as e:
                # mark as disconnected and back off
                print("Network error:", e)
                self.connected = False
                # exponential-ish backoff up to a limit
                time.sleep(0.5)

    def stop(self):
        self.running = False
        if self.supabase:
            try:
                self.supabase.table("players").delete().eq("player_id", self.PLAYER_ID).execute()
                # Also delete any cannonballs from this player
                self.supabase.table("cannonballs").delete().eq("player_id", self.PLAYER_ID).execute()
            except Exception:
                pass

