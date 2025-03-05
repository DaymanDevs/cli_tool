import curses
from settings_manager import SettingsManager
from sl_tp_manager import SLTPManager
from combine_data import load_and_combine_csv
from query_builder import filter_data, display_results

# Initialize global variables
DATA_DIRECTORY = "data"
all_data = {}
settings_manager = SettingsManager()
sltp_manager = SLTPManager()

def main_menu(stdscr):
    """Main menu for the interactive CLI."""
    menu = [
        "Manage Wallets",
        "Manage SL/TP Strategies",
        "Manage Filters",
        "Query Data",
        "Import Data",
        "Exit",
    ]
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Main Menu")
        for idx, item in enumerate(menu):
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(idx + 2, 0, item)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 2, 0, item)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row == 0:
                manage_wallets(stdscr)
            elif current_row == 1:
                manage_sl_tp_strategies(stdscr)
            elif current_row == 2:
                manage_filters(stdscr)
            elif current_row == 3:
                query_data(stdscr)
            elif current_row == 4:
                import_data(stdscr)
            elif current_row == 5:
                break

def manage_wallets(stdscr):
    """Menu for managing wallets."""
    wallets = settings_manager.list_profiles()
    menu = wallets + ["Add Wallet", "Back"]
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Manage Wallets")
        for idx, item in enumerate(menu):
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(idx + 2, 0, item)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 2, 0, item)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row < len(wallets):  # Edit Wallet
                edit_wallet(stdscr, wallets[current_row])
            elif current_row == len(wallets):  # Add Wallet
                add_wallet(stdscr)
            elif current_row == len(wallets) + 1:  # Back
                break

