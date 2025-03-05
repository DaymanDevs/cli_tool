from table_format import format_table_columns
from table_utils import filter_table, generate_wallet_summary, search_contracts_in_pf
from ui_utils import menu_selection, print_filters, get_terminal_height
from wallet_config import load_wallets, apply_wallet_config
from config import DATA_DIRECTORY
import pandas as pd
import platform
from datetime import datetime
import os
if platform.system() == "Windows":
    import msvcrt
else:
    import curses
import colorama
from colorama import Fore, Style

colorama.init()

def display_table(table_name, combined_tables, display_name, search_results=None):
    if table_name not in combined_tables and search_results is None:
        print(f"Table '{table_name}' not found.")
        return
    
    if search_results is not None and not search_results.empty:
        df = search_results.copy()
    else:
        is_top_table = "top" in display_name.lower()
        base_name = table_name.lower().replace(" top", "")
        df = combined_tables[base_name].copy()
        df = df.rename(columns={"Funding Time": "FundTime", "Funding Source": "FundSource", "Dev Bal": "DevBal", "Has Links": "Links"})
        
        if is_top_table:
            top_key = f"{base_name}10"
            top_df = combined_tables.get(top_key, pd.DataFrame())
            if not top_df.empty:
                df = df.drop(columns=['MaxMcap', 'X\'s'], errors='ignore')
                df = df.merge(top_df[['Contract', 'MaxMcap', 'X\'s']], on='Contract', how='left')
    
    if 'Date' in df.columns and 'Time' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Date'] = df.apply(lambda row: f"{row['Date'].strftime('%d/%m/%y %H:%M')}" if pd.notna(row['Date']) and pd.notna(row['Time']) else 
                              f"{row['Date'].strftime('%d/%m/%y')}" if pd.notna(row['Date']) else pd.NA, axis=1)
        df = df.drop(columns=['Time'])
    if 'Funding' in df.columns:
        df = df.drop(columns=['FundTime', 'FundSource'], errors='ignore')
    
    if '#' not in df.columns:
        df.insert(0, "#", range(1, len(df) + 1))
    original_df = df.copy()
    filters = {}
    applied_configs = {}
    
    if platform.system() == "Windows":
        os.system('cls')
    
    while True:
        options = ["Return to menu", "Search in PF", "Filter Table", "Clear Filters", "Export to CSV", "Wallet Configs", "Back"]
        middle_content = generate_wallet_summary(df, applied_configs.keys())
        if not middle_content:
            middle_content = ""
        table_str_full = f"{print_filters(filters)}\nRow Count: {len(df)}\n=== Data for {display_name.upper()} ===\n" + \
                        format_table_columns(df, applied_configs)
        if applied_configs:
            middle_content = f"'{', '.join(applied_configs.keys())}' applied\n" + middle_content
        
        terminal_height = get_terminal_height()
        header_lines = len(f"{print_filters(filters)}\nRow Count: {len(df)}\n=== Data for {display_name.upper()} ===\n".split('\n'))
        middle_lines = len(middle_content.split('\n')) if middle_content else 0
        max_table_lines = terminal_height - header_lines - middle_lines - len(options) - 5
        table_lines = table_str_full.split('\n')
        table_str = '\n'.join(table_lines[:max(0, min(max_table_lines, len(table_lines)))])
        
        choice = menu_selection(options, table_str, middle_content)
        if choice is None:
            break
        
        if choice == "Search in PF":
            selected = menu_selection(options, table_str, prompt="Enter selection numbers (comma-separated, or 'all'): ", middle_content=middle_content)
            if selected is None:
                continue
            if selected.lower() == "all":
                contracts = df["Contract"].tolist()
                search_contracts_in_pf(contracts, combined_tables, df)
            else:
                selected_nums = [int(i.strip()) for i in selected.split(',') if i.strip().isdigit()]
                if selected_nums and all(num in df["#"].values for num in selected_nums):
                    filtered_df = df.loc[df["#"].isin(selected_nums)]
                    contracts = filtered_df["Contract"].tolist()
                    search_contracts_in_pf(contracts, combined_tables, filtered_df)
                else:
                    menu_selection(options, table_str, info_message="Invalid selection. Press any key to continue...", middle_content=middle_content)
                    input()
            if platform.system() == "Windows":
                os.system('cls')
        
        elif choice == "Filter Table":
            df, filters = filter_table(df, display_name, filters)
            df = df.drop(columns=list(applied_configs.keys()), errors='ignore')
            applied_configs = {}
            if platform.system() == "Windows":
                os.system('cls')
        
        elif choice == "Clear Filters":
            df = original_df.copy()
            df = df.drop(columns=list(applied_configs.keys()), errors='ignore')
            filters = {}
            applied_configs = {}
            if platform.system() == "Windows":
                os.system('cls')
        
        elif choice == "Export to CSV":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            export_dir = "exports"
            os.makedirs(export_dir, exist_ok=True)
            filename = os.path.join(export_dir, f"table_export_{timestamp}.csv")
            df.to_csv(filename, index=False)
            menu_selection(options, table_str, info_message=f"Table exported to {filename}. Press any key to continue...", middle_content=middle_content)
            input()
            if platform.system() == "Windows":
                os.system('cls')
        
        elif choice == "Wallet Configs":
            wallet_options = ["Apply Wallet Config", "Create Wallet Config Using Filtered Table", "Remove Wallet Configs", "Back"]
            while True:
                wallet_choice = menu_selection(wallet_options, table_str, middle_content)
                if wallet_choice == "Back" or wallet_choice is None:
                    break
                
                if wallet_choice == "Apply Wallet Config":
                    wallets = load_wallets()
                    if not wallets:
                        menu_selection(wallet_options, table_str, info_message="No wallet configs available. Press any key to continue...", middle_content=middle_content)
                        input()
                        continue
                    numbered_wallets = [f"{i+1}: {name}" for i, name in enumerate(wallets.keys())] + ["All", "Back"]
                    wallet_select = menu_selection(numbered_wallets, table_str, middle_content=middle_content, prompt="Select wallets (comma-separated numbers, 'all', or 'back'): ")
                    if wallet_select == "Back" or wallet_select is None:
                        continue
                    if wallet_select.lower() == "all":
                        selected_configs = list(wallets.keys())
                    else:
                        selected_nums = [int(i.strip()) - 1 for i in wallet_select.split(',') if i.strip().isdigit() and 0 <= int(i.strip()) - 1 < len(wallets)]
                        selected_configs = [list(wallets.keys())[num] for num in selected_nums] if selected_nums else []
                    if selected_configs:
                        for config_name in selected_configs:
                            if config_name not in df.columns:
                                df[config_name] = apply_wallet_config(df, config_name, wallets[config_name])
                                applied_configs[config_name] = wallets[config_name]
                        if platform.system() == "Windows":
                            os.system('cls')
                    else:
                        menu_selection(wallet_options, table_str, info_message="No valid configs selected. Press any key to continue...", middle_content=middle_content)
                        input()
                
                elif wallet_choice == "Create Wallet Config Using Filtered Table":
                    name = menu_selection(wallet_options, table_str, prompt="Enter name for new wallet config (or blank to cancel): ", middle_content=middle_content)
                    if name is None or not name.strip():
                        continue
                    selected = menu_selection(wallet_options, table_str, prompt="Enter selection numbers (comma-separated, or 'all'): ", middle_content=middle_content)
                    if selected is None:
                        continue
                    if selected.lower() == "all":
                        selected_df = df.copy()
                    else:
                        selected_nums = [int(i.strip()) for i in selected.split(',') if i.strip().isdigit()]
                        if selected_nums and all(num in df["#"].values for num in selected_nums):
                            selected_df = df.loc[df["#"].isin(selected_nums)]
                        else:
                            menu_selection(wallet_options, table_str, info_message="Invalid selection. Press any key to continue...", middle_content=middle_content)
                            input()
                            continue
                    from wallet_config import DEFAULT_CRITERIA
                    new_config = generate_wallet_config_from_rows(selected_df)
                    create_wallet_config(name, new_config)
                    print(f"'{name}' created")
                    if platform.system() == "Windows":
                        os.system('cls')
                
                elif wallet_choice == "Remove Wallet Configs":
                    if not applied_configs:
                        menu_selection(wallet_options, table_str, info_message="No configs applied. Press any key to continue...", middle_content=middle_content)
                        input()
                        continue
                    remove_options = [f"{i+1}: {name}" for i, name in enumerate(applied_configs.keys())] + ["Remove All", "Back"]
                    remove_choice = menu_selection(remove_options, table_str, middle_content=middle_content)
                    if remove_choice == "Back" or remove_choice is None:
                        continue
                    if remove_choice == "Remove All":
                        df = df.drop(columns=list(applied_configs.keys()))
                        applied_configs.clear()
                        if platform.system() == "Windows":
                            os.system('cls')
                    else:
                        selected_num = int(remove_choice.split(':')[0]) - 1
                        config_name = list(applied_configs.keys())[selected_num]
                        df = df.drop(columns=[config_name])
                        del applied_configs[config_name]
                        if platform.system() == "Windows":
                            os.system('cls')
                
                if platform.system() == "Windows":
                    os.system('cls')
        
        elif choice == "Back" or choice == "Return to menu":
            break
    
    if search_results is not None and not search_results.empty and platform.system() == "Windows":
        os.system('cls')

