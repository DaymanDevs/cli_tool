import pandas as pd
from datetime import datetime
from wallet_config import apply_wallet_config, DEFAULT_CRITERIA
from data_loader import load_mcaps_csv
from config import DATA_DIRECTORY
from ui_utils import print_filters, menu_selection, format_filter_display
from table_format import format_table_columns
import colorama
from colorama import Fore, Style
from utils import convert_fundtime_to_hours

def filter_table(df, display_name, existing_filters=None):
    filters = existing_filters.copy() if existing_filters else {}
    base_options = [
        "Date", "Name", "Mcap", "Liq", "AG", "Bundle", "Funding", 
        "Dev%", "DevBal", "Links", "F", "KYC", "Unq", "SM", "MaxMcap", "X's", "Back"
    ]
    percent_cols = ["Bundle", "Dev%"]
    
    filtered_df = df.copy()
    filtered_df = filtered_df.rename(columns={"Funding Time": "FundTime", "Funding Source": "FundSource", "Dev Bal": "DevBal", "Has Links": "Links"})
    if 'Funding' not in filtered_df.columns and 'FundTime' in filtered_df.columns and 'FundSource' in filtered_df.columns:
        filtered_df['Funding'] = filtered_df.apply(lambda row: f"{row['FundTime']} ({row['FundSource']})" if pd.notna(row['FundTime']) and pd.notna(row['FundSource']) else pd.NA, axis=1)
        filtered_df = filtered_df.drop(columns=['FundTime', 'FundSource'], errors='ignore')
    
    for column, value in filters.items():
        if column == "Date":
            min_val, max_val = value
            if min_val != float('-inf'):
                min_date = pd.to_datetime(min_val, format='%d/%m/%y %H:%M')
                filtered_df = filtered_df[filtered_df[column] >= min_date]
            if max_val != float('inf'):
                max_date = pd.to_datetime(max_val, format='%d/%m/%y %H:%M')
                filtered_df = filtered_df[filtered_df[column] <= max_date]
        elif column in ["Name"]:
            filtered_df = filtered_df[filtered_df[column].str.lower() == value]
        elif column == "Links":
            filtered_df = filtered_df[filtered_df[column] == value]
        elif column == "Funding":
            min_val = value["min"]
            filtered_df['FundTimeHours'] = filtered_df['Funding'].apply(lambda x: convert_fundtime_to_hours(x.split(' (')[0]) if pd.notna(x) and '(' in x else float('nan'))
            filtered_df = filtered_df[filtered_df['FundTimeHours'] >= min_val].dropna(subset=['FundTimeHours'])
            filtered_df = filtered_df.drop(columns=['FundTimeHours'])
        elif column == "Bundle":
            max_val = value["max"]
            filtered_df = filtered_df[filtered_df[column] <= max_val].dropna(subset=[column])
        elif column == "DevBal":
            max_val = value["max"]
            filtered_df = filtered_df[filtered_df[column] <= max_val].dropna(subset=[column])
        elif column == "X's":
            min_val = value["min"]
            filtered_df = filtered_df[filtered_df[column] >= min_val].dropna(subset=[column])
        else:
            min_val, max_val = value
            filtered_df = filtered_df[(filtered_df[column] >= min_val) & (filtered_df[column] <= max_val)].dropna(subset=[column])
    
    while True:
        filter_options = [
            format_filter_display(opt, filters[opt]) if opt in filters else opt 
            for opt in base_options if opt in filtered_df.columns or opt == "Back"
        ]
        
        table_str = f"{print_filters(filters)}\nRow Count: {len(filtered_df)}\n=== Data for {display_name.upper()} ===\n" + \
                    format_table_columns(filtered_df, [])
        choice = menu_selection(filter_options, table_str)
        if choice == "Back" or choice is None:
            break
        
        column = next(col for col in base_options if choice == col or choice.startswith(col + " ("))
        
        if column == "Date":
            min_date_input = menu_selection(filter_options, table_str, prompt="Enter minimum date (DD/MM/YY HH:MM) or leave blank: ")
            if min_date_input is None:
                continue
            max_date_input = menu_selection(filter_options, table_str, prompt="Enter maximum date (DD/MM/YY HH:MM) or leave blank: ")
            if max_date_input is None:
                continue
            if min_date_input or max_date_input:
                try:
                    min_date = datetime.strptime(min_date_input, "%d/%m/%y %H:%M").strftime("%d/%m/%y %H:%M") if min_date_input else float('-inf')
                    max_date = datetime.strptime(max_date_input, "%d/%m/%y %H:%M").strftime("%d/%m/%y %H:%M") if max_date_input else float('inf')
                    filters["Date"] = [min_date, max_date]
                except ValueError:
                    menu_selection(filter_options, table_str, info_message="Invalid date format (DD/MM/YY HH:MM). Press any key to continue...")
                    input()
            elif "Date" in filters:
                del filters["Date"]
        
        elif column == "Name":
            name_input = menu_selection(filter_options, table_str, prompt="Enter name (case insensitive) or leave blank to skip: ")
            if name_input is None:
                continue
            if name_input:
                filters["Name"] = name_input.lower()
            elif "Name" in filters:
                del filters["Name"]
        
        elif column == "Links" and "Links" in filtered_df.columns:
            yes_no_options = ["Yes", "No", "Skip", "Back"]
            yes_no = menu_selection(yes_no_options, table_str)
            if yes_no == "Back" or yes_no is None:
                continue
            elif yes_no != "Skip":
                filters["Links"] = yes_no
            elif "Links" in filters:
                del filters["Links"]
        
        elif column == "Funding":
            min_val = menu_selection(filter_options, table_str, prompt="Enter minimum FundTime in hours (or leave blank): ")
            if min_val is None:
                continue
            if min_val:
                try:
                    filters[column] = {"min": float(min_val)}
                except ValueError:
                    menu_selection(filter_options, table_str, info_message="Invalid number format. Press any key to continue...")
                    input()
            elif column in filters:
                del filters[column]
        
        elif column == "Bundle":
            max_val = menu_selection(filter_options, table_str, prompt="Enter maximum Bundle % (or leave blank): ")
            if max_val is None:
                continue
            if max_val:
                try:
                    filters[column] = {"max": float(max_val) / 100}
                except ValueError:
                    menu_selection(filter_options, table_str, info_message="Invalid number format. Press any key to continue...")
                    input()
            elif column in filters:
                del filters[column]
        
        elif column == "DevBal":
            max_val = menu_selection(filter_options, table_str, prompt="Enter maximum DevBal (or leave blank): ")
            if max_val is None:
                continue
            if max_val:
                try:
                    filters[column] = {"max": float(max_val)}
                except ValueError:
                    menu_selection(filter_options, table_str, info_message="Invalid number format. Press any key to continue...")
                    input()
            elif column in filters:
                del filters[column]
        
        elif column == "X's":
            min_val = menu_selection(filter_options, table_str, prompt="Enter minimum X's (or leave blank): ")
            if min_val is None:
                continue
            if min_val:
                try:
                    filters[column] = {"min": float(min_val)}
                except ValueError:
                    menu_selection(filter_options, table_str, info_message="Invalid number format. Press any key to continue...")
                    input()
            elif column in filters:
                del filters[column]
        
        else:
            min_val = menu_selection(filter_options, table_str, prompt=f"Enter minimum {column} (or blank for no min): ")
            if min_val is None:
                continue
            max_val = menu_selection(filter_options, table_str, prompt=f"Enter maximum {column} (or blank for no max): ")
            if max_val is None:
                continue
            if min_val or max_val:
                try:
                    min_float = float(min_val) if min_val else float('-inf')
                    max_float = float(max_val) if max_val else float('inf')
                    filters[column] = [min_float, max_float]
                except ValueError:
                    menu_selection(filter_options, table_str, info_message="Invalid number format. Press any key to continue...")
                    input()
            elif column in filters:
                del filters[column]
        
        filtered_df = df.copy()
        filtered_df = filtered_df.rename(columns={"Funding Time": "FundTime", "Funding Source": "FundSource", "Dev Bal": "DevBal", "Has Links": "Links"})
        if 'Funding' not in filtered_df.columns and 'FundTime' in filtered_df.columns and 'FundSource' in filtered_df.columns:
            filtered_df['Funding'] = filtered_df.apply(lambda row: f"{row['FundTime']} ({row['FundSource']})" if pd.notna(row['FundTime']) and pd.notna(row['FundSource']) else pd.NA, axis=1)
            filtered_df = filtered_df.drop(columns=['FundTime', 'FundSource'], errors='ignore')
        for column, value in filters.items():
            if column == "Date":
                min_val, max_val = value
                if min_val != float('-inf'):
                    min_date = pd.to_datetime(min_val, format='%d/%m/%y %H:%M')
                    filtered_df = filtered_df[filtered_df[column] >= min_date]
                if max_val != float('inf'):
                    max_date = pd.to_datetime(max_val, format='%d/%m/%y %H:%M')
                    filtered_df = filtered_df[filtered_df[column] <= max_date]
            elif column in ["Name"]:
                filtered_df = filtered_df[filtered_df[column].str.lower() == value]
            elif column == "Links":
                filtered_df = filtered_df[filtered_df[column] == value]
            elif column == "Funding":
                min_val = value["min"]
                filtered_df['FundTimeHours'] = filtered_df['Funding'].apply(lambda x: convert_fundtime_to_hours(x.split(' (')[0]) if pd.notna(x) and '(' in x else float('nan'))
                filtered_df = filtered_df[filtered_df['FundTimeHours'] >= min_val].dropna(subset=['FundTimeHours'])
                filtered_df = filtered_df.drop(columns=['FundTimeHours'])
            elif column == "Bundle":
                max_val = value["max"]
                filtered_df = filtered_df[filtered_df[column] <= max_val].dropna(subset=[column])
            elif column == "DevBal":
                max_val = value["max"]
                filtered_df = filtered_df[filtered_df[column] <= max_val].dropna(subset=[column])
            elif column == "X's":
                min_val = value["min"]
                filtered_df = filtered_df[filtered_df[column] >= min_val].dropna(subset=[column])
            else:
                min_val, max_val = value
                filtered_df = filtered_df[(filtered_df[column] >= min_val) & (filtered_df[column] <= max_val)].dropna(subset=[column])
    
    return filtered_df, filters

