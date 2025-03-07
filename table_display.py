from table_format import format_table_columns
from table_utils import filter_table, generate_wallet_summary, search_contracts_in_pf, generate_wallet_config_from_rows
from ui_utils import menu_selection, print_filters, get_terminal_height
from wallet_config import load_wallets, apply_wallet_config, create_wallet_config, DEFAULT_CRITERIA
from data_loader import load_mcaps_db
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

def display_table(table_name, conn, display_name, search_results=None):
    if conn is None:
        print("Error: Database connection failed.")
        return
    
    mcaps_df = load_mcaps_db(conn)
    is_top_table = "top" in display_name.lower()
    base_name = table_name.lower().replace(" top", "")
    
    if search_results is not None and not search_results.empty:
        df = search_results.copy()
    else:
        query = f"SELECT * FROM {base_name} ORDER BY Date DESC LIMIT 1000"
        df = pd.read_sql_query(query, conn)
        df = df.rename(columns={"Funding Time": "FundTime", "Funding Source": "FundSource", "Dev Bal": "DevBal", "Has Links": "Links"})
        
        # Combine Date and Time if both exist
        if 'Date' in df.columns and 'Time' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce', dayfirst=True, format='%d/%m/%y %H:%M')
            df = df.drop(columns=['Time'], errors='ignore')
        
        # Handle MCAPS and Top table data
        top_contracts = set()
        if is_top_table:
            top_key = f"{base_name}10"
            top_df = pd.read_sql_query(f"SELECT token, MaxMcap FROM {top_key}", conn)
            if not top_df.empty:
                top_contracts = set(top_df['token'])
                df = df.merge(top_df, on='token', how='left', suffixes=('', '_top'))
                if 'MaxMcap_top' in df.columns:
                    df['MaxMcap'] = df['MaxMcap_top'].fillna(df['MaxMcap'])
                    df = df.drop(columns=[col for col in df.columns if col.endswith('_top')], errors='ignore')
        
        if not mcaps_df.empty:
            df = df.merge(mcaps_df, on='token', how='left', suffixes=('', '_mcaps'))
            mask = ~df['token'].isin(top_contracts)
            if 'MaxMcap_mcaps' in df.columns:
                df.loc[mask, 'MaxMcap'] = df.loc[mask, 'MaxMcap'].fillna(df['MaxMcap_mcaps'])
                df = df.drop(columns=['MaxMcap_mcaps'], errors='ignore')
        
        # Calculate X's dynamically
        df['X\'s'] = (df['MaxMcap'] / df['Mcap']).replace([float('inf'), -float('inf')], 0).fillna(0)
        
        if 'Funding' in df.columns:
            df = df.drop(columns=['FundTime', 'FundSource'], errors='ignore')
        
        # Drop unwanted columns
        df = df.drop(columns=['top_20_holders', 'token_age_days'], errors='ignore')
        
        if base_name == 'pf':
            df = df.sort_values(["token", "Date"], ascending=[True, True])
            if 'Iteration' in df.columns:
                df = df.drop(columns=["Iteration"])
            df.insert(0, "Iteration", df.groupby("token").cumcount() + 1)
            df = df.sort_values("Date", ascending=False)
    
    total_rows = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {base_name}", conn).iloc[0]['count']
    if '#' not in df.columns:
        df.insert(0, "#", range(1, len(df) + 1))
    original_df = df.copy()
    filters = {}
    applied_configs = {}
    
    while True:
        options = ["Return to menu", "Search in PF", "Filter Table", "Clear Filters", "Export to CSV", "Wallet Configs", "Back"]
        middle_content = generate_wallet_summary(df, applied_configs.keys())
        if not middle_content:
            middle_content = ""
        table_str_full = f"{print_filters(filters)}\nRow Count: {total_rows} (Showing {len(df)})\n=== Data for {display_name.upper()} ===\n" + \
                        format_table_columns(df, applied_configs)
        
        terminal_height = get_terminal_height()
        menu_lines = len(options) + 2
        middle_lines = middle_content.count('\n') + 1 if middle_content else 0
        max_table_lines = terminal_height - menu_lines - middle_lines - 2
        table_lines = table_str_full.split('\n')
        table_str = '\n'.join(table_lines[:max(0, min(max_table_lines, len(table_lines)))])
        
        choice = menu_selection(options, table_str, middle_content, prompt=f"=== {display_name.upper()} ===")
        if choice == "Back" or choice == "Return to menu" or choice is None:
            break
        
        if choice == "Search in PF":
            selected = menu_selection(options, table_str, middle_content, prompt="Enter selection numbers (comma-separated, or 'all'): ")
            if selected is None:
                continue
            if selected.lower() == "all":
                contracts = df["token"].tolist()
                search_contracts_in_pf(contracts, conn, df)
            else:
                selected_nums = [int(i.strip()) for i in selected.split(',') if i.strip().isdigit()]
                if selected_nums and all(num in df["#"].values for num in selected_nums):
                    filtered_df = df.loc[df["#"].isin(selected_nums)]
                    contracts = filtered_df["token"].tolist()
                    search_contracts_in_pf(contracts, conn, filtered_df)
                else:
                    menu_selection(options, table_str, middle_content, info_message="Invalid selection. Press any key to continue...")
                    input()
        
        elif choice == "Filter Table":
            df, filters = filter_table(df, display_name, filters)
            df = df.drop(columns=list(applied_configs.keys()), errors='ignore')
            applied_configs = {}
        
        elif choice == "Clear Filters":
            df = original_df.copy()
            df = df.drop(columns=list(applied_configs.keys()), errors='ignore')
            filters = {}
            applied_configs = {}
        
        elif choice == "Export to CSV":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            export_dir = "exports"
            os.makedirs(export_dir, exist_ok=True)
            filename = os.path.join(export_dir, f"table_export_{timestamp}.csv")
            df.to_csv(filename, index=False)
            menu_selection(options, table_str, middle_content, info_message=f"Table exported to {filename}. Press any key to continue...")
            input()
        
        elif choice == "Wallet Configs":
            wallet_options = ["Apply Wallet Config", "Create Wallet Config Using Filtered Table", "Remove Wallet Configs", "Back"]
            while True:
                wallet_choice = menu_selection(wallet_options, table_str, middle_content)
                if wallet_choice == "Back" or wallet_choice is None:
                    break
                
                if wallet_choice == "Apply Wallet Config":
                    wallets = load_wallets()
                    if not wallets:
                        menu_selection(wallet_options, table_str, middle_content, info_message="No wallet configs available. Press any key to continue...")
                        input()
                        continue
                    numbered_wallets = [f"{i+1}: {name}" for i, name in enumerate(wallets.keys())] + ["All", "Back"]
                    wallet_select = menu_selection(numbered_wallets, table_str, middle_content, prompt="Select wallets (comma-separated numbers, 'all', or 'back'): ", allow_input=True)
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
                    else:
                        menu_selection(wallet_options, table_str, middle_content, info_message="No valid configs selected. Press any key to continue...")
                        input()
                
                elif wallet_choice == "Create Wallet Config Using Filtered Table":
                    name = menu_selection(wallet_options, table_str, middle_content, prompt="Enter name for new wallet config (or blank to cancel): ", allow_input=True)
                    if name is None or not name.strip():
                        continue
                    selected = menu_selection(wallet_options, table_str, middle_content, prompt="Enter selection numbers (comma-separated, or 'all'): ", allow_input=True)
                    if selected is None:
                        continue
                    if selected.lower() == "all":
                        selected_df = df.copy()
                    else:
                        selected_nums = [int(i.strip()) for i in selected.split(',') if i.strip().isdigit()]
                        if selected_nums and all(num in df["#"].values for num in selected_nums):
                            selected_df = df.loc[df["#"].isin(selected_nums)]
                        else:
                            menu_selection(wallet_options, table_str, middle_content, info_message="Invalid selection. Press any key to continue...")
                            input()
                            continue
                    new_config = generate_wallet_config_from_rows(selected_df)
                    create_wallet_config(name, new_config)
                    print(f"'{name}' created")
                    input("Press any key to continue...")
                
                elif wallet_choice == "Remove Wallet Configs":
                    if not applied_configs:
                        menu_selection(wallet_options, table_str, middle_content, info_message="No configs applied. Press any key to continue...")
                        input()
                        continue
                    remove_options = [f"{i+1}: {name}" for i, name in enumerate(applied_configs.keys())] + ["Remove All", "Back"]
                    remove_choice = menu_selection(remove_options, table_str, middle_content)
                    if remove_choice == "Back" or remove_choice is None:
                        continue
                    if remove_choice == "Remove All":
                        df = df.drop(columns=list(applied_configs.keys()))
                        applied_configs.clear()
                    else:
                        selected_num = int(remove_choice.split(':')[0]) - 1
                        config_name = list(applied_configs.keys())[selected_num]
                        df = df.drop(columns=[config_name])
                        del applied_configs[config_name]

