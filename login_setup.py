from playwright.sync_api import sync_playwright
import os
from pathlib import Path

def save_login():
    """
    Securely save Steam login session.
    
    Session is stored in user's home directory with restricted permissions.
    """
    # Store session in user home directory for security
    session_dir = Path.home() / ".pricetracker"
    session_dir.mkdir(exist_ok=True, mode=0o700)  # Only owner can read/write/execute
    session_path = session_dir / "steam_session.json"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            page.goto("https://steamcommunity.com/login")
            print("Steam'e login ol. Bitince Enter'a bas.")
            input()

            # Save session state securely
            context.storage_state(path=str(session_path))
            
            # Restrict file permissions to owner only (0o600 = rw-------)
            os.chmod(session_path, 0o600)
            
            print(f"✓ Session kaydedildi: {session_path}")
            browser.close()
            
    except Exception as e:
        print(f"✗ Hata oluştu: {e}")
        raise

if __name__ == "__main__":
    save_login()
