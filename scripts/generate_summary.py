import os
import json
import random
import subprocess
import google.generativeai as genai


def get_git_changes():
    """Gets the last 3 commit messages."""
    try:
        # Get last 3 commits
        # Note: We fetch from the local repository copy checked out by the Action.
        return subprocess.check_output(
            ["git", "log", "-n", "3", "--pretty=format:%s"], text=True
        )
    except Exception:
        return "Unknown changes"


def generate_update():
    """Generates an AI summary or uses a fallback message."""
    api_key = os.environ.get("GEMINI_API_KEY")
    changes = get_git_changes()

    # --- PATH A: REAL AI (If you added the key) ---
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Use the faster, cost-effective model for summaries
            model = genai.GenerativeModel('gemini-1.5-flash')

            prompt = f"""
            You are the "Dev Log Bot" for a chaotic boat combat game called "Boat Man Shooters".
            Analyze the following changes and summarize them into ONE short, funny, exciting sentence (max 2 sentences) for players.
            Tone: Chaotic, pirate-like, enthusiastic.

            Commits:
            {changes}
            """

            response = model.generate_content(prompt)
            return response.text.strip()
        except:
            # Fallback if API fails (e.g., rate limit, network error)
            pass

            # --- PATH B: FAKE AI (Fallback if no key or API failed) ---
    print("No API key found or API failed. Using fallback message.")
    fallbacks = [
        "The Captain is too drunk to write a log, but code was definitely pushed.",
        "Cannons calibrated. Bugs squashed. The chaos continues.",
        "We changed some things. Hopefully the boat doesn't sink immediately.",
        "Updates deployed! If it breaks, blame the parrot.",
        f"Latest changes: {changes.splitlines()[0]}... and more secrets."
    ]
    return random.choice(fallbacks)


if __name__ == "__main__":
    summary = generate_update()

    # IMPORTANT: Save to the docs/data folder for GitHub Pages
    output_dir = os.path.join("docs", "data")
    os.makedirs(output_dir, exist_ok=True)

    # Save the summary into a JSON file
    with open(os.path.join(output_dir, "ai_summary.json"), "w") as f:
        json.dump({"summary": summary}, f, indent=2)

    print(f"Summary saved to {output_dir}/ai_summary.json")