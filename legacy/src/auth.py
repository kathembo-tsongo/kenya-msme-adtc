"""
auth.py — Credentials Manager for Kenya MSME Advisor
Handles loading, saving, and updating user credentials from file.
"""

import json
import hashlib
from pathlib import Path

CREDS_FILE = Path(__file__).parent.parent / "config" / "credentials.json"


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def load_credentials() -> dict:
    """Load credentials from file."""
    if not CREDS_FILE.exists():
        # Create default credentials if file missing
        default = {
            "users": {
                "admin": {
                    "password": hash_password("msme2024admin"),
                    "role":     "admin",
                    "name":     "System Administrator",
                    "email":    "admin@msme-advisor.co.ke",
                    "hashed":   True
                },
                "researcher": {
                    "password": hash_password("msme2024research"),
                    "role":     "researcher",
                    "name":     "Researcher",
                    "email":    "researcher@msme-advisor.co.ke",
                    "hashed":   True
                }
            }
        }
        CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        CREDS_FILE.write_text(json.dumps(default, indent=4))
        return default
    return json.loads(CREDS_FILE.read_text())


def save_credentials(creds: dict):
    """Save credentials to file."""
    CREDS_FILE.write_text(json.dumps(creds, indent=4))


def verify_password(username: str, password: str) -> bool:
    """Verify username and password."""
    creds = load_credentials()
    user  = creds["users"].get(username)
    if not user:
        return False
    stored = user["password"]
    # Support both hashed and plain passwords (migrate on first use)
    if user.get("hashed"):
        return stored == hash_password(password)
    else:
        # Plain password — verify then migrate to hashed
        if stored == password:
            migrate_to_hashed(username, password)
            return True
        return False


def migrate_to_hashed(username: str, password: str):
    """Migrate plain password to hashed."""
    creds = load_credentials()
    if username in creds["users"]:
        creds["users"][username]["password"] = hash_password(password)
        creds["users"][username]["hashed"]   = True
        save_credentials(creds)


def get_user(username: str) -> dict:
    """Get user info by username."""
    creds = load_credentials()
    return creds["users"].get(username, {})


def update_password(username: str, new_password: str) -> bool:
    """Update a user's password."""
    creds = load_credentials()
    if username not in creds["users"]:
        return False
    creds["users"][username]["password"] = hash_password(new_password)
    creds["users"][username]["hashed"]   = True
    save_credentials(creds)
    return True


def update_username(old_username: str, new_username: str) -> bool:
    """Rename a user account."""
    creds = load_credentials()
    if old_username not in creds["users"]:
        return False
    if new_username in creds["users"]:
        return False  # Username already taken
    creds["users"][new_username] = creds["users"].pop(old_username)
    save_credentials(creds)
    return True


def update_profile(username: str, name: str, email: str) -> bool:
    """Update user display name and email."""
    creds = load_credentials()
    if username not in creds["users"]:
        return False
    creds["users"][username]["name"]  = name
    creds["users"][username]["email"] = email
    save_credentials(creds)
    return True


def list_users() -> list:
    """List all users (for admin view)."""
    creds = load_credentials()
    users = []
    for username, info in creds["users"].items():
        users.append({
            "username": username,
            "name":     info.get("name", ""),
            "role":     info.get("role", ""),
            "email":    info.get("email", ""),
        })
    return users
