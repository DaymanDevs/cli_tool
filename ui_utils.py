import platform
import os
if platform.system() == "Windows":
    import msvcrt
    from msvcrt import getch
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

def menu_selection(options, table_str, middle_content="", prompt="Select an option: ", info_message=None):
    if platform.system() == "Windows":
        selected = 0
        while True:
            os.system('cls')
            print(prompt)
            for i, option in enumerate(options):
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
                if next_key == b'H' and selected > 0:  # Up arrow
                    selected -= 1
                elif next_key == b'P' and selected < len(options) - 1:  # Down arrow
                    selected += 1
            elif key == b'\r':  # Enter key
                return options[selected]
            elif key == b'\x1b':  # ESC key
                return None
    else:
        def curses_menu(stdscr):
            curses.curs_set(0)
            selected = 0
            while True:
                stdscr.clear()
                stdscr.addstr(0, 0, prompt)
                for i, option in enumerate(options):
                    y = i + 1
                    if i == selected:
                        stdscr.addstr(y, 0, f"> {option}", curses.A_REVERSE)
                    else:
                        stdscr.addstr(y, 0, f"  {option}")
                if info_message:
                    stdscr.addstr(len(options) + 2, 0, info_message, curses.color_pair(1))
                if table_str:
                    stdscr.addstr(len(options) + (3 if info_message else 2), 0, table_str)
                if middle_content:
                    start_y = len(options) + (3 if info_message else 2) + table_str.count('\n') + 1
                    stdscr.addstr(start_y, 0, middle_content)
                stdscr.refresh()
                
                key = stdscr.getch()
                if key == curses.KEY_UP and selected > 0:
                    selected -= 1
                elif key == curses.KEY_DOWN and selected < len(options) - 1:
                    selected += 1
                elif key == ord('\n'):
                    return options[selected]
                elif key == 27:  # ESC
                    return None
        
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        return curses.wrapper(curses_menu)

def get_terminal_height():
    if platform.system() == "Windows":
        return int(os.get_terminal_size().lines)
    else:
        return int(os.popen('tput lines').read())