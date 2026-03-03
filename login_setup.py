from playwright.sync_api import sync_playwright

def save_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://steamcommunity.com/login")
        print("Steam'e login ol. Bitince Enter'a bas.")
        input()

        context.storage_state(path="steam_session.json")
        browser.close()

save_login()