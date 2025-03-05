import pandas as pd
import os
import sys
import platform
from datetime import datetime

if platform.system() == "Windows":
    import msvcrt
else:
    import curses

def load_and_combine_csv(directory):
    """Load all CSV files from a directory and combine them by base name."""
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' not found.")
        return {}
    
    csv_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.csv')]
    tables = {}
    
    for file in csv_files:
        df = pd.read_csv(file)
        numeric_cols = ["Mcap", "Liq", "AG", "Dev Bal", "F", "KYC", "Unq", "SM"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        percent_cols = ["Bundle", "Dev%"]
        for col in percent_cols:
            if col in df.columns:
                df[col] = df[col].replace({'%': ''}, regex=True).astype(float) / 100
        name = os.path.basename(file).split('-')[0].lower()
        tables.setdefault(name, []).append(df)
    
    combined_tables = {}
    for name, dfs in tables.items():
        combined_df = pd.concat(dfs, ignore_index=True)
        if name.endswith("10") and 'Multiples' in combined_df.columns:
            combined_df['Multiples'] = combined_df['Multiples'].replace({'x': ''}, regex=True).astype(float)
            combined_df = combined_df.sort_values('Multiples', ascending=False).drop_duplicates('Contract', keep='first')
        combined_tables[name] = combined_df
    
    return combined_tables

def get_terminal_height():
    """Get the current terminal height in lines."""
    try:
        return os.get_terminal_size().lines
    except OSError:
        return 24  # Default fallback

def menu_selection(options, table_str="", prompt=None, info_message=None):
    """Handle menu navigation with arrow marker, limited table output."""
    terminal_height = get_terminal_height()
    menu_space = len(options) + (2 if prompt else 1) + (2 if info_message else 0)
    max_table_lines = max(0, terminal_height - menu_space - 5)
    
    table_lines = table_str.split('\n')
    visible_table_lines = table_lines[:max_table_lines]
    visible_table_str = '\n'.join(visible_table_lines)

    if platform.system() == "Windows":
        index = 0
        input_value = ""
        input_active = bool(prompt)
        
        while True:
            os.system('cls' if platform.system() == 'Windows' else 'clear')
            for i, option in enumerate(options):
                prefix = "-->" if i == index else "   "
                print(f"{prefix} {option}")
            print("\n")
            if input_active and prompt:
                print(prompt)
                print(input_value)
            elif info_message:
                print(info_message)
            print("\n" + visible_table_str)
            sys.stdout.flush()

            key = ord(msvcrt.getch())
            if key == 13:  # Enter
                if input_active:
                    return input_value or ""
                elif info_message:
                    return None
                else:
                    return options[index]
            elif key == 80 and not input_active:  # Down arrow
                index = (index + 1) % len(options)
            elif key == 72 and not input_active:  # Up arrow
                index = (index - 1) % len(options)
            elif input_active:
                if key == 8:  # Backspace
                    input_value = input_value[:-1] if input_value else ""
                elif 32 <= key <= 126:  # Printable characters
                    input_value += chr(key)
    else:
        def curses_menu(stdscr):
            curses.curs_set(1 if prompt else 0)
            current_row = 0
            input_value = ""
            input_active = bool(prompt)
            
            while True:
                stdscr.clear()
                for i, option in enumerate(options):
                    prefix = "-->" if i == current_row and not input_active else "   "
                    stdscr.addstr(i, 0, f"{prefix} {option}")
                menu_end = len(options)
                if input_active and prompt:
                    stdscr.addstr(menu_end, 0, prompt)
                    stdscr.addstr(menu_end + 1, 0, input_value)
                elif info_message:
                    stdscr.addstr(menu_end, 0, info_message)
                stdscr.addstr(menu_end + (2 if input_active else 1), 0, "\n" + visible_table_str)
                if input_active:
                    stdscr.move(menu_end + 1, len(input_value))
                else:
                    stdscr.move(current_row, 0)
                stdscr.refresh()
                
                key = stdscr.getch()
                if key == curses.KEY_UP and not input_active:
                    current_row = (current_row - 1) % len(options)
                elif key == curses.KEY_DOWN and not input_active:
                    current_row = (current_row + 1) % len(options)
                elif key == 10:  # Enter
                    if input_active:
                        return input_value or ""
                    elif info_message:
                        return None
                    else:
                        return options[current_row]
                elif input_active:
                    if key == curses.KEY_BACKSPACE or key == 127:  # Backspace
                        input_value = input_value[:-1] if input_value else ""
                    elif 32 <= key <= 126:  # Printable characters
                        input_value += chr(key)
        return curses.wrapper(curses_menu)

def format_filter_display(column, value):
    """Format filter values for display."""
    if column in ["Date", "Name", "FundSource"]:
        return f"{column} ({value})"
    elif column == "Links":
        return f"{column} ({value})"
    else:
        min_val, max_val = value
        if min_val == float('-inf') and max_val == float('inf'):
            return column
        elif min_val == float('-inf'):
            return f"{column} (<= {max_val})"
        elif max_val == float('inf'):
            return f"{column} (>= {min_val})"
        else:
            return f"{column} ({min_val} - {max_val})"

def print_filters(filters):
    """Display applied filters above the table."""
    if not filters:
        return ""
    filter_str = "Filters: " + ", ".join(format_filter_display(col, val) for col, val in filters.items())
    return f"{filter_str}"

def filter_table(df, display_name):
    """Filter the DataFrame with a menu showing current settings."""
    filters = {}
    base_options = [
        "Date", "Name", "Mcap", "Liq", "AG", "Bundle", "FundTime", 
        "FundSource", "Dev%", "DevBal", "Links", "F", "KYC", "Unq", "SM", "HighestMcap", "Multiples", "Done", "Back"
    ]
    
    filtered_df = df.copy()
    filtered_df = filtered_df.rename(columns={"Funding Time": "FundTime", "Funding Source": "FundSource", "Dev Bal": "DevBal", "Has Links": "Links"})
    
    while True:
        filter_options = [format_filter_display(col, filters[col]) if col in filters else col 
                          for col in base_options if col in filtered_df.columns or col in ["Done", "Back"]]
        table_str = f"{print_filters(filters)}\n=== Data for {display_name.upper()} ===\n" + \
                    filtered_df.to_string(index=False, justify='left', formatters={
                        'Contract': lambda x: x[:8] + "...",
                        'Bundle': lambda x: f'{x*100:.2f}%' if pd.notnull(x) else 'NaN',
                        'Dev%': lambda x: f'{x*100:.2f}%' if pd.notnull(x) else 'NaN',
                        'Multiples': lambda x: f'{x:.1f}x' if pd.notnull(x) else 'NaN'
                    })
        choice = menu_selection(filter_options, table_str)
        if choice == "Done":
            break
        elif choice == "Back":
            return df, {}  # Return original df and empty filters on Back
        
        column = next(col for col in base_options if choice.startswith(col))
        
        if column == "Date":
            date_input = menu_selection(filter_options, table_str, "Enter date (dd/mm/yy) or leave blank to skip: ")
            if date_input:
                try:
                    filters["Date"] = datetime.strptime(date_input, "%d/%m/%y").strftime("%d/%m/%Y")
                except ValueError:
                    menu_selection(filter_options, table_str, info_message="Invalid date format. Press Enter to continue...")
            elif "Date" in filters:
                del filters["Date"]
        
        elif column == "Name":
            name_input = menu_selection(filter_options, table_str, "Enter name (case insensitive) or leave blank to skip: ")
            if name_input:
                filters["Name"] = name_input.lower()
            elif "Name" in filters:
                del filters["Name"]
        
        elif column == "FundSource" and "FundSource" in filtered_df.columns:
            source_input = menu_selection(filter_options, table_str, "Enter funding source (case insensitive) or leave blank to skip: ")
            if source_input:
                filters["FundSource"] = source_input.lower()
            elif "FundSource" in filters:
                del filters["FundSource"]
        
        elif column == "Links" and "Links" in filtered_df.columns:
            yes_no_options = ["Yes", "No", "Skip", "Back"]
            yes_no = menu_selection(yes_no_options, table_str)
            if yes_no == "Back":
                continue
            elif yes_no != "Skip":
                filters["Links"] = yes_no
            elif "Links" in filters:
                del filters["Links"]
        
        else:
            min_val = menu_selection(filter_options, table_str, f"Enter minimum {column} (or leave blank): ")
            max_val = menu_selection(filter_options, table_str, f"Enter maximum {column} (or leave blank): ")
            if min_val or max_val:
                try:
                    filters[column] = [
                        float(min_val) if min_val else float('-inf'),
                        float(max_val) if max_val else float('inf')
                    ]
                except ValueError:
                    menu_selection(filter_options, table_str, info_message="Invalid number format. Press Enter to continue...")
            elif column in filters:
                del filters[column]
    
    # Apply filters
    for column, value in filters.items():
        if column in ["Date", "Name", "FundSource"]:
            filtered_df = filtered_df[filtered_df[column].str.lower() == value]
        elif column == "Links":
            filtered_df = filtered_df[filtered_df[column] == value]
        else:
            min_val, max_val = value
            filtered_df = filtered_df[(filtered_df[column] >= min_val) & (filtered_df[column] <= max_val)].dropna(subset=[column])
    
    return filtered_df, filters

def display_table(table_name, combined_tables, display_name):
    """Display a table and handle actions with arrow-key menu above."""
    if table_name not in combined_tables:
        print(f"Table '{table_name}' not found.")
        return
    
    # Determine if it's a top table using display_name
    is_top_table = "top" in display_name.lower()
    base_name = display_name.lower().replace(" top", "")
    df = combined_tables[base_name].copy() if not is_top_table else combined_tables[base_name].copy()
    df = df.rename(columns={"Funding Time": "FundTime", "Funding Source": "FundSource", "Dev Bal": "DevBal", "Has Links": "Links"})
    
    if is_top_table:
        top_key = f"{base_name}10"
        top_df = combined_tables.get(top_key, pd.DataFrame())
        if not top_df.empty:
            # Merge top_df with full df on Contract
            df = pd.merge(df, top_df[['Contract', 'HighestMcap', 'Multiples']], on='Contract', how='inner')
    
    # Sort all tables by Date (descending), and TOP tables by Date and Multiples
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
        if is_top_table and 'Multiples' in df.columns:
            df = df.sort_values(['Date', 'Multiples'], ascending=[False, False])
        else:
            df = df.sort_values('Date', ascending=False)
    
    if 'Selection #' not in df.columns:
        df.insert(0, "Selection #", range(1, len(df) + 1))
    original_df = df.copy()
    filters = {}
    
    if platform.system() == "Windows":
        os.system('cls' if platform.system() == 'Windows' else 'clear')
    
    while True:
        table_str = f"{print_filters(filters)}\n=== Data for {display_name.upper()} ===\n" + \
                    df.to_string(index=False, justify='left', formatters={
                        'Contract': lambda x: x[:8] + "...",
                        'Bundle': lambda x: f'{x*100:.2f}%' if pd.notnull(x) else 'NaN',
                        'Dev%': lambda x: f'{x*100:.2f}%' if pd.notnull(x) else 'NaN',
                        'Multiples': lambda x: f'{x:.1f}x' if pd.notnull(x) else 'NaN'
                    })
        options = ["Return to menu", "Search in PF", "Filter Table", "Clear Filters", "Back"]
        choice = menu_selection(options, table_str)
        
        if choice == "Search in PF":
            selected = menu_selection(options, table_str, "Enter selection numbers (comma-separated, or 'all'): ")
            if selected.lower() == "all":
                contracts = df["Contract"].tolist()
                search_contracts_in_pf(contracts, combined_tables)
            else:
                selected_nums = [int(i.strip()) for i in selected.split(',') if i.strip().isdigit()]
                if selected_nums and all(num in df["Selection #"].values for num in selected_nums):
                    filtered_df = df.loc[df["Selection #"].isin(selected_nums)]
                    contracts = filtered_df["Contract"].tolist()
                    search_contracts_in_pf(contracts, combined_tables)
                else:
                    menu_selection(options, table_str, info_message="Invalid selection. Press Enter to continue...")
            if platform.system() == "Windows":
                os.system('cls' if platform.system() == 'Windows' else 'clear')
        
        elif choice == "Filter Table":
            df, filters = filter_table(df, display_name)
            if platform.system() == "Windows":
                os.system('cls' if platform.system() == 'Windows' else 'clear')
        
        elif choice == "Clear Filters":
            df = original_df.copy()
            filters = {}
            if platform.system() == "Windows":
                os.system('cls' if platform.system() == 'Windows' else 'clear')
        
        elif choice == "Back" or choice == "Return to menu":
            break

def search_contracts_in_pf(contracts, combined_tables):
    """Search for contracts in the PF table with iteration per contract as first column."""
    if "pf" not in combined_tables:
        print("PF table not found.")
        return
    
    df = combined_tables["pf"][combined_tables["pf"]["Contract"].isin(contracts)]
    if df.empty:
        print("\n=== Search Results in PF ===")
        print("No matching results found.")
    else:
        df = df.sort_values(["Contract", "Date"])
        df.insert(0, "Iteration", df.groupby("Contract").cumcount() + 1)
        df = df.reset_index(drop=True)
        df = df.rename(columns={"Funding Time": "FundTime", "Funding Source": "FundSource", "Dev Bal": "DevBal", "Has Links": "Links"})
        print("\n=== Search Results in PF ===")
        print(df.to_string(index=False, justify='left', formatters={
            'Contract': lambda x: x[:8] + "...",
            'Bundle': lambda x: f'{x*100:.2f}%' if pd.notnull(x) else 'NaN',
            'Dev%': lambda x: f'{x*100:.2f}%' if pd.notnull(x) else 'NaN'
        }))
    print("\nPress any key to continue...")
    if platform.system() == "Windows":
        msvcrt.getch()
    else:
        curses.wrapper(lambda stdscr: stdscr.getch())

def cross_reference_contract(combined_tables):
    """Cross-reference a contract across two tables."""
    contract = input("Enter contract address: ").strip()
    target_table = input("Enter target table (default is 'PF'): ").strip().lower() or "pf"
    
    if target_table not in combined_tables or "pf" not in combined_tables:
        print(f"One or both tables ('PF', '{target_table.upper()}') not found.")
        return
    
    pf_results = combined_tables["pf"][combined_tables["pf"]['Contract'] == contract]
    target_results = combined_tables[target_table][combined_tables[target_table]['Contract'] == contract]
    
    print(f"\n=== Results for Contract {contract} ===\n")
    print("From PF:")
    pf_results = pf_results.rename(columns={"Funding Time": "FundTime", "Funding Source": "FundSource", "Dev Bal": "DevBal", "Has Links": "Links"})
    print(pf_results.to_string(index=False, justify='left', formatters={'Contract': lambda x: x[:8] + "...", 'Bundle': lambda x: f'{x*100:.2f}%' if pd.notnull(x) else 'NaN', 'Dev%': lambda x: f'{x*100:.2f}%' if pd.notnull(x) else 'NaN'}) if not pf_results.empty else "No matching results.")
    print(f"\nFrom {target_table.upper()}:")
    target_results = target_results.rename(columns={"Funding Time": "FundTime", "Funding Source": "FundSource", "Dev Bal": "DevBal", "Has Links": "Links"})
    print(target_results.to_string(index=False, justify='left', formatters={'Contract': lambda x: x[:8] + "...", 'Bundle': lambda x: f'{x*100:.2f}%' if pd.notnull(x) else 'NaN', 'Dev%': lambda x: f'{x*100:.2f}%' if pd.notnull(x) else 'NaN'}) if not target_results.empty else "No matching results.")
    print("\nPress any key to continue...")
    if platform.system() == "Windows":
        msvcrt.getch()
    else:
        curses.wrapper(lambda stdscr: stdscr.getch())

def main():
    """Main CLI loop with 'Tables' menu."""
    data_directory = 'data'
    combined_tables = load_and_combine_csv(data_directory)
    if not combined_tables:
        return
    
    table_options = ["PF", "Fomo", "Fomo Top", "BB", "BB Top", "GM", "GM Top", "MF", "MF Top", "SM", "Back"]
    main_options = ["Tables", "Cross-reference by contract", "Exit"]
    
    while True:
        choice = menu_selection(main_options)
        
        if choice == "Tables":
            while True:
                table_choice = menu_selection(table_options)
                if table_choice == "Back":
                    break
                internal_key = table_choice.lower().replace(" top", "") if " top" in table_choice.lower() else table_choice.lower()
                display_table(internal_key, combined_tables, table_choice)
        elif choice == "Cross-reference by contract":
            cross_reference_contract(combined_tables)
        elif choice == "Exit":
            print("Goodbye.")
            break

if __name__ == "__main__":
    main()