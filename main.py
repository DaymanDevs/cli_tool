import pandas as pd
import os
import sys
import platform
from datetime import datetime
from data_loader import load_and_combine_csv
from table_display import display_table, search_tables_by_contract
from config import DATA_DIRECTORY
from ui_utils import menu_selection
from wallet_utils import format_wallet_table, update_criteria
from wallet_config import load_wallets, create_wallet_config, duplicate_wallet_config, DEFAULT_CRITERIA, save_wallets

if platform.system() == "Windows":
    import msvcrt
else:
    import curses

def manage_wallets(combined_tables):
    wallets = load_wallets()
    wallet_names = list(wallets.keys())
    
    while True:
        options = ["Create Wallet", "Edit Wallet", "Delete Wallet", "Duplicate Wallet", "Back"]
        wallet_table = format_wallet_table(wallets)
        choice = menu_selection(options, wallet_table if wallet_table else "No wallets available.")
        if choice == "Back" or choice is None:
            break
        
        if choice == "Create Wallet":
            name = menu_selection(options, wallet_table, prompt="Enter wallet name (or blank to cancel): ")
            if name is None or not name.strip():
                continue
            if name in wallets:
                print("Name already exists. Press Enter to continue...")
                input()
                continue
            criteria = DEFAULT_CRITERIA.copy()
            if update_criteria(criteria, name, wallet_names + [name]) is False:
                continue
            create_wallet_config(name, criteria)
            print(f"'{name}' created. Press Enter to continue...")
            input()
        
        elif choice == "Edit Wallet" and wallet_names:
            wallet_choice = menu_selection([f"{i+1}: {name}" for i, name in enumerate(wallet_names)] + ["Back"], wallet_table)
            if wallet_choice == "Back" or wallet_choice is None:
                continue
            selected_num = int(wallet_choice.split(':')[0]) - 1
            wallet_name = wallet_names[selected_num]
            criteria = wallets[wallet_name].copy()
            if update_criteria(criteria, wallet_name, wallet_names) is False:
                continue
            create_wallet_config(wallet_name, criteria)
            print(f"'{wallet_name}' updated. Press Enter to continue...")
            input()
        
        elif choice == "Delete Wallet" and wallet_names:
            wallet_choice = menu_selection([f"{i+1}: {name}" for i, name in enumerate(wallet_names)] + ["Back"], wallet_table)
            if wallet_choice == "Back" or wallet_choice is None:
                continue
            selected_num = int(wallet_choice.split(':')[0]) - 1
            wallet_name = wallet_names[selected_num]
            confirm = menu_selection(["Yes", "No"], wallet_table, prompt=f"Delete '{wallet_name}'? (Yes/No): ")
            if confirm == "Yes":
                del wallets[wallet_name]
                save_wallets(wallets)
                wallet_names.remove(wallet_name)
                print(f"'{wallet_name}' deleted. Press Enter to continue...")
                input()
        
        elif choice == "Duplicate Wallet" and wallet_names:
            wallet_choice = menu_selection([f"{i+1}: {name}" for i, name in enumerate(wallet_names)] + ["Back"], wallet_table)
            if wallet_choice == "Back" or wallet_choice is None:
                continue
            selected_num = int(wallet_choice.split(':')[0]) - 1
            original_name = wallet_names[selected_num]
            new_name = menu_selection(options, wallet_table, prompt=f"Enter new name for duplicate of '{original_name}' (or blank to cancel): ")
            if new_name is None or not name.strip():
                continue
            if new_name in wallets:
                print("Name already exists. Press Enter to continue...")
                input()
                continue
            duplicate_wallet_config(original_name, new_name)
            print(f"'{new_name}' created as duplicate of '{original_name}'. Press Enter to continue...")
            input()
    
    if platform.system() == "Windows":
        os.system('cls')

def main():
    combined_tables = load_and_combine_csv(DATA_DIRECTORY)
    if not combined_tables:
        print("No data loaded. Press any key to exit...")
        if platform.system() == "Windows":
            msvcrt.getch()
        else:
            curses.wrapper(lambda stdscr: stdscr.getch())
        return
    
    table_options = ["PF", "Fomo", "Fomo Top", "BB", "BB Top", "GM", "GM Top", "MF", "MF Top", "SM", "SM Top", "Back"]
    main_options = ["Tables", "Wallets", "Search by contract", "Exit"]
    
    while True:
        choice = menu_selection(main_options)
        if choice == "Exit" or choice is None:
            print("Goodbye.")
            break
        
        if choice == "Tables":
            while True:
                table_choice = menu_selection(table_options)
                if table_choice == "Back" or table_choice is None:
                    break
                internal_key = table_choice.lower().replace(" top", "")
                display_table(internal_key, combined_tables, table_choice)
        
        elif choice == "Wallets":
            manage_wallets(combined_tables)
        
        elif choice == "Search by contract":
            search_tables_by_contract(combined_tables)

if __name__ == "__main__":
    main()