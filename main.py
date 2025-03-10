import pandas as pd
import sqlite3
from table_display import display_table, search_tables_by_contract
from wallet_utils import format_wallet_table, update_criteria
from wallet_config import load_wallets, save_wallets, duplicate_wallet_config
from config import DATA_DIRECTORY
from ui_utils import menu_selection, get_terminal_height
import platform
import os
import colorama
from colorama import Fore, Style

colorama.init()

def manage_wallets(conn):
    wallets = load_wallets()
    options = ["Create New Wallet", "Edit Wallet", "Duplicate Wallet", "Delete Wallet", "Back"] if wallets else ["Create New Wallet", "Back"]
    
    while True:
        wallet_table = format_wallet_table(wallets) if wallets else "No wallets configured."
        choice = menu_selection(options, wallet_table, prompt="=== WALLETS ===")
        if choice == "Back" or choice is None:
            break
        
        if choice == "Create New Wallet":
            new_name = menu_selection(options, wallet_table, prompt="Enter new wallet name (or blank to cancel): ", allow_input=True)
            if new_name and new_name not in wallets:
                from wallet_config import DEFAULT_CRITERIA
                new_criteria = DEFAULT_CRITERIA.copy()
                if update_criteria(new_criteria, new_name, wallets.keys()):
                    wallets[new_name] = new_criteria
                    save_wallets(wallets)
        
        elif choice == "Edit Wallet" and wallets:
            wallet_options = list(wallets.keys()) + ["Back"]
            edit_choice = menu_selection(wallet_options, wallet_table)
            if edit_choice != "Back" and edit_choice is not None:
                result = update_criteria(wallets[edit_choice], edit_choice, wallets.keys())
                if result is True:
                    save_wallets(wallets)
                elif result:
                    wallet_name = result
                    wallets = load_wallets()
                    update_criteria(wallets[wallet_name], wallet_name, wallets.keys())
        
        elif choice == "Duplicate Wallet" and wallets:
            wallet_options = list(wallets.keys()) + ["Back"]
            dup_choice = menu_selection(wallet_options, wallet_table)
            if dup_choice != "Back" and dup_choice is not None:
                new_name = menu_selection(wallet_options, wallet_table, prompt="Enter new wallet name (or blank to cancel): ", allow_input=True)
                if new_name and new_name not in wallets:
                    duplicate_wallet_config(dup_choice, new_name)
                    wallets = load_wallets()
        
        elif choice == "Delete Wallet" and wallets:
            wallet_options = list(wallets.keys()) + ["Back"]
            del_choice = menu_selection(wallet_options, wallet_table)
            if del_choice != "Back" and del_choice is not None:
                confirm = menu_selection(["Yes", "No"], wallet_table, prompt=f"Are you sure you want to delete '{del_choice}'?")
                if confirm == "Yes":
                    del wallets[del_choice]
                    save_wallets(wallets)

def main():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')
    
    db_path = os.path.join(DATA_DIRECTORY, 'data.db')
    if not os.path.exists(db_path):
        print("Error: Database not found. Run init_db.py first.")
        return
    conn = sqlite3.connect(db_path)
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'mcaps'")
    feed_tables = [row[0] for row in cursor.fetchall()]
    if not feed_tables:
        print("Error: No feed tables found in database. Run init_db.py with data.")
        conn.close()
        return
    
    regular_feeds = [t for t in feed_tables if not t.endswith('10')]
    top_feeds = [t for t in feed_tables if t.endswith('10')]
    
    main_menu = ["Feeds", "Wallets", "Search by contract", "Exit"]
    feed_options = [table.replace('_', ' ').title() for table in regular_feeds] + \
                   [table.replace('_', ' ').title().replace('10', ' Top') for table in top_feeds] + ["Back"]
    
    while True:
        choice = menu_selection(main_menu, "", prompt="=== MAIN MENU ===")
        if choice == "Exit" or choice is None:
            break
        
        if choice == "Feeds":
            feed_choice = menu_selection(feed_options, "", prompt="=== FEEDS ===")
            if feed_choice != "Back" and feed_choice is not None:
                internal_key = feed_choice.lower().replace(' ', '_').replace('top', '10')
                display_name = feed_choice
                display_table(internal_key, conn, display_name)
        
        elif choice == "Wallets":
            manage_wallets(conn)
        
        elif choice == "Search by contract":
            search_tables_by_contract(conn)
        
        if platform.system() == "Windows":
            os.system('cls')
        else:
            os.system('clear')
    
    conn.close()

if __name__ == "__main__":
    main()