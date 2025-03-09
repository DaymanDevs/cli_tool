import pandas as pd
from table_format import format_table_columns
from table_utils import filter_table, generate_wallet_summary, search_contracts_in_pf, generate_wallet_config_from_rows
from ui_utils import menu_selection, print_filters, get_terminal_height
from wallet_config import load_wallets, apply_wallet_config, create_wallet_config, DEFAULT_CRITERIA
from data_loader import load_mcaps_db
from config import DATA_DIRECTORY
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
    is_top_table = table_name.endswith('10')
    base_name = table_name.replace('10', '')
    
    if search_results is not None and not search_results.empty:
        df = search_results.copy()
    else:
        if is_top_table:
            columns = 'Contract, Name, Mcap, HighestMcap, Multiples'
            query = f"SELECT {columns} FROM {table_name} ORDER BY Multiples DESC"
            try:
                df = pd.read_sql_query(query, conn)
            except pd.io.sql.DatabaseError as e:
                print(f"Database error: {e}")
                return
        else:
            columns = 'token, Date, Name, Mcap, Liq, "Liq%", AG, Bundle, FundingTime, FundingSource, Funding, "Dev%", DevBal, Links, F, KYC, Unq, SM, TTC, "B-Ratio", FreshDeployer, Drained, Desc'
            query = f"SELECT {columns} FROM {base_name}"  # No LIMIT to fetch all rows
            try:
                df = pd.read_sql_query(query, conn)
            except pd.io.sql.DatabaseError as e:
                print(f"Database error: {e}")
                return
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # Merge with Top table data if exists
            top_table = f"{base_name}10"
            if top_table in pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)['name'].values:
                top_df = pd.read_sql_query(f"SELECT Contract AS token, HighestMcap AS MaxMcap FROM {top_table}", conn)
                df = df.merge(top_df, on='token', how='left', suffixes=('', '_top'))
                if 'MaxMcap_top' in df.columns:
                    df['MaxMcap'] = df['MaxMcap_top'].fillna(df.get('MaxMcap', df['Mcap']))
                    df = df.drop(columns=['MaxMcap_top'], errors='ignore')
            
            # Merge with MCAPS data, prioritizing Top table MaxMcap
            if not mcaps_df.empty:
                df = df.merge(mcaps_df, on='token', how='left', suffixes=('', '_mcaps'))
                if 'MaxMcap_mcaps' in df.columns:
                    df['MaxMcap'] = df['MaxMcap'].fillna(df['MaxMcap_mcaps']).fillna(df['Mcap'])
                    df = df.drop(columns=['MaxMcap_mcaps'], errors='ignore')
            
            df["X's"] = (df['MaxMcap'] / df['Mcap']).replace([float('inf'), -float('inf')], 0).fillna(0)
            df = df.sort_values('Date', ascending=False)
    
    total_rows = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table_name}", conn).iloc[0]['count']
    if '#' not in df.columns:
        df.insert(0, "#", range(1, len(df) + 1))
    original_df = df.copy()
    filters = {}
    applied_configs = {}
    page = 0
    
    while True:
        options = ["Return to menu", "Search in PF", "Filter Table", "Clear Filters", "Export to CSV", "Wallet Configs", "Next Page", "Prev Page", "Back"]
        middle_content = generate_wallet_summary(df, applied_configs.keys())
        if not middle_content:
            middle_content = ""
        
        terminal_height = get_terminal_height()
        menu_lines = len(options) + 2
        middle_lines = middle_content.count('\n') + 1 if middle_content else 0
        header_lines = 4  # Filters, Rows, Title, Table header
        rows_per_page = max(1, terminal_height - menu_lines - middle_lines - header_lines)
        start_idx = page * rows_per_page
        end_idx = min((page + 1) * rows_per_page, len(df))
        visible_df = df.iloc[start_idx:end_idx]
        table_str_full = f"{print_filters(filters)}\nRows: {len(df)} of {total_rows}\n=== Data for {display_name.upper()} ===\n" + \
                        format_table_columns(visible_df, applied_configs)
        
        table_lines = table_str_full.split('\n')
        table_str = '\n'.join(table_lines[:terminal_height - menu_lines - middle_lines])
        
        choice = menu_selection(options, table_str, middle_content, prompt=f"=== {display_name.upper()} ===")
        if choice in ["Back", "Return to menu"] or choice is None:
            break
        
        if choice == "Search in PF" and not is_top_table:
            selected = menu_selection(options, table_str, middle_content, prompt="Enter selection numbers (comma-separated, or 'all'): ", allow_input=True)
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
            page = 0
        
        elif choice == "Clear Filters":
            df = original_df.copy()
            df = df.drop(columns=list(applied_configs.keys()), errors='ignore')
            filters = {}
            applied_configs = {}
            page = 0
        
        elif choice == "Export to CSV":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            export_dir = "exports"
            os.makedirs(export_dir, exist_ok=True)
            filename = os.path.join(export_dir, f"table_export_{timestamp}.csv")
            df.to_csv(filename, index=False)
            menu_selection(options, table_str, middle_content, info_message=f"Table exported to {filename}. Press any key to continue...")
            input()
        
        elif choice == "Wallet Configs" and not is_top_table:
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
                        break
                    if wallet_select.lower() == "all":
                        selected_configs = list(wallets.keys())
                    else:
                        try:
                            selected_nums = [int(i.strip()) - 1 for i in wallet_select.split(',') if i.strip().isdigit() and 0 <= int(i.strip()) - 1 < len(wallets)]
                            selected_configs = [list(wallets.keys())[num] for num in selected_nums] if selected_nums else []
                        except ValueError:
                            selected_configs = []
                    if selected_configs:
                        for config_name in selected_configs:
                            if config_name not in df.columns:
                                df[config_name] = apply_wallet_config(df, config_name, wallets[config_name])
                                applied_configs[config_name] = wallets[config_name]
                        page = 0
                    else:
                        menu_selection(wallet_options, table_str, middle_content, info_message="No valid configs selected. Press any key to continue...")
                        input()
                    break
                
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
                    page = 0
        
        elif choice == "Next Page":
            if (page + 1) * rows_per_page < len(df):
                page += 1
        elif choice == "Prev Page":
            if page > 0:
                page -= 1

def search_tables_by_contract(conn):
    contract = menu_selection([], "", prompt="Enter contract address to search: ", allow_input=True)
    if not contract:
        return
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'mcaps'")
    feed_tables = [row[0] for row in cursor.fetchall()]
    
    results = []
    for table in feed_tables:
        if table.endswith('10'):
            query = f"SELECT Contract AS token, Name, Mcap, HighestMcap AS MaxMcap, Multiples AS \"X's\" FROM {table} WHERE Contract LIKE ?"
        else:
            query = f"SELECT * FROM {table} WHERE token LIKE ?"
        df = pd.read_sql_query(query, conn, params=(f"%{contract}%",))
        if not df.empty:
            df['Feed'] = table.replace('_', ' ').title().replace('10', ' Top')
            if not table.endswith('10') and 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            results.append(df)
    
    if results:
        combined_df = pd.concat(results, ignore_index=True)
        display_table('search_results', conn, f"Search Results for '{contract}'", search_results=combined_df)
    else:
        print(f"No results found for contract '{contract}'. Press any key to continue...")
        input()