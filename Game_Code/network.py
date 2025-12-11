import time
import uuid
from threading import Thread
from supabase import create_client, Client
from config import *


class NetworkManager:
    def __init__(self, player):
        self.player = player
        self.PLAYER_ID = str(uuid.uuid4())
        self.PLAYER_NAME = f"Player_{self.PLAYER_ID[:8]}"
        self.other_players = {}
        self.remote_cannonballs = {}  # Track remote cannonballs by ID
        self.running = True
        self.connected = False
        self.last_connection_attempt = 0
        self.connection_retry_interval = 2.0
        self.max_retry_interval = 30.0
        self.consecutive_failures = 0

        self.supabase = None
        self._attempt_connection()
        Thread(target=self._network_loop, daemon=True).start()
        Thread(target=self._cannonball_loop, daemon=True).start()
        print(f"🎮 NetworkManager initialized")
        print(f"   Player ID: {self.PLAYER_ID}")
        print(f"   Player Name: {self.PLAYER_NAME}")
        self.seen_uuids = []

    def _attempt_connection(self):
        """Attempt to establish connection to Supabase"""
        try:
            current_time = time.time()
            if current_time - self.last_connection_attempt >= self.connection_retry_interval:
                self.last_connection_attempt = current_time

                if not self.supabase:
                    print(f"🔗 Connecting to Supabase...")
                    self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

                # Test connection
                test = self.supabase.table("players").select("count", count="exact").limit(1).execute()

                self.connected = True
                self.consecutive_failures = 0
                self.connection_retry_interval = 2.0
                print("✅ Connected to Supabase")
                return True

        except Exception as e:
            self.connected = False
            self.consecutive_failures += 1
            self.connection_retry_interval = min(
                self.max_retry_interval,
                2.0 * (1.5 ** min(self.consecutive_failures, 8))
            )
            print(f"❌ Connection failed: {e}")
            print(f"   Will retry in {self.connection_retry_interval:.1f}s")

        return False

    # Chat methods (unchanged)
    def new_chat(self, item_data: dict):
        try:
            new_uuid = str(uuid.uuid4())
            item_data["id"] = new_uuid
            response = self.supabase.from_("chat").insert(item_data).execute()
            if response.data:
                print(f"✅ Chat added: {new_uuid}")
                return response.data
            else:
                print(f"Chat error: {response.error}")
                return None
        except Exception as e:
            print(f"Chat exception: {e}")
            return None

    def get_chats(self):
        try:
            response = self.supabase.table("chat").select("*").execute()
            indx = 0
            if response.data:
                for row in response.data:
                    uuid = row["id"]
                    msg = row["msg"]
                    if uuid not in self.seen_uuids:
                        self.seen_uuids.append(uuid)
                        indx += 1
                        print(f"{msg}")
                print(f"✅ Retrieved {indx} chats")
            elif response.error:
                print(f"❌ Chat error: {response.error}")
        except Exception as e:
            print(f"❌ Chat exception: {e}")

    def delete_chat_history(self):
        try:
            response = self.supabase.table("chat").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            if response.data:
                print(f"✅ Deleted all chats")
            elif response.error:
                print(f"❌ Delete error: {response.error}")
        except Exception as e:
            print(f"❌ Delete exception: {e}")

    def create_cannonball(self, cannonball_data):
        """Send a cannonball to Supabase"""
        try:
            if not self.connected or not self.supabase:
                print("❌ Cannot create cannonball: Not connected")
                return None

            # Add player_id to cannonball data
            cannonball_data["player_id"] = self.PLAYER_ID

            print(f"🎯 Creating cannonball:")
            print(f"   From player: {self.PLAYER_ID[:8]}")
            print(f"   Position: ({cannonball_data['x']:.2f}, {cannonball_data['y']:.2f})")
            print(f"   Side: {cannonball_data['side']}")

            # Send to Supabase
            response = self.supabase.table("cannonballs").insert(cannonball_data).execute()

            if hasattr(response, 'data') and response.data:
                server_id = response.data[0]['id']
                print(f"✅ Cannonball saved with ID: {server_id[:8]}")
                return server_id
            else:
                print(f"❌ Failed to save cannonball")
                if hasattr(response, 'error'):
                    print(f"   Error: {response.error}")
                return None

        except Exception as e:
            print(f"💥 Cannonball creation error: {e}")
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

                # Fetch new cannonballs every 250ms
                if now - last_fetch >= 0.25:
                    try:
                        # Get cannonballs created in the last 5.5 seconds
                        cutoff = now - 5.5

                        # Convert to ISO format
                        from datetime import datetime, timezone
                        cutoff_iso = datetime.fromtimestamp(cutoff, tz=timezone.utc).isoformat()

                        # Fetch cannonballs from other players
                        resp = self.supabase.table("cannonballs") \
                            .select("*") \
                            .gte("created_at", cutoff_iso) \
                            .neq("player_id", self.PLAYER_ID) \
                            .execute()

                        if hasattr(resp, 'data') and resp.data:
                            new_count = 0
                            current_ids = set(self.remote_cannonballs.keys())
                            fetched_ids = set()

                            for cb_data in resp.data:
                                cb_id = cb_data.get("id")
                                if not cb_id:
                                    continue

                                fetched_ids.add(cb_id)

                                if cb_id not in self.remote_cannonballs:
                                    # Create new remote cannonball
                                    from cannonball import CannonBall
                                    try:
                                        cannonball = CannonBall.from_dict(cb_data)
                                        self.remote_cannonballs[cb_id] = {
                                            "cannonball": cannonball,
                                            "player_id": cb_data.get("player_id"),
                                            "fetched_at": now
                                        }
                                        new_count += 1

                                        if new_count <= 3:  # Limit debug output
                                            player_id = cb_data.get("player_id", "unknown")[:8]
                                            print(f"🎯 New remote cannonball from {player_id}")
                                            print(f"   Position: ({cannonball.x:.2f}, {cannonball.y:.2f})")

                                    except Exception as e:
                                        print(f"❌ Error creating remote cannonball: {e}")
                                        continue

                            if new_count > 0:
                                print(f"✅ Added {new_count} new remote cannonballs")

                            # Remove cannonballs that are no longer in the database
                            expired_ids = current_ids - fetched_ids
                            for cb_id in expired_ids:
                                if cb_id in self.remote_cannonballs:
                                    del self.remote_cannonballs[cb_id]

                        else:
                            # No new cannonballs
                            pass

                    except Exception as e:
                        print(f"❌ Fetch error: {e}")

                    last_fetch = now

                # Cleanup very old cannonballs (7+ seconds)
                cleanup_time = now - 7.0
                to_remove = []
                for cb_id, cb_info in self.remote_cannonballs.items():
                    if cb_info["fetched_at"] < cleanup_time:
                        to_remove.append(cb_id)

                if to_remove:
                    for cb_id in to_remove:
                        del self.remote_cannonballs[cb_id]
                    if len(to_remove) > 0:
                        print(f"🗑️  Cleaned up {len(to_remove)} expired cannonballs")

                time.sleep(0.01)

            except Exception as e:
                print(f"💥 Cannonball loop error: {e}")
                time.sleep(1.0)

    def get_remote_cannonballs(self):
        """Get list of remote cannonball objects"""
        return [info["cannonball"] for info in self.remote_cannonballs.values()]

    def _network_loop(self):
        last_send = 0.0
        last_fetch = 0.0

        while self.running:
            now = time.time()

            # Reconnect if needed
            if not self.connected:
                self._attempt_connection()
                time.sleep(0.1)
                continue

            try:
                # Send player update
                if now - last_send >= SEND_INTERVAL:
                    data = {
                        "player_id": self.PLAYER_ID,
                        "player_name": self.PLAYER_NAME,
                        "x": float(self.player.x),
                        "y": float(self.player.y),
                        "rotation": float(self.player.rotation),
                        "updated_at": now
                    }
                    if self.supabase:
                        self.supabase.table("players").upsert(data, on_conflict="player_id").execute()
                        last_send = now

                # Fetch other players
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

                self.connected = True
                time.sleep(0.01)

            except Exception as e:
                print(f"❌ Network error: {e}")
                self.connected = False
                time.sleep(0.5)

    def stop(self):
        self.running = False
        if self.supabase:
            try:
                self.supabase.table("players").delete().eq("player_id", self.PLAYER_ID).execute()
                self.supabase.table("cannonballs").delete().eq("player_id", self.PLAYER_ID).execute()
                print("✅ Cleaned up player data")
            except Exception as e:
                print(f"❌ Cleanup error: {e}")


