import json
import os
from ui_utils import menu_selection
from config import WALLETS_FILE
import colorama
from colorama import Fore, Style

def format_wallet_table(wallets):
    if not wallets:
        return None
    
    headers = ["Name", "Mcap", "Liq", "AG", "Bundle", "Funding", "Dev%", "DevBal", "Links", "F", "KYC", "Unq", "SM", "X's"]
    col_widths = {header: len(header) for header in headers}
    col_widths["Name"] = max(col_widths["Name"], max((len(name) for name in wallets.keys()), default=0))
    
    rows = []
    for name, criteria in wallets.items():
        row = [name]
        for key in headers[1:]:
            if key == "Links":
                value = str(criteria.get(key, "Any"))
            elif key in ["Mcap", "Liq", "DevBal", "F", "KYC", "Unq", "SM"]:
                min_val = criteria.get(key, {}).get("min", float('-inf'))
                max_val = criteria.get(key, {}).get("max", float('inf'))
                value = f"{min_val:,} - {max_val:,}" if min_val != float('-inf') or max_val != float('inf') else "Any"
            elif key in ["Bundle", "Dev%"]:
                max_val = criteria.get(key, {}).get("max", float('inf'))
                value = f"<= {max_val*100:.2f}%" if max_val != float('inf') else "Any"
            elif key == "Funding":
                min_val = criteria.get(key, {}).get("min", 0)
                value = f">= {min_val}h" if min_val > 0 else "Any"
            elif key == "X's":
                min_val = criteria.get(key, {}).get("min", float('-inf'))
                value = f">= {min_val:.2f}x" if min_val != float('-inf') else "Any"
            else:
                min_val = criteria.get(key, {}).get("min", float('-inf'))
                max_val = criteria.get(key, {}).get("max", float('inf'))
                value = f"{min_val} - {max_val}" if min_val != float('-inf') or max_val != float('inf') else "Any"
            row.append(value)
            col_widths[key] = max(col_widths[key], len(value))
        rows.append(row)
    
    header_row = " | ".join(f"{Fore.CYAN}{header:<{col_widths[header]}}{Style.RESET_ALL}" for header in headers)
    separator = "-" * (sum(col_widths.values()) + 3 * (len(headers) - 1))
    formatted_rows = [header_row, separator]
    for row in rows:
        formatted_row = " | ".join(f"{val:<{col_widths[headers[i]]}}" for i, val in enumerate(row))
        formatted_rows.append(formatted_row)
    
    return "\n".join(formatted_rows)

def update_criteria(criteria, wallet_name, existing_names):
    options = list(criteria.keys()) + ["Save", "Save As", "Back"]
    while True:
        formatted_table = format_wallet_table({wallet_name: criteria})
        choice = menu_selection(options, formatted_table)
        if choice == "Back" or choice is None:
            return None
        elif choice == "Save":
            return True
        elif choice == "Save As":
            new_name = menu_selection(options, formatted_table, prompt="Enter new wallet name (or blank to cancel): ")
            if new_name and new_name not in existing_names:
                return new_name
            elif new_name in existing_names:
                menu_selection(options, formatted_table, info_message="Name already exists. Press any key to continue...")
                input()
            continue
        
        key = choice
        if key == "Links":
            yes_no_options = ["Yes", "No", "Any", "Back"]
            yes_no = menu_selection(yes_no_options, formatted_table)
            if yes_no == "Back" or yes_no is None:
                continue
            elif yes_no == "Any":
                criteria[key] = None
            else:
                criteria[key] = yes_no
        
        elif key in ["Mcap", "Liq", "AG", "F", "KYC", "Unq", "SM", "DevBal"]:
            min_val = menu_selection(options, formatted_table, prompt=f"Enter minimum {key} (or blank for no min): ")
            if min_val is None:
                continue
            max_val = menu_selection(options, formatted_table, prompt=f"Enter maximum {key} (or blank for no max): ")
            if max_val is None:
                continue
            try:
                min_float = float(min_val) if min_val else float('-inf')
                max_float = float(max_val) if max_val else float('inf')
                criteria[key] = {"min": min_float, "max": max_float}
            except ValueError:
                menu_selection(options, formatted_table, info_message="Invalid number format. Press any key to continue...")
                input()
        
        elif key in ["Bundle", "Dev%"]:
            max_val = menu_selection(options, formatted_table, prompt=f"Enter maximum {key} % (or blank for no max): ")
            if max_val is None:
                continue
            try:
                max_float = float(max_val) / 100 if max_val else float('inf')
                criteria[key] = {"max": max_float}
            except ValueError:
                menu_selection(options, formatted_table, info_message="Invalid number format. Press any key to continue...")
                input()
        
        elif key == "Funding":
            min_val = menu_selection(options, formatted_table, prompt="Enter minimum Funding time in hours (or blank for no min): ")
            if min_val is None:
                continue
            try:
                min_float = float(min_val) if min_val else 0
                criteria[key] = {"min": min_float}
            except ValueError:
                menu_selection(options, formatted_table, info_message="Invalid number format. Press any key to continue...")
                input()
        
        elif key == "X's":
            min_val = menu_selection(options, formatted_table, prompt="Enter minimum X's (or blank for no min): ")
            if min_val is None:
                continue
            try:
                min_float = float(min_val) if min_val else float('-inf')
                criteria[key] = {"min": min_float}
            except ValueError:
                menu_selection(options, formatted_table, info_message="Invalid number format. Press any key to continue...")
                input()