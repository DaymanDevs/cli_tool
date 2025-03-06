import pandas as pd
from data_loader import load_and_combine_csv
from table_display import display_table, search_tables_by_contract
from wallet_utils import format_wallet_table, update_criteria
from wallet_config import load_wallets, save_wallets, duplicate_wallet_config
from config import DATA_DIRECTORY
from ui_utils import menu_selection
import platform
import os
import threading
import colorama
from colorama import Fore, Style

colorama.init()

def load_data_in_background(combined_tables):
    combined_tables[0] = load_and_combine_csv(DATA_DIRECTORY)

def manage_wallets(combined_tables):
    wallets = load_wallets()
    while True:
        wallet_table = format_wallet_table(wallets)
        if wallet_table is None:
            options = ["Create New Wallet", "Back"]
            table_str = "No wallets configured."
        else:
            options = ["Create New Wallet", "Edit Wallet", "Duplicate Wallet", "Delete Wallet", "Back"]
            table_str = wallet_table
        
        choice = menu_selection(options, table_str)
        if choice == "Back" or choice is None:
            break
        
        if choice == "Create New Wallet":
            new_name = menu_selection(options, table_str, prompt="Enter new wallet name (or blank to cancel): ")
            if new_name is None or not new_name.strip():
                continue
            if new_name in wallets:
                menu_selection(options, table_str, info_message="Name already exists. Press any key to continue...")
                input()
                continue
            from wallet_config import DEFAULT_CRITERIA
            new_criteria = DEFAULT_CRITERIA.copy()
            if update_criteria(new_criteria, new_name, wallets.keys()):
                wallets[new_name] = new_criteria
                save_wallets(wallets)
        
        elif choice == "Edit Wallet":
            wallet_options = list(wallets.keys()) + ["Back"]
            edit_choice = menu_selection(wallet_options, table_str)
            if edit_choice == "Back" or edit_choice is None:
                continue
            result = update_criteria(wallets[edit_choice], edit_choice, wallets.keys())
            if result is True:  # Save in place
                save_wallets(wallets)
            elif result:  # Save As with new name
                wallet_name = result
                wallets = load_wallets()  # Reload to get new wallet
                update_criteria(wallets[wallet_name], wallet_name, wallets.keys())
        
        elif choice == "Duplicate Wallet":
            wallet_options = list(wallets.keys()) + ["Back"]
            dup_choice = menu_selection(wallet_options, table_str)
            if dup_choice == "Back" or dup_choice is None:
                continue
            new_name = menu_selection(wallet_options, table_str, prompt="Enter new wallet name (or blank to cancel): ")
            if new_name is None or not new_name.strip():
                continue
            if new_name in wallets:
                menu_selection(wallet_options, table_str, info_message="Name already exists. Press any key to continue...")
                input()
                continue
            duplicate_wallet_config(dup_choice, new_name)
            wallets = load_wallets()
        
        elif choice == "Delete Wallet":
            wallet_options = list(wallets.keys()) + ["Back"]
            del_choice = menu_selection(wallet_options, table_str)
            if del_choice == "Back" or del_choice is None:
                continue
            confirm = menu_selection(["Yes", "No"], f"Are you sure you want to delete '{del_choice}'?")
            if confirm == "Yes":
                del wallets[del_choice]
                save_wallets(wallets)

def main():
    if platform.system() == "Windows":
        os.system('cls')
    
    main_menu = ["Feeds", "Wallets", "Search by contract", "Exit"]
    feed_options = [
        "PF", "Fomo", "BB", "GM", "MF", "SM",
        "PF Top", "Fomo Top", "BB Top", "GM Top", "MF Top", "SM Top",
        "Back"
    ]
    
    # Background loading
    combined_tables = [None]  # List to share between threads
    loading_thread = threading.Thread(target=load_data_in_background, args=(combined_tables,))
    loading_thread.daemon = True  # Exit thread when main program exits
    loading_thread.start()
    
    while True:
        choice = menu_selection(main_menu, "=== MAIN MENU ===")
        if choice == "Exit" or choice is None:
            break
        
        if choice == "Feeds":
            if combined_tables[0] is None:
                print("Loading data, please wait...")
                loading_thread.join()  # Wait for loading to finish
            feed_choice = menu_selection(feed_options, "=== FEEDS ===")
            if feed_choice == "Back" or feed_choice is None:
                continue
            internal_key = feed_choice.lower().replace(" top", "")
            display_table(internal_key, combined_tables[0], feed_choice)
        
        elif choice == "Wallets":
            if combined_tables[0] is None:
                print("Loading data, please wait...")
                loading_thread.join()
            manage_wallets(combined_tables[0])
        
        elif choice == "Search by contract":
            if combined_tables[0] is None:
                print("Loading data, please wait...")
                loading_thread.join()
            search_tables_by_contract(combined_tables[0])
        
        if platform.system() == "Windows":
            os.system('cls')

if __name__ == "__main__":
    main()