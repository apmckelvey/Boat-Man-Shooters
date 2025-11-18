import time
import uuid
from datetime import datetime
import pygame
from threading import Thread
from supabase import create_client, Client
from config import *


class NetworkManager:
    def __init__(self, player):
        self.player = player
        self.PLAYER_ID = str(uuid.uuid4())
        self.PLAYER_NAME = f"Player_{self.PLAYER_ID[:8]}"
        self.other_players = {}
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
        print("Network thread started")
        self.seen_uuids = [] #this counts what chats have already been loaded
    def new_chat(self, table_name: str, item_data: dict):
        try:
            new_uuid = str(uuid.uuid4())
            item_data["id"] = new_uuid
            response = self.supabase.from_(table_name).insert(item_data).execute()
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
        response = self.supabase.table("chat").select("*").execute()
        for row in response.data:
            uuid = row["id"]
            msg = row["msg"]
            if uuid not in self.seen_uuids: #if it hasn't been loaded yet than
                self.seen_uuids.append(uuid)
                print(f"{msg}")

    def delete_chat_history(self):
        try:
            response = self.supabase.table("chat").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()#delete rows where id is not equal to empty uuid format
            if response.data:
                print(f"Successfully deleted all rows from table '{'chat'}'.")
                print(f"Deleted data: {response.data}")
            elif response.error:
                print(f"Error deleting rows: {response.error}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
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
                consecutive_errors = 0
                self.connected = True

                time.sleep(0.01)
            except Exception as e:
                # mark as disconnected and back off
                print("Network error:", e)
                consecutive_errors += 1
                self.connected = False
                # exponential-ish backoff up to a limit
                time.sleep(min(0.5 * consecutive_errors, 5.0))

    def stop(self):
        self.running = False
        if self.supabase:
            try:
                self.supabase.table("players").delete().eq("player_id", self.PLAYER_ID).execute()
            except Exception:
                pass