def search_tables_by_contract(combined_tables):
    contracts = []
    while True:
        contract = input("Enter contract address (or press Enter to finish): ").strip()
        if not contract:
            break
        contracts.append(contract)
    if not contracts:
        return
    
    feed_options = ["PF", "Fomo", "BB", "GM", "MF", "SM"]
    numbered_feeds = [f"{i+1}: {feed}" for i, feed in enumerate(feed_options)] + ["All", "Back"]
    feed_choice = menu_selection(numbered_feeds, "Select feeds to search (comma-separated numbers, or 'all'): ")
    if feed_choice == "Back" or feed_choice is None:
        return
    
    if feed_choice.lower() == "all":
        selected_feeds = feed_options
    else:
        selected_nums = [int(i.strip()) - 1 for i in feed_choice.split(',') if i.strip().isdigit()]
        selected_feeds = [feed_options[i] for i in selected_nums if 0 <= i < len(feed_options)]
    
    if not selected_feeds:
        print("No valid feeds selected. Press any key to continue...")
        input()
        return
    
    results = {}
    for feed in selected_feeds:
        try:
            feed_df = combined_tables[feed.lower()].copy()
            feed_df = feed_df[feed_df['Contract'].isin(contracts)]
            if not feed_df.empty:
                if 'Date' in feed_df.columns and 'Time' in feed_df.columns:
                    feed_df['Date'] = pd.to_datetime(feed_df['Date'], errors='coerce')
                    feed_df['Date'] = feed_df.apply(lambda row: f"{row['Date'].strftime('%d/%m/%y %H:%M')}" if pd.notna(row['Date']) and pd.notna(row['Time']) else 
                                                    f"{row['Date'].strftime('%d/%m/%y')}" if pd.notna(row['Date']) else pd.NA, axis=1)
                    feed_df = feed_df.drop(columns=['Time'])
                if 'Funding' in feed_df.columns:
                    feed_df = feed_df.drop(columns=['FundTime', 'FundSource'], errors='ignore')
                if '#' not in feed_df.columns:
                    feed_df.insert(0, "#", range(1, len(feed_df) + 1))
                results[feed] = feed_df
            menu_selection(["Continue"], f"\n=== Results for {feed.upper()} ===\n" + format_table_columns(feed_df), info_message="Press any key to continue...")
        except KeyError:
            print(f"Warning: Feed '{feed}' not found in combined_tables. Skipping...")
            continue
    
    if not results:
        print("No results found. Press any key to continue...")
        input()
        return
    
    for feed, feed_df in results.items():
        print(f"\n=== Results for {feed.upper()} ===\n")
        print(format_table_columns(feed_df))
        prompt = menu_selection(["Go to PF", "Exit"], "Press Enter to go to PF, ESC to exit:")
        if prompt == "Go to PF":
            display_table("pf", combined_tables, "PF", results.get("PF", pd.DataFrame()))
        else:
            print("\nPress any key to continue...")
            if platform.system() == "Windows":
                msvcrt.getch()
            else:
                curses.wrapper(lambda stdscr: stdscr.getch())