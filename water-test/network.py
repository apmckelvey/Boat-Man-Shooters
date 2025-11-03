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
        self.running = True

        self.supabase = None
        try:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("✓ Connected to Supabase")
            Thread(target=self._network_loop, daemon=True).start()
            print("Network thread started")
        except Exception as e:
            print("✗ Supabase disabled:", e)

    def _network_loop(self):
        if not self.supabase:
            return
        last_send = 0.0
        last_fetch = 0.0

        while self.running:
            try:
                now = time.time()

                if now - last_send >= SEND_INTERVAL:
                    data = {
                        "player_id": self.PLAYER_ID,
                        "player_name": self.PLAYER_NAME,
                        "x": float(self.player.x),
                        "y": float(self.player.y),
                        "rotation": float(self.player.rotation),
                        "updated_at": float(now)
                    }
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

                            dx = px - self.player.x
                            dy = py - self.player.y
                            dist = (dx * dx + dy * dy) ** 0.5

                            if dist <= VISIBLE_RADIUS:
                                if pid not in self.other_players:
                                    self.other_players[pid] = {
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

                time.sleep(0.01)
            except Exception as e:
                print("Network error:", e)
                time.sleep(0.5)

    def stop(self):
        self.running = False
        if self.supabase:
            try:
                self.supabase.table("players").delete().eq("player_id", self.PLAYER_ID).execute()
            except Exception:
                pass