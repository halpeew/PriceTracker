from playwright.sync_api import sync_playwright
import os
import json
from pathlib import Path

def save_login():
    session_path = Path.home() / ".steam_session" / "steam_session.json"
    session_path.parent.mkdir(exist_ok=True, mode=0o700)  # Sadece kullanıcı okuyabilitir
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            page.goto("https://steamcommunity.com/login")
            print("Steam'e login ol. Bitince Enter'a bas.")
            input()

            # Dosya izinlerini 0o600 olarak ayarla (sadece sahibi okuyabilir)
            context.storage_state(path=str(session_path))
            os.chmod(session_path, 0o600)
            
            print(f"Session kaydedildi: {session_path}")
            browser.close()
    except Exception as e:
        print(f"Hata oluştu: {e}")
        raise

if __name__ == "__main__":
    save_login()