def generate_wallet_summary(df, configs):
    if not configs:
        return ""
    
    stats = {}
    thresholds = [2, 5, 10, 30, 50, 80, 100, 120, 150, 200]
    criteria = ["Buys", "Skips", "Rugs"] + [f"{t}x" for t in thresholds] + ["Best X", "Profit X"]
    
    max_wallet_width = max(len(str(config)) for config in configs) if configs else 12
    
    for config_name in configs:
        if config_name not in df.columns:
            stats[config_name] = {crit: "N/A" for crit in criteria}
            continue
        buys = df[df[config_name] == "buy"]
        skips = len(df) - len(buys)
        rugs = len(buys[buys["X's"] == 0])
        multiples = buys["X's"].dropna()
        threshold_counts = {f"{t}x": len(multiples[multiples >= t]) for t in thresholds}
        highest_multiple = multiples.max() if not multiples.empty else 0
        
        profit_x = 0
        for threshold in thresholds:
            count = threshold_counts.get(f"{threshold}x", 0)
            profit_x += threshold * count
        profit_x -= len(buys)
        
        stats[config_name] = {
            "Buys": len(buys),
            "Skips": skips,
            "Rugs": rugs,
            **threshold_counts,
            "Best X": f"{highest_multiple:.2f}x" if highest_multiple else "0.00x",
            "Profit X": profit_x
        }
    
    table_lines = [f"{'Criteria':<9} | " + " | ".join(f"{Fore.CYAN}{config:<{max_wallet_width}}{Style.RESET_ALL}" for config in configs)]
    table_lines.append("-" * (12 + 3 + max_wallet_width * len(configs) + 3 * (len(configs) - 1)))
    
    for crit in criteria:
        row_values = [stats[config][crit] for config in configs]
        numeric_values = []
        for v in row_values:
            if isinstance(v, str) and 'x' in v:
                try:
                    numeric_values.append(float(v.replace('x', '')))
                except ValueError:
                    numeric_values.append(0)
            elif isinstance(v, (int, float)):
                numeric_values.append(v)
            else:
                numeric_values.append(0)
        max_value = max(numeric_values + [0]) if numeric_values else 0
        row = f"{crit:<9} | "
        for value in row_values:
            if value == 0 or (isinstance(value, str) and value == "0.00x"):
                color = Fore.WHITE
            elif (isinstance(value, str) and 'x' in value and float(value.replace('x', '')) == max_value) or \
                 (isinstance(value, (int, float)) and value == max_value):
                color = Fore.GREEN
            else:
                color = Fore.WHITE
            row += f"{color}{value:<{max_wallet_width}}{Style.RESET_ALL} | "
        table_lines.append(row.rstrip(" | "))
    
    return "\n".join(table_lines)

