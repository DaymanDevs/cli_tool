import pandas as pd
from data_loader import load_and_combine_csv
from table_display import display_table, search_tables_by_contract
from wallet_utils import format_wallet_table, update_criteria
from wallet_config import load_wallets, save_wallets, duplicate_wallet_config
from config import DATA_DIRECTORY
from ui_utils import menu_selection
import platform
import os
import colorama
from colorama import Fore, Style

colorama.init()

def manage_wallets(combined_tables):
    wallets = load_wallets()  # Load wallets each time to ensure freshness
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
            if update_criteria(wallets[edit_choice], edit_choice, wallets.keys()):
                save_wallets(wallets)
        
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
            wallets = load_wallets()  # Reload to reflect changes
        
        elif choice == "Delete Wallet":
            wallet_options = list(wallets.keys()) + ["Back"]
            del_choice = menu_selection(wallet_options, table_str)
            if del_choice == "Back" or del_choice is None:
                continue
            del wallets[del_choice]
            save_wallets(wallets)

def main():
    if platform.system() == "Windows":
        os.system('cls')
    
    combined_tables = load_and_combine_csv(DATA_DIRECTORY)
    
    main_menu = ["Feeds", "Wallets", "Search by contract", "Exit"]
    feed_options = [
        "PF", "Fomo", "BB", "GM", "MF", "SM",
        "PF Top", "Fomo Top", "BB Top", "GM Top", "MF Top", "SM Top",
        "Back"
    ]
    
    while True:
        choice = menu_selection(main_menu, "=== MAIN MENU ===")
        if choice == "Exit" or choice is None:
            break
        
        if choice == "Feeds":
            feed_choice = menu_selection(feed_options, "=== FEEDS ===")
            if feed_choice == "Back" or feed_choice is None:
                continue
            internal_key = feed_choice.lower().replace(" top", "")
            display_table(internal_key, combined_tables, feed_choice)
        
        elif choice == "Wallets":
            manage_wallets(combined_tables)
        
        elif choice == "Search by contract":
            search_tables_by_contract(combined_tables)
        
        if platform.system() == "Windows":
            os.system('cls')

if __name__ == "__main__":
    main()