import platform
import os
if platform.system() == "Windows":
    import msvcrt
else:
    import curses
import colorama
from colorama import Fore, Style

colorama.init()

def print_filters(filters):
    if not filters:
        return "No filters applied."
    filter_strs = []
    for key, value in filters.items():
        if key == "Date":
            min_val, max_val = value
            min_str = min_val if min_val != float('-inf') else "No min"
            max_str = max_val if max_val != float('inf') else "No max"
            filter_strs.append(f"{key}: {min_str} - {max_str}")
        elif key == "Name":
            filter_strs.append(f"{key}: {value}")
        elif key == "Links":
            filter_strs.append(f"{key}: {value}")
        elif key == "Funding":
            filter_strs.append(f"{key}: >= {value['min']}h")
        elif key == "Bundle":
            filter_strs.append(f"{key}: <= {value['max']*100:.2f}%")
        elif key == "DevBal":
            filter_strs.append(f"{key}: <= {value['max']:,}")
        elif key == "X's":
            filter_strs.append(f"{key}: >= {value['min']:.2f}x")
        else:
            min_val, max_val = value
            min_str = f"{min_val:,}" if min_val != float('-inf') else "No min"
            max_str = f"{max_val:,}" if max_val != float('inf') else "No max"
            filter_strs.append(f"{key}: {min_str} - {max_str}")
    return "Filters: " + ", ".join(filter_strs)

def format_filter_display(option, value):
    if option == "Date":
        min_val, max_val = value
        min_str = min_val if min_val != float('-inf') else "No min"
        max_str = max_val if max_val != float('inf') else "No max"
        return f"{option} ({min_str} - {max_str})"
    elif option == "Name":
        return f"{option} ({value})"
    elif option == "Links":
        return f"{option} ({value})"
    elif option == "Funding":
        return f"{option} (>= {value['min']}h)"
    elif option == "Bundle":
        return f"{option} (<= {value['max']*100:.2f}%)"
    elif option == "DevBal":
        return f"{option} (<= {value['max']:,})"
    elif option == "X's":
        return f"{option} (>= {value['min']:.2f}x)"
    else:
        min_val, max_val = value
        min_str = f"{min_val:,}" if min_val != float('-inf') else "No min"
        max_str = f"{max_val:,}" if max_val != float('inf') else "No max"
        return f"{option} ({min_str} - {max_str})"

def menu_selection(options, table_str, middle_content="", prompt="Select an option: ", info_message=None, allow_input=False):
    if platform.system() == "Windows":
        selected = 0
        while True:
            os.system('cls')
            print(prompt)
            visible_options = options[:get_terminal_height() - 5 - (middle_content.count('\n') + 1 if middle_content else 0)]
            for i, option in enumerate(visible_options):
                if i == selected:
                    print(f"> {Fore.CYAN}{option}{Style.RESET_ALL}")
                else:
                    print(f"  {option}")
            if info_message:
                print(f"\n{Fore.YELLOW}{info_message}{Style.RESET_ALL}")
            if table_str:
                print(f"\n{table_str}")
            if middle_content:
                print(middle_content)
            
            key = msvcrt.getch()
            if key == b'\xe0':  # Arrow key prefix
                next_key = msvcrt.getch()
                if next_key == b'H':  # Up arrow
                    selected = (selected - 1) % len(visible_options)
                elif next_key == b'P':  # Down arrow
                    selected = (selected + 1) % len(visible_options)
            elif key == b'\r':  # Enter key
                return visible_options[selected]
            elif key == b'\x1b':  # ESC key
                return None
            elif allow_input and key.isalnum():
                return input(f"{prompt} ").strip()
    else:
        def curses_menu(stdscr):
            curses.curs_set(0)
            selected = 0
            while True:
                stdscr.clear()
                stdscr.addstr(0, 0, prompt)
                visible_options = options[:get_terminal_height() - 5 - (middle_content.count('\n') + 1 if middle_content else 0)]
                for i, option in enumerate(visible_options):
                    y = i + 1
                    if i == selected:
                        stdscr.addstr(y, 0, f"> {option}", curses.A_REVERSE)
                    else:
                        stdscr.addstr(y, 0, f"  {option}")
                if info_message:
                    stdscr.addstr(len(visible_options) + 2, 0, info_message, curses.color_pair(1))
                if table_str:
                    stdscr.addstr(len(visible_options) + (3 if info_message else 2), 0, table_str)
                if middle_content:
                    start_y = len(visible_options) + (3 if info_message else 2) + table_str.count('\n') + 1
                    stdscr.addstr(start_y, 0, middle_content)
                stdscr.refresh()
                
                key = stdscr.getch()
                if key == curses.KEY_UP:
                    selected = (selected - 1) % len(visible_options)
                elif key == curses.KEY_DOWN:
                    selected = (selected + 1) % len(visible_options)
                elif key == ord('\n'):
                    return visible_options[selected]
                elif key == 27:  # ESC
                    return None
                elif allow_input and key >= 32 and key <= 126:
                    stdscr.addstr(0, len(prompt), "")
                    curses.echo()
                    input_str = stdscr.getstr(0, len(prompt), 100).decode('utf-8').strip()
                    curses.noecho()
                    return input_str
        
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        return curses.wrapper(curses_menu)

def get_terminal_height():
    if platform.system() == "Windows":
        return int(os.get_terminal_size().lines)
    else:
        return int(os.popen('tput lines').read())