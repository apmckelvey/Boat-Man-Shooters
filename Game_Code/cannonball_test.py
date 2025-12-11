import time
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import json
import uuid


def fix_and_test_cannonballs():
    """Fix and test the cannonballs table"""

    print("=" * 60)
    print("FIXING CANNONBALLS TABLE")
    print("=" * 60)

    try:
        # Connect to Supabase
        print("1. Connecting to Supabase...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("   ✓ Connected")

        # Test with a UUID player_id (what the table expects)
        print("\n2. Testing with UUID player_id...")
        test_cannonball_uuid = {
            "player_id": str(uuid.uuid4()),  # Real UUID
            "x": 8.5,
            "y": 8.5,
            "rotation": 1.57,
            "velocity_x": 0.7,
            "velocity_y": 0.2,
            "side": "right"
        }

        print(f"   Test data (UUID): {json.dumps(test_cannonball_uuid, indent=4)}")

        try:
            response = supabase.table("cannonballs").insert(test_cannonball_uuid).execute()
            print(f"   ✓ Insert with UUID successful")
            print(f"   Response: {response}")
        except Exception as e:
            print(f"   ✗ Insert with UUID failed: {e}")

        # Test with our actual player ID format
        print("\n3. Testing with our player ID format...")
        test_cannonball_text = {
            "player_id": "abc123_test_player",  # Text, not UUID
            "x": 9.5,
            "y": 9.5,
            "rotation": 0.0,
            "velocity_x": 0.5,
            "velocity_y": -0.5,
            "side": "left"
        }

        print(f"   Test data (text): {json.dumps(test_cannonball_text, indent=4)}")

        try:
            response = supabase.table("cannonballs").insert(test_cannonball_text).execute()
            print(f"   ✓ Insert with text successful")
            print(f"   Response: {response}")
        except Exception as e:
            print(f"   ✗ Insert with text failed: {e}")

        # List what's in the table now
        print("\n4. Current table contents...")
        response = supabase.table("cannonballs").select("*").limit(10).execute()
        if response.data:
            print(f"   Found {len(response.data)} records:")
            for i, cb in enumerate(response.data):
                player_id = cb.get('player_id', 'N/A')
                is_uuid = len(player_id) == 36 and '-' in player_id
                print(f"   {i + 1}. Player ID: {player_id[:20]}... ({'UUID' if is_uuid else 'TEXT'})")
                print(f"      Position: ({cb.get('x', 0):.2f}, {cb.get('y', 0):.2f})")
        else:
            print("   No records found")

    except Exception as e:
        print(f"✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    fix_and_test_cannonballs()