def generate_wallet_config_from_rows(df):
    config = DEFAULT_CRITERIA.copy()
    if df.empty:
        return config
    
    for key in config.keys():
        if key in df.columns:
            if key == "Links":
                unique_links = df[key].dropna().unique()
                config[key] = unique_links[0] if len(unique_links) == 1 else None
            elif key == "DevBal":
                max_val = df[key].max()
                config[key]["max"] = float(max_val) if pd.notnull(max_val) else float('inf')
            elif key == "Funding":
                hours = df[key].apply(lambda x: convert_fundtime_to_hours(x.split(' (')[0]) if pd.notna(x) and '(' in x else float('nan'))
                min_val = hours.min()
                config[key]["min"] = int(round(min_val)) if pd.notnull(min_val) else 0
            elif key == "Bundle":
                max_val = df[key].max()
                config[key]["max"] = float(max_val) if pd.notnull(max_val) else float('inf')
            elif key == "X's":
                min_val = df[key].min()
                config[key]["min"] = float(min_val) if pd.notnull(min_val) else float('-inf')
            elif key == "Mcap":
                max_val = df[key].max()
                config[key]["max"] = int(round(max_val, -3)) if pd.notnull(max_val) else float('inf')
                config[key]["min"] = int(round(df[key].min(), -3)) if pd.notnull(df[key].min()) else float('-inf')
            else:
                min_val, max_val = df[key].min(), df[key].max()
                if key in ["Liq"]:
                    config[key]["min"] = int(round(min_val, -3)) if pd.notnull(min_val) else float('-inf')
                    config[key]["max"] = int(round(max_val, -3)) if pd.notnull(max_val) else float('inf')
                else:
                    config[key]["min"] = int(round(min_val)) if pd.notnull(min_val) else float('-inf')
                    config[key]["max"] = int(round(max_val)) if pd.notnull(max_val) else float('inf')
    return config

