import os
import sys
import platform
if platform.system() == "Windows":
    import msvcrt
else:
    import curses

def get_terminal_height():
    """Get the current terminal height in lines."""
    try:
        return os.get_terminal_size().lines
    except OSError:
        return 24  # Default fallback

def menu_selection(options, table_str="", prompt=None, info_message=None, middle_content=""):
    """Handle menu navigation with arrow marker, limited table output, and ESC to back out."""
    terminal_height = get_terminal_height()
    menu_space = len(options) + (2 if prompt else 1) + (2 if info_message else 0)
    middle_lines = len(middle_content.split('\n')) if middle_content else 0
    max_table_lines = max(0, terminal_height - menu_space - middle_lines - 5)
    
    table_lines = table_str.split('\n')
    visible_table_lines = table_lines[:max_table_lines]
    visible_table_str = '\n'.join(visible_table_lines)

    if platform.system() == "Windows":
        index = 0
        input_value = ""
        input_active = bool(prompt)
        
        while True:
            os.system('cls' if platform.system() == 'Windows' else 'clear')  # Clear only if necessary
            for i, option in enumerate(options):
                prefix = "-->" if i == index and not input_active else "   "
                print(f"{prefix} {option}")
            print("\n")
            if input_active and prompt:
                print(prompt)
                print(input_value)
            elif info_message:
                print(info_message)
            if middle_content:
                print("\n" + middle_content)
            print("\n" + visible_table_str)
            sys.stdout.flush()

            key = ord(msvcrt.getch())
            if key == 27:  # ESC key
                return None
            elif key == 13:  # Enter
                if input_active:
                    return input_value or ""
                elif info_message:
                    return None
                else:
                    return options[index]
            elif key in (80, 72) and not input_active:  # Down (80) or Up (72) arrow
                index = (index + (1 if key == 80 else -1)) % len(options)
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
                if middle_content:
                    stdscr.addstr(menu_end + 1, 0, middle_content)
                stdscr.addstr(menu_end + (2 if input_active else 1) + middle_lines, 0, "\n" + visible_table_str)
                if input_active:
                    stdscr.move(menu_end + 1, len(input_value))
                else:
                    stdscr.move(current_row, 0)
                stdscr.refresh()
                
                key = stdscr.getch()
                if key == 27:  # ESC key
                    return None
                elif key == curses.KEY_UP and not input_active:
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

def print_filters(filters):
    """Display applied filters above the table."""
    if not filters:
        return ""
    filter_str = "Filters: " + ", ".join(format_filter_display(col, val) for col, val in filters.items())
    return f"{filter_str}"

def format_filter_display(column, value):
    """Format filter values for display."""
    percent_cols = ["Bundle", "Dev%"]
    if column in ["Date", "Name", "FundSource"]:
        return f"{column} ({value})"
    elif column == "Links":
        return f"{column} ({value})"
    elif column in ["FundTime", "Bundle", "DevBal"]:
        max_val = value["max"]
        if column == "FundTime":
            return f"{column} (<= {max_val:.0f}h)" if max_val != 99 else column
        elif column == "Bundle":
            return f"{column} (<= {max_val*100:.2f}%)" if max_val != float('inf') else column
        elif column == "DevBal":
            return f"{column} (<= {max_val:.2f} Sol)" if max_val != float('inf') else column
    else:
        min_val, max_val = value
        if column in percent_cols:
            min_display = f"{min_val*100:.1f}%" if min_val != float('-inf') else ""
            max_display = f"{max_val*100:.1f}%" if max_val != float('inf') else ""
        else:
            min_display = f"{min_val}" if min_val != float('-inf') else ""
            max_display = f"{max_val}" if max_val != float('inf') else ""
        
        if min_display == "" and max_display == "":
            return column
        elif min_display == "":
            return f"{column} (<= {max_display})"
        elif max_display == "":
            return f"{column} (>= {min_display})"
        else:
            return f"{column} ({min_display} - {max_display})"