def add_wallet(stdscr):
    """Add a new wallet."""
    stdscr.clear()
    stdscr.addstr(0, 0, "Enter new wallet name: ")
    curses.echo()
    wallet_name = stdscr.getstr(1, 0).decode("utf-8").strip()
    curses.noecho()

    if not wallet_name:
        stdscr.addstr(3, 0, "Error: Wallet name cannot be blank. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    if wallet_name in settings_manager.list_profiles():
        stdscr.addstr(3, 0, "Error: Wallet name already exists. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    settings_manager.add_profile(wallet_name)
    stdscr.addstr(3, 0, f"Wallet '{wallet_name}' added successfully.")
    stdscr.addstr(5, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def edit_wallet(stdscr, wallet_name):
    """Edit an existing wallet."""
    wallet_settings = settings_manager.get_settings(wallet_name)
    menu = list(wallet_settings.keys()) + ["Rename Wallet", "Delete Wallet", "Back"]
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Editing Wallet: {wallet_name}")
        for idx, item in enumerate(menu):
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(idx + 2, 0, item)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 2, 0, item)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row < len(wallet_settings):  # Edit Filter
                edit_wallet_setting(stdscr, wallet_name, menu[current_row])
            elif current_row == len(wallet_settings):  # Rename Wallet
                rename_wallet(stdscr, wallet_name)
                break
            elif current_row == len(wallet_settings) + 1:  # Delete Wallet
                delete_wallet(stdscr, wallet_name)
                break
            elif current_row == len(wallet_settings) + 2:  # Back
                break

def edit_wallet_setting(stdscr, wallet_name, setting_name):
    """Edit a specific setting for a wallet."""
    stdscr.clear()
    stdscr.addstr(0, 0, f"Editing '{setting_name}' for wallet '{wallet_name}'")
    stdscr.addstr(1, 0, f"Current value: {settings_manager.get_settings(wallet_name).get(setting_name, 'N/A')}")
    stdscr.addstr(3, 0, "Enter new value: ")
    curses.echo()
    new_value = stdscr.getstr(4, 0).decode("utf-8").strip()
    curses.noecho()

    if not new_value:
        stdscr.addstr(6, 0, "Error: Value cannot be blank. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    settings_manager.update_settings(wallet_name, {setting_name: new_value})
    stdscr.addstr(6, 0, f"Updated '{setting_name}' to '{new_value}' for wallet '{wallet_name}'.")
    stdscr.addstr(8, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def rename_wallet(stdscr, wallet_name):
    """Rename an existing wallet."""
    stdscr.clear()
    stdscr.addstr(0, 0, f"Renaming Wallet: {wallet_name}")
    stdscr.addstr(1, 0, "Enter new wallet name: ")
    curses.echo()
    new_name = stdscr.getstr(2, 0).decode("utf-8").strip()
    curses.noecho()

    if not new_name:
        stdscr.addstr(4, 0, "Error: Wallet name cannot be blank. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    if new_name in settings_manager.list_profiles():
        stdscr.addstr(4, 0, "Error: Wallet name already exists. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    settings_manager.rename_profile(wallet_name, new_name)
    stdscr.addstr(4, 0, f"Wallet renamed to '{new_name}'.")
    stdscr.addstr(6, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def delete_wallet(stdscr, wallet_name):
    """Delete an existing wallet."""
    stdscr.clear()
    stdscr.addstr(0, 0, f"Are you sure you want to delete wallet '{wallet_name}'? (y/n): ")
    key = stdscr.getch()

    if key in [ord('y'), ord('Y')]:
        settings_manager.delete_profile(wallet_name)
        stdscr.addstr(2, 0, f"Wallet '{wallet_name}' deleted successfully.")
    else:
        stdscr.addstr(2, 0, "Action canceled.")
    stdscr.addstr(4, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def manage_sl_tp_strategies(stdscr):
    """Menu for managing SL/TP strategies."""
    strategies = sltp_manager.list_strategies()
    menu = strategies + ["Add Strategy", "Back"]
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Manage SL/TP Strategies")
        for idx, item in enumerate(menu):
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(idx + 2, 0, item)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 2, 0, item)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row < len(strategies):  # Edit Strategy
                edit_strategy(stdscr, strategies[current_row])
            elif current_row == len(strategies):  # Add Strategy
                add_strategy(stdscr)
            elif current_row == len(strategies) + 1:  # Back
                break

def add_strategy(stdscr):
    """Add a new SL/TP strategy."""
    stdscr.clear()
    stdscr.addstr(0, 0, "Enter new strategy name: ")
    curses.echo()
    strategy_name = stdscr.getstr(1, 0).decode("utf-8").strip()
    curses.noecho()

    if not strategy_name:
        stdscr.addstr(3, 0, "Error: Strategy name cannot be blank. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    if strategy_name in sltp_manager.list_strategies():
        stdscr.addstr(3, 0, "Error: Strategy name already exists. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    sltp_manager.add_strategy(strategy_name)
    stdscr.addstr(3, 0, f"Strategy '{strategy_name}' added successfully.")
    stdscr.addstr(5, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def edit_strategy(stdscr, strategy_name):
    """Edit an SL/TP strategy."""
    steps = sltp_manager.get_strategy_steps(strategy_name)
    menu = [f"{idx + 1}: {step['type']} | P/L: {step['pl']} | Sell: {step['sell']}" for idx, step in enumerate(steps)]
    menu += ["Add Step", "Delete Strategy", "Back"]
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Editing Strategy: {strategy_name}")
        stdscr.addstr(1, 0, "Existing Steps:")
        for idx, item in enumerate(menu):
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(idx + 3, 0, item)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 3, 0, item)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row < len(steps):  # Edit Step
                edit_step(stdscr, strategy_name, current_row)
            elif current_row == len(steps):  # Add Step
                add_step_to_strategy(stdscr, strategy_name)
            elif current_row == len(steps) + 1:  # Delete Strategy
                delete_strategy(stdscr, strategy_name)
                break
            elif current_row == len(steps) + 2:  # Back
                break

def add_step_to_strategy(stdscr, strategy_name):
    """Add a step to an SL/TP strategy."""
    stdscr.clear()
    stdscr.addstr(0, 0, f"Adding Step to Strategy: {strategy_name}")
    stdscr.addstr(1, 0, "Step Type (Stop Loss/Take Profit): ")
    curses.echo()
    step_type = stdscr.getstr(2, 0).decode("utf-8").strip().lower()
    curses.noecho()

    if step_type not in ["stop loss", "take profit"]:
        stdscr.addstr(4, 0, "Error: Step Type must be 'Stop Loss' or 'Take Profit'. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    stdscr.addstr(5, 0, "Enter P/L Position (%): ")
    curses.echo()
    pl = stdscr.getstr(6, 0).decode("utf-8").strip()
    curses.noecho()

    stdscr.addstr(7, 0, "Enter Tokens to Sell (%): ")
    curses.echo()
    sell = stdscr.getstr(8, 0).decode("utf-8").strip()
    curses.noecho()

    try:
        pl = float(pl)
        sell = float(sell)
        sltp_manager.add_step(strategy_name, step_type, pl, sell)
        stdscr.addstr(10, 0, "Step added successfully. Press any key to return.")
    except ValueError:
        stdscr.addstr(10, 0, "Error: P/L and Sell must be numeric. Press any key to return.")

    stdscr.refresh()
    stdscr.getch()

def edit_step(stdscr, strategy_name, step_index):
    """Edit an existing step in an SL/TP strategy."""
    step = sltp_manager.get_strategy_steps(strategy_name)[step_index]
    stdscr.clear()
    stdscr.addstr(0, 0, f"Editing Step {step_index + 1} in Strategy: {strategy_name}")
    stdscr.addstr(1, 0, f"Current Type: {step['type']}, P/L: {step['pl']}%, Sell: {step['sell']}%")

    stdscr.addstr(3, 0, "Enter new P/L Position (%): ")
    curses.echo()
    new_pl = stdscr.getstr(4, 0).decode("utf-8").strip()
    curses.noecho()

    stdscr.addstr(5, 0, "Enter new Tokens to Sell (%): ")
    curses.echo()
    new_sell = stdscr.getstr(6, 0).decode("utf-8").strip()
    curses.noecho()

    try:
        new_pl = float(new_pl)
        new_sell = float(new_sell)
        sltp_manager.update_step(strategy_name, step_index, new_pl, new_sell)
        stdscr.addstr(8, 0, "Step updated successfully. Press any key to return.")
    except ValueError:
        stdscr.addstr(8, 0, "Error: P/L and Sell must be numeric. Press any key to return.")

    stdscr.refresh()
    stdscr.getch()

def delete_strategy(stdscr, strategy_name):
    """Delete an SL/TP strategy."""
    stdscr.clear()
    stdscr.addstr(0, 0, f"Are you sure you want to delete strategy '{strategy_name}'? (y/n): ")
    key = stdscr.getch()

    if key in [ord('y'), ord('Y')]:
        sltp_manager.delete_strategy(strategy_name)
        stdscr.addstr(2, 0, f"Strategy '{strategy_name}' deleted successfully.")
    else:
        stdscr.addstr(2, 0, "Action canceled.")
    stdscr.addstr(4, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def manage_filters(stdscr):
    """Menu for managing filters."""
    filters = settings_manager.list_filters()
    menu = filters + ["Add Filter", "Back"]
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Manage Filters")
        for idx, item in enumerate(menu):
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(idx + 2, 0, item)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 2, 0, item)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row < len(filters):  # Edit Filter
                edit_filter(stdscr, filters[current_row])
            elif current_row == len(filters):  # Add Filter
                add_filter(stdscr)
            elif current_row == len(filters) + 1:  # Back
                break

def add_filter(stdscr):
    """Add a new filter."""
    stdscr.clear()
    stdscr.addstr(0, 0, "Enter new filter name: ")
    curses.echo()
    filter_name = stdscr.getstr(1, 0).decode("utf-8").strip()
    curses.noecho()

    if not filter_name:
        stdscr.addstr(3, 0, "Error: Filter name cannot be blank. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    if filter_name in settings_manager.list_filters():
        stdscr.addstr(3, 0, "Error: Filter already exists. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    settings_manager.add_filter(filter_name)
    stdscr.addstr(3, 0, f"Filter '{filter_name}' added successfully.")
    stdscr.addstr(5, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def edit_filter(stdscr, filter_name):
    """Edit an existing filter."""
    stdscr.clear()
    stdscr.addstr(0, 0, f"Editing Filter: {filter_name}")
    stdscr.addstr(1, 0, f"Are you sure you want to delete this filter? (y/n): ")
    key = stdscr.getch()

    if key in [ord('y'), ord('Y')]:
        settings_manager.delete_filter(filter_name)
        stdscr.addstr(3, 0, f"Filter '{filter_name}' deleted successfully.")
    else:
        stdscr.addstr(3, 0, "Action canceled.")
    stdscr.addstr(5, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def query_data(stdscr):
    """Menu for querying data."""
    profiles = settings_manager.list_profiles()
    menu = profiles + ["Manual Query", "Back"]
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Query Data")
        for idx, item in enumerate(menu):
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(idx + 2, 0, item)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 2, 0, item)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row < len(profiles):  # Query by Profile
                execute_query(stdscr, profiles[current_row])
            elif current_row == len(profiles):  # Manual Query
                manual_query(stdscr)
            elif current_row == len(profiles) + 1:  # Back
                break

def execute_query(stdscr, profile_name):
    """Execute a query using a specific wallet profile."""
    stdscr.clear()
    stdscr.addstr(0, 0, f"Querying data using profile: {profile_name}")
    profile_settings = settings_manager.get_settings(profile_name)

    # Filter data based on profile settings
    results = filter_data(all_data, profile_settings)

    # Display results
    display_results(stdscr, results)

    stdscr.addstr(len(results) + 2, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def manual_query(stdscr):
    """Manually input query parameters."""
    stdscr.clear()
    stdscr.addstr(0, 0, "Manual Query")
    stdscr.addstr(1, 0, "Enter your query parameters (leave blank to skip):")

    query_params = {}
    for filter_name in settings_manager.list_filters():
        stdscr.addstr(3, 0, f"{filter_name}: ")
        curses.echo()
        value = stdscr.getstr(4 + list(query_params.keys()).index(filter_name), 0).decode("utf-8").strip()
        curses.noecho()
        if value:
            query_params[filter_name] = value

    # Filter data based on manual query
    results = filter_data(all_data, query_params)

    # Display results
    display_results(stdscr, results)

    stdscr.addstr(len(results) + 2, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def import_data(stdscr):
    """Import and combine data from CSV files."""
    global all_data
    stdscr.clear()
    stdscr.addstr(0, 0, "Importing data...")
    stdscr.refresh()

    # Load and combine data from CSV files
    try:
        all_data = load_and_combine_csv(DATA_DIRECTORY)
        stdscr.addstr(2, 0, "Data imported successfully.")
    except Exception as e:
        stdscr.addstr(2, 0, f"Error importing data: {e}")

    stdscr.addstr(4, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main_menu)