def search_contracts_in_pf(contracts, combined_tables, df):
    if "pf" not in combined_tables:
        print("PF table not found.")
        return
    
    mcaps_df = load_mcaps_csv(DATA_DIRECTORY)
    
    pf_df = combined_tables["pf"][combined_tables["pf"]["Contract"].isin(contracts)]
    if pf_df.empty:
        print("\n=== Search Results in PF ===")
        print("No matching results found.")
    else:
        pf_df = pf_df.sort_values(["Contract", "Date"], ascending=[True, True])
        if "Iteration" in pf_df.columns:
            pf_df = pf_df.drop(columns=["Iteration"])
        pf_df.insert(0, "Iteration", pf_df.groupby("Contract").cumcount() + 1)
        pf_df = pf_df.reset_index(drop=True)
        pf_df = pf_df.rename(columns={"Funding Time": "FundTime", "Funding Source": "FundSource", "Dev Bal": "DevBal", "Has Links": "Links"})
        if 'Funding' not in pf_df.columns and 'FundTime' in pf_df.columns and 'FundSource' in pf_df.columns:
            pf_df['Funding'] = pf_df.apply(lambda row: f"{row['FundTime']} ({row['FundSource']})" if pd.notna(row['FundTime']) and pd.notna(row['FundSource']) else pd.NA, axis=1)
            pf_df = pf_df.drop(columns=['FundTime', 'FundSource'], errors='ignore')
        
        if '#' not in pf_df.columns:
            pf_df.insert(0, "#", range(1, len(pf_df) + 1))
        
        if not mcaps_df.empty:
            pf_df = pf_df.merge(mcaps_df, on='Contract', how='left', suffixes=('', '_mcaps'))
            if 'MaxMcap_mcaps' in pf_df.columns:
                pf_df['MaxMcap'] = pf_df['MaxMcap'].fillna(pf_df['MaxMcap_mcaps'])
                pf_df['X\'s'] = pf_df['X\'s'].fillna(pf_df['MaxMcap'] / pf_df['Mcap']).replace([float('inf'), -float('inf')], 0)
                pf_df = pf_df.drop(columns=['MaxMcap_mcaps'])
        else:
            pf_df['MaxMcap'] = pf_df.get('MaxMcap', 0)
            pf_df['X\'s'] = pf_df.get('X\'s', 0)
        
        print(f"\nRow Count: {len(pf_df)}\n=== Search Results in PF ===")
        print(format_table_columns(pf_df, []))
        prompt = menu_selection(["Go to PF", "Exit"], "Press Enter to go to PF, ESC to exit:")
        if prompt == "Go to PF":
            display_table("pf", combined_tables, "PF", pf_df)
        else:
            print("\nPress any key to continue...")
            if platform.system() == "Windows":
                msvcrt.getch()
            else:
                curses.wrapper(lambda stdscr: stdscr.getch())