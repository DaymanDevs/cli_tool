import colorama
from colorama import Fore, Style
from ui_utils import menu_selection
from wallet_config import DEFAULT_CRITERIA, load_wallets, create_wallet_config, duplicate_wallet_config
from utils import format_criteria_value

def update_criteria(criteria, wallet_name, options):
    while True:
        crit_options = [f"{k} ({format_criteria_value(k, v)})" for k, v in criteria.items()] + ["Targeted Feed", "Save and Exit", "Duplicate Wallet"]
        title = f"Editing {wallet_name}\n\n"
        choice = menu_selection(crit_options, title + "Edit Wallet Criteria:")
        if choice == "Save and Exit":
            return True
        if choice == "Duplicate Wallet":
            new_name = menu_selection(options, prompt=f"Enter new name for duplicate of '{wallet_name}': ")
            if new_name is None:
                continue
            if new_name and new_name not in load_wallets():
                duplicate_wallet_config(wallet_name, new_name)
                wallets = load_wallets()  # Reload to ensure new wallet is available
                print(f"'{new_name}' created as duplicate of '{wallet_name}'")
                new_criteria = wallets[new_name]
                if update_criteria(new_criteria, new_name, options) is False:
                    continue
                create_wallet_config(new_name, new_criteria)
                print(f"'{new_name}' updated. Press Enter to continue...")
                input()
            elif new_name in load_wallets():
                print("Name already exists. Press Enter to continue...")
                input()
            continue
        if choice == "Targeted Feed":
            feed_options = ["PF", "Fomo", "BB", "GM", "MF", "SM", "Back"]
            feed_choice = menu_selection(feed_options, title + "Select Targeted Feed:")
            if feed_choice != "Back" and feed_choice is not None:
                criteria["Targeted Feed"] = feed_choice  # Updated to "Targeted Feed"
            continue
        if choice is None:
            return False
        
        key = choice.split(" (")[0]
        if key == "Links":
            yes_no = menu_selection(["Yes", "No", "None", "Back"], f"Set {key}:")
            if yes_no == "Back" or yes_no is None:
                continue
            criteria[key] = yes_no if yes_no != "None" else None
        elif key == "DevBal":
            max_val = menu_selection(crit_options, prompt="Enter maximum (or blank for no max): ")
            if max_val is None:
                continue
            try:
                criteria[key]["max"] = float(max_val) if max_val else float('inf')  # Plain number, no dollar sign
            except ValueError:
                print("Invalid number. Press Enter to continue...")
                input()
        elif key == "Funding":
            min_val = menu_selection(crit_options, prompt="Enter minimum FundTime in hours (or leave blank): ")  # Changed to minimum
            if min_val is None:
                continue
            try:
                criteria[key]["min"] = float(min_val) if min_val else 0  # Buy if FundTime >= min_val
            except ValueError:
                print("Invalid number. Press Enter to continue...")
                input()
        elif key == "Bundle":
            max_val = menu_selection(crit_options, prompt="Enter maximum % (or blank for no max): ")
            if max_val is None:
                continue
            try:
                criteria[key]["max"] = float(max_val.replace('%', '')) / 100 if max_val else float('inf')
            except ValueError:
                print("Invalid number. Press Enter to continue...")
                input()
        elif key in ["AG", "F", "KYC", "Unq", "SM"]:
            min_val = menu_selection(crit_options, prompt="Enter minimum (or blank for no min): ")
            if min_val is None:
                continue
            max_val = menu_selection(crit_options, prompt="Enter maximum (or blank for no max): ")
            if max_val is None:
                continue
            try:
                criteria[key]["min"] = float(min_val) if min_val else float('-inf')  # Plain numbers, no dollar signs
                criteria[key]["max"] = float(max_val) if max_val else float('inf')
            except ValueError:
                print("Invalid number. Press Enter to continue...")
                input()
        else:
            min_val = menu_selection(crit_options, prompt="Enter minimum (or blank for no min): ")
            if min_val is None:
                continue
            max_val = menu_selection(crit_options, prompt="Enter maximum (or blank for no max): ")
            if max_val is None:
                continue
            try:
                criteria[key]["min"] = float(min_val.replace('$', '').replace(',', '')) if min_val else float('-inf')
                criteria[key]["max"] = float(max_val.replace('$', '').replace(',', '')) if max_val else float('inf')
            except ValueError:
                print("Invalid number. Press Enter to continue...")
                input()

def format_wallet_table(wallets):
    if not wallets:
        return "No wallets available."
    
    criteria = list(next(iter(wallets.values())).keys()) if wallets else []
    headers = list(wallets.keys())
    # Calculate dynamic column widths based on longest value for each wallet
    column_widths = {}
    for header in headers:
        max_width = max(len(str(header)), max(len(str(format_criteria_value(crit, wallets[header][crit]))) for crit in criteria))
        column_widths[header] = max(12, max_width)  # Minimum 12 chars for readability
    criteria_width = 9  # Fixed width for "Criteria"
    
    table_lines = [f"{'Criteria':<{criteria_width}} | " + " | ".join(f"{Fore.CYAN}{header:<{column_widths[header]}}{Style.RESET_ALL}" for header in headers)]
    table_lines.append("-" * (criteria_width + 3 + sum(column_widths.values()) + 3 * (len(headers) - 1)))  # Separators
    
    for crit in criteria:
        row = f"{crit:<{criteria_width}} | "
        for wallet_name in headers:
            value = format_criteria_value(crit, wallets[wallet_name][crit])
            color = Fore.WHITE
            formatted_value = f"{value:<{column_widths[wallet_name]}}"
            row += f"{color}{formatted_value}{Style.RESET_ALL} | "
        table_lines.append(row.rstrip(" | "))
    
    return "\n".join(table_lines)