def search_tables_by_contract(conn):
    if conn is None:
        print("Error: Database connection failed.")
        return
    
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
    feed_choice = menu_selection(numbered_feeds, "", prompt="Select feeds to search (comma-separated numbers, or 'all'): ", allow_input=True)
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
    mcaps_df = load_mcaps_db(conn)
    top_contracts = set()
    for feed in ['fomo10', 'bb10', 'gm10', 'mf10', 'sm10']:
        top_df = pd.read_sql_query(f"SELECT token FROM {feed}", conn)
        top_contracts.update(top_df['token'])
    
    for feed in selected_feeds:
        try:
            query = f"SELECT * FROM {feed.lower()} WHERE token IN ({','.join(['?' for _ in contracts])})"
            feed_df = pd.read_sql_query(query, conn, params=contracts)
            if not feed_df.empty:
                if 'Date' in feed_df.columns and 'Time' in feed_df.columns:
                    feed_df['Date'] = pd.to_datetime(feed_df['Date'] + ' ' + feed_df['Time'], errors='coerce', dayfirst=True, format='%d/%m/%y %H:%M')
                    feed_df = feed_df.drop(columns=['Time'], errors='ignore')
                feed_df = feed_df.sort_values(["Date"], ascending=[True])
                if 'Iteration' in feed_df.columns:
                    feed_df = feed_df.drop(columns=["Iteration"])
                feed_df.insert(0, "Iteration", feed_df.groupby("token").cumcount() + 1)
                feed_df = feed_df.reset_index(drop=True)
                if 'Funding' in feed_df.columns:
                    feed_df = feed_df.drop(columns=['FundTime', 'FundSource'], errors='ignore')
                if not mcaps_df.empty:
                    feed_df = feed_df.merge(mcaps_df, on='token', how='left', suffixes=('', '_mcaps'))
                    mask = ~feed_df['token'].isin(top_contracts)
                    if 'MaxMcap_mcaps' in feed_df.columns:
                        feed_df.loc[mask, 'MaxMcap'] = feed_df.loc[mask, 'MaxMcap'].fillna(feed_df['MaxMcap_mcaps'])
                        feed_df = feed_df.drop(columns=['MaxMcap_mcaps'], errors='ignore')
                feed_df['X\'s'] = (feed_df['MaxMcap'] / feed_df['Mcap']).replace([float('inf'), -float('inf')], 0).fillna(0)
                if '#' not in feed_df.columns:
                    feed_df.insert(0, "#", range(1, len(feed_df) + 1))
                results[feed] = feed_df
        except Exception as e:
            print(f"Warning: Error loading feed '{feed}': {e}")
            continue
    
    if not results:
        print("No results found. Press any key to continue...")
        input()
        return
    
    combined_output = []
    for feed, feed_df in results.items():
        combined_output.append(f"Row Count: {len(feed_df)}\n=== Results for {feed.upper()} ===\n{format_table_columns(feed_df, [])}")
    combined_table = "\n\n".join(combined_output)
    prompt = menu_selection(["Go to PF", "Go to SM", "Exit"], combined_table, prompt="Press Enter to go to PF, S for SM, ESC to exit:")
    if prompt == "Go to PF":
        display_table("pf", conn, "PF", results.get("PF", pd.DataFrame()))
    elif prompt == "Go to SM":
        display_table("sm", conn, "SM", results.get("SM", pd.DataFrame()))
    else:
        print("\nPress any key to continue...")
        if platform.system() == "Windows":
            msvcrt.getch()
        else:
            curses.wrapper(lambda stdscr: stdscr.getch())