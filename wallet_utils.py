import pandas as pd
import json
from ui_utils import menu_selection
from utils import format_criteria_value
from wallet_config import DEFAULT_CRITERIA, load_wallets, save_wallets
import colorama
from colorama import Fore, Style

def format_wallet_table(wallets):
    if not wallets:
        return None
    
    headers = list(wallets.keys())
    criteria = [
        "Targeted Feed", "Mcap", "Liq", "AG", "DevBal", "Funding", 
        "Bundle", "Links", "F", "KYC", "Unq", "SM", "MaxMcap", "X's"
    ]
    
    max_widths = {}
    for header in headers:
        wallet_criteria = wallets[header]
        max_width = max(len(str(header)), max(len(str(format_criteria_value(crit, wallet_criteria.get(crit, "N/A")))) for crit in criteria))
        max_widths[header] = max_width
    
    table_lines = []
    header_line = "Criteria".ljust(9) + " | " + " | ".join(f"{Fore.CYAN}{header:<{max_widths[header]}}{Style.RESET_ALL}" for header in headers)
    table_lines.append(header_line)
    table_lines.append("-" * (9 + 3 + sum(max_widths.values()) + 3 * (len(headers) - 1)))
    
    for crit in criteria:
        row = f"{crit:<9} | "
        for header in headers:
            wallet_criteria = wallets[header]
            value = format_criteria_value(crit, wallet_criteria.get(crit, "N/A"))
            row += f"{value:<{max_widths[header]}} | "
        table_lines.append(row.rstrip(" | "))
    
    return "\n".join(table_lines)

def update_criteria(criteria, wallet_name, wallet_names):
    options = ["Targeted Feed", "Mcap", "Liq", "AG", "DevBal", "Funding", "Bundle", "Links", "F", "KYC", "Unq", "SM", "MaxMcap", "X's", "Back"]
    while True:
        table_str = f"Editing '{wallet_name}'\n" + format_wallet_table({wallet_name: criteria})
        choice = menu_selection(options, table_str)
        if choice == "Back" or choice is None:
            break
        
        if choice == "Targeted Feed":
            feed_options = ["PF", "Fomo", "BB", "GM", "MF", "SM", "None", "Back"]
            feed = menu_selection(feed_options, table_str)
            if feed == "Back" or feed is None:
                continue
            elif feed == "None":
                criteria["Targeted Feed"] = None
            else:
                criteria["Targeted Feed"] = feed
        
        elif choice == "Links":
            yes_no_options = ["Yes", "No", "None", "Back"]
            yes_no = menu_selection(yes_no_options, table_str)
            if yes_no == "Back" or yes_no is None:
                continue
            elif yes_no == "None":
                criteria["Links"] = None
            else:
                criteria["Links"] = yes_no
        
        elif choice == "Funding":
            min_val = menu_selection(options, table_str, prompt="Enter minimum Funding hours (or blank for no min): ")
            if min_val is None:
                continue
            if min_val:
                try:
                    criteria["Funding"]["min"] = float(min_val)
                except ValueError:
                    menu_selection(options, table_str, info_message="Invalid number format. Press any key to continue...")
                    input()
            else:
                criteria["Funding"]["min"] = 0
        
        elif choice == "Bundle":
            max_val = menu_selection(options, table_str, prompt="Enter maximum Bundle % (or blank for no max): ")
            if max_val is None:
                continue
            if max_val:
                try:
                    criteria["Bundle"]["max"] = float(max_val) / 100
                except ValueError:
                    menu_selection(options, table_str, info_message="Invalid number format. Press any key to continue...")
                    input()
            else:
                criteria["Bundle"]["max"] = float('inf')
        
        elif choice == "DevBal":
            max_val = menu_selection(options, table_str, prompt="Enter maximum DevBal (or blank for no max): ")
            if max_val is None:
                continue
            if max_val:
                try:
                    criteria["DevBal"]["max"] = float(max_val)
                except ValueError:
                    menu_selection(options, table_str, info_message="Invalid number format. Press any key to continue...")
                    input()
            else:
                criteria["DevBal"]["max"] = float('inf')
        
        elif choice == "X's":
            min_val = menu_selection(options, table_str, prompt="Enter minimum X's (or blank for no min): ")
            if min_val is None:
                continue
            if min_val:
                try:
                    criteria["X's"]["min"] = float(min_val)
                except ValueError:
                    menu_selection(options, table_str, info_message="Invalid number format. Press any key to continue...")
                    input()
            else:
                criteria["X's"]["min"] = float('-inf')
        
        else:
            min_val = menu_selection(options, table_str, prompt=f"Enter minimum {choice} (or blank for no min): ")
            if min_val is None:
                continue
            max_val = menu_selection(options, table_str, prompt=f"Enter maximum {choice} (or blank for no max): ")
            if max_val is None:
                continue
            if min_val or max_val:
                try:
                    min_float = float(min_val) if min_val else float('-inf')
                    max_float = float(max_val) if max_val else float('inf')
                    criteria[choice] = {"min": min_float, "max": max_float}
                except ValueError:
                    menu_selection(options, table_str, info_message="Invalid number format. Press any key to continue...")
                    input()
            elif choice in criteria:
                criteria[choice] = DEFAULT_CRITERIA[choice]
    
    overwrite_options = ["Save", "Save As", "Discard", "Back"]
    while True:
        overwrite = menu_selection(overwrite_options, table_str)
        if overwrite == "Back" or overwrite is None:
            return False
        elif overwrite == "Save":
            return True
        elif overwrite == "Save As":
            new_name = menu_selection(overwrite_options, table_str, prompt="Enter new wallet name (or blank to cancel): ")
            if new_name is None or not new_name.strip():
                continue
            if new_name in wallet_names:
                menu_selection(overwrite_options, table_str, info_message="Name already exists. Press any key to continue...")
                input()
                continue
            save_wallets({new_name: criteria, **load_wallets()})
            return True
        elif overwrite == "Discard":
            return False