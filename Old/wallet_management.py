import curses
from settings_manager import settings_manager

def manage_wallets(stdscr):
    """Main menu for managing wallets."""
    menu = ["Edit Wallets", "Manage Filters", "Back"]
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
            if current_row == 0:
                edit_wallets(stdscr)
            elif current_row == 1:
                manage_filters(stdscr)
            elif current_row == 2:
                break

def edit_wallets(stdscr):
    """Edit existing wallet profiles."""
    profiles = settings_manager.list_profiles()
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Edit Wallets")
        for idx, profile in enumerate(profiles):
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(idx + 2, 0, profile)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 2, 0, profile)
        if current_row == len(profiles):
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(len(profiles) + 2, 0, "Add New Wallet")
            stdscr.attroff(curses.A_REVERSE)
        else:
            stdscr.addstr(len(profiles) + 2, 0, "Add New Wallet")
        if current_row == len(profiles) + 1:
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(len(profiles) + 3, 0, "Back")
            stdscr.attroff(curses.A_REVERSE)
        else:
            stdscr.addstr(len(profiles) + 3, 0, "Back")

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(profiles) + 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row == len(profiles):
                add_wallet(stdscr)
            elif current_row == len(profiles) + 1:
                break
            else:
                manage_wallet_profile(stdscr, profiles[current_row])

def manage_filters(stdscr):
    """Manage filters for wallets."""
    filters = settings_manager.get_options()
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Manage Filters")
        for idx, filter_name in enumerate(filters):
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(idx + 2, 0, filter_name)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 2, 0, filter_name)
        if current_row == len(filters):
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(len(filters) + 2, 0, "Add New Filter")
            stdscr.attroff(curses.A_REVERSE)
        else:
            stdscr.addstr(len(filters) + 2, 0, "Add New Filter")
        if current_row == len(filters) + 1:
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(len(filters) + 3, 0, "Back")
            stdscr.attroff(curses.A_REVERSE)
        else:
            stdscr.addstr(len(filters) + 3, 0, "Back")

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(filters) + 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row == len(filters):
                add_filter(stdscr)
            elif current_row == len(filters) + 1:
                break
            else:
                remove_filter(stdscr, filters[current_row])

def add_wallet(stdscr):
    """Add a new wallet."""
    stdscr.clear()
    stdscr.addstr(0, 0, "Enter new wallet name: ")
    curses.echo()
    wallet_name = stdscr.getstr(1, 0).decode("utf-8")
    curses.noecho()

    if wallet_name in settings_manager.list_profiles():
        stdscr.addstr(2, 0, "Wallet already exists. Press any key to return.")
        stdscr.refresh()
        stdscr.getch()
        return

    settings_manager.update_settings(wallet_name, {})
    stdscr.addstr(2, 0, f"Added wallet: {wallet_name}")
    stdscr.addstr(4, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def add_filter(stdscr):
    """Add a new filter to all wallets."""
    stdscr.clear()
    stdscr.addstr(0, 0, "Enter new filter name: ")
    curses.echo()
    filter_name = stdscr.getstr(1, 0).decode("utf-8")
    curses.noecho()

    settings_manager.add_setting_option(filter_name)
    stdscr.addstr(2, 0, f"Added filter: {filter_name}")
    stdscr.addstr(4, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()

def remove_filter(stdscr, filter_name):
    """Remove a filter from all wallets."""
    stdscr.clear()
    stdscr.addstr(0, 0, f"Are you sure you want to delete the filter '{filter_name}'? (y/n): ")
    curses.echo()
    confirm = stdscr.getstr(1, 0).decode("utf-8").lower()
    curses.noecho()

    if confirm == 'y':
        settings_manager.remove_setting_option(filter_name)
        stdscr.addstr(2, 0, f"Filter '{filter_name}' removed.")
    else:
        stdscr.addstr(2, 0, "Deletion canceled.")

    stdscr.addstr(4, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()
