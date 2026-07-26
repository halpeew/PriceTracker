import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from playwright.sync_api import sync_playwright
import requests
import os 
from dotenv import load_dotenv

load_dotenv()
STEAM_ID = os.getenv("STEAM_ID")
BYNO_API_URL = os.getenv("BYNO_API_URL")


# ---------------- INVENTORY ----------------
def fetch_inventory():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="steam_session.json")
        page = context.new_page()

        inventory_data = {}

        def handle_response(response):
            if "/inventory/" in response.url and "730/2" in response.url:
                try:
                    data = response.json()
                    if data.get("success"):
                        nonlocal inventory_data
                        inventory_data = data
                except:
                    pass

        page.on("response", handle_response)
        page.goto(f"https://steamcommunity.com/profiles/{STEAM_ID}/inventory/#730_2")
        page.wait_for_timeout(8000)
        browser.close()

    if not inventory_data:
        return []

    assets = inventory_data["assets"]
    descriptions = inventory_data["descriptions"]

    desc_map = {}
    for d in descriptions:
        desc_map[(d["classid"], d["instanceid"])] = d

    items = []
    for a in assets:
        d = desc_map.get((a["classid"], a["instanceid"]))
        if not d:
            continue

        items.append({
            "name": d["market_hash_name"],
            "tradable": d.get("tradable", 0)
        })

    return items


# ---------------- STEAM PRICE ----------------
def get_market_price(name):
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        "appid": 730,
        "currency": 1,
        "market_hash_name": name
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data.get("success"):
            return float(data["lowest_price"].replace("$", ""))
    except:
        pass

    return 0.0


# ---------------- BYNOGAME PRICE (GLOBAL FETCH) ----------------
def fetch_bynogame_prices():
    try:
        r = requests.get(BYNO_API_URL, timeout=20)
        data = r.json()

        price_map = {}

        listings = data.get("data", [])

        for item in listings:
            name = item.get("name", "").strip().lower()
            price = item.get("price")

            if not name or price is None:
                continue

            price = float(price)

            # aynı itemden birden fazla varsa en düşüğü al
            if name not in price_map:
                price_map[name] = price
            else:
                price_map[name] = min(price_map[name], price)

        print(f"[BYNO] Toplam çekilen item: {len(price_map)}")

        return price_map

    except Exception as e:
        print("BYNO ERROR:", e)
        return {}


# ---------------- UI ----------------
class App:

    def __init__(self, root):
        self.root = root
        self.root.title("CS2 Trade & Profit Tracker PRO")
        self.root.geometry("1450x750")
        self.root.configure(bg="#1e1e1e")

        self.price_cache = {}
        self.byno_prices = {}
        self.items_data = []

        # TOP PANEL
        top_frame = tk.Frame(root, bg="#1e1e1e")
        top_frame.pack(fill="x")

        self.total_value_label = tk.Label(
            top_frame,
            text="Total Value: $0.00",
            fg="#00ff88",
            bg="#1e1e1e",
            font=("Segoe UI", 14, "bold")
        )
        self.total_value_label.pack(side="right", padx=20, pady=10)

        # TABLE
        self.tree = ttk.Treeview(
            root,
            columns=("name", "price", "net", "byno", "tradable"),
            show="headings",
            selectmode="extended"
        )

        self.tree.heading("name", text="Item")
        self.tree.heading("price", text="Market Price")
        self.tree.heading("net", text="After Fee")
        self.tree.heading("byno", text="3rd Party Lowest")
        self.tree.heading("tradable", text="Tradable")

        self.tree.column("name", width=450)
        self.tree.column("price", width=120)
        self.tree.column("net", width=120)
        self.tree.column("byno", width=150)
        self.tree.column("tradable", width=100)

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # BUTTONS
        bottom = tk.Frame(root, bg="#1e1e1e")
        bottom.pack(fill="x")

        ttk.Button(bottom, text="Refresh", command=self.refresh).pack(side="left", padx=10, pady=10)
        ttk.Button(bottom, text="3. Parti Alım Analizi", command=self.third_party_analysis).pack(side="right", padx=10, pady=10)

        self.refresh()

    # ---------------- REFRESH ----------------
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.items_data.clear()

        items = fetch_inventory()

        # 🔥 Bynogame fiyatlarını 1 kere çekiyoruz
        self.byno_prices = fetch_bynogame_prices()

        total_value = 0

        for item in items:
            name = item["name"]
            normalized_name = name.strip().lower()

            # Steam price
            if name in self.price_cache:
                price = self.price_cache[name]
            else:
                price = get_market_price(name)
                self.price_cache[name] = price

            net = round(price * 0.85, 2)
            total_value += net

            # Bynogame price
            byno_price = self.byno_prices.get(normalized_name, "-")

            row_id = self.tree.insert("", "end", values=(
                name,
                f"${price}",
                f"${net}",
                f"${byno_price}" if byno_price != "-" else "-",
                "Yes" if item["tradable"] else "No"
            ))

            self.items_data.append({
                "row": row_id,
                "name": name,
                "net": net
            })

        self.total_value_label.config(text=f"Total Value: ${round(total_value,2)}")

    # ---------------- THIRD PARTY ANALYSIS ----------------
    def third_party_analysis(self):

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "En az bir item seçmelisin.")
            return

        try:
            buy_price = float(simpledialog.askstring("Alım Fiyatı", "Alım fiyatınız kaçtı? (adet başı)"))
        except:
            return

        total_current = 0
        count = 0

        for row in selected:
            for item in self.items_data:
                if item["row"] == row:
                    total_current += item["net"]
                    count += 1

        total_buy = buy_price * count
        profit = total_current - total_buy
        percent = (profit / total_buy * 100) if total_buy != 0 else 0

        result_text = (
            f"Seçilen Adet: {count}\n"
            f"Toplam Alım: ${round(total_buy,2)}\n"
            f"Net Steam Satış: ${round(total_current,2)}\n\n"
            f"Kâr/Zarar: ${round(profit,2)}\n"
            f"ROI: %{round(percent,2)}"
        )

        if profit > 0:
            messagebox.showinfo("KÂR", result_text)
        else:
            messagebox.showerror("ZARAR", result_text)


root = tk.Tk()
app = App(root)
root.mainloop()
