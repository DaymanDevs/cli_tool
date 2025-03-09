import platform
import os
import time
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
            min_str = min_val.strftime('%d/%m/%y %H:%M') if min_val != float('-inf') else "No min"
            max_str = max_val.strftime('%d/%m/%y %H:%M') if max_val != float('inf') else "No max"
            filter_strs.append(f"{key}: {min_str} - {max_str}")
        elif key in ["Name", "Links", "FreshDeployer", "Desc", "token_name"]:
            filter_strs.append(f"{key}: {value}")
        elif key == "FundingTime":
            filter_strs.append(f"{key}: >= {value['min']}")
        elif key in ["Liq%", "Bundle", "Dev%", "B-Ratio"]:
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
        min_str = min_val.strftime('%d/%m/%y %H:%M') if min_val != float('-inf') else "No min"
        max_str = max_val.strftime('%d/%m/%y %H:%M') if max_val != float('inf') else "No max"
        return f"{option} ({min_str} - {max_str})"
    elif option in ["Name", "Links", "FreshDeployer", "Desc", "token_name"]:
        return f"{option} ({value})"
    elif option == "FundingTime":
        return f"{option} (>= {value['min']})"
    elif option in ["Liq%", "Bundle", "Dev%", "B-Ratio"]:
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
        input_buffer = ""
        os.system('cls')  # Initial clear
        # Draw menu once initially
        print(prompt + (input_buffer if allow_input else ""))
        terminal_height = get_terminal_height()
        reserved_lines = 5 + (middle_content.count('\n') + 1 if middle_content else 0) + (2 if info_message else 0)
        max_options = terminal_height - reserved_lines - (table_str.count('\n') + 1 if table_str else 0)
        visible_options = options[:max(0, min(len(options), max_options))]
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

        while True:
            if msvcrt.kbhit():  # Only redraw on keypress
                char = msvcrt.getch()
                if allow_input:
                    if char == b'\r':  # Enter
                        return input_buffer if input_buffer else visible_options[selected]
                    elif char == b'\x08':  # Backspace
                        input_buffer = input_buffer[:-1]
                    elif char == b'\x1b':  # ESC
                        return None
                    elif char.isalnum() or char in b' ,':
                        input_buffer += char.decode('utf-8')
                else:
                    if char == b'\xe0':  # Arrow key prefix
                        next_key = msvcrt.getch()
                        if next_key == b'H':  # Up arrow
                            selected = max(0, selected - 1)
                        elif next_key == b'P':  # Down arrow
                            selected = min(len(visible_options) - 1, selected + 1)
                    elif char == b'\r':  # Enter key
                        return visible_options[selected]
                    elif char == b'\x1b':  # ESC key
                        return None
                
                # Redraw only after keypress
                os.system('cls')
                print(prompt + (input_buffer if allow_input else ""))
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
            time.sleep(0.01)  # Small sleep to reduce CPU usage

    else:  # Linux/Unix with curses
        def curses_menu(stdscr):
            curses.curs_set(1 if allow_input else 0)
            selected = 0
            input_buffer = ""
            while True:
                stdscr.clear()
                stdscr.addstr(0, 0, prompt + input_buffer)
                for i, option in enumerate(options):
                    if i == selected:
                        stdscr.addstr(i + 1, 0, f"> {option}", curses.color_pair(1))
                    else:
                        stdscr.addstr(i + 1, 0, f"  {option}")
                if info_message:
                    stdscr.addstr(len(options) + 2, 0, info_message, curses.color_pair(2))
                if table_str:
                    stdscr.addstr(len(options) + 4, 0, table_str)
                if middle_content:
                    stdscr.addstr(len(options) + 5 + table_str.count('\n'), 0, middle_content)
                stdscr.refresh()
                
                key = stdscr.getch()
                if allow_input:
                    if key == 10:  # Enter
                        return input_buffer if input_buffer else options[selected]
                    elif key == 27:  # ESC
                        return None
                    elif key == curses.KEY_BACKSPACE or key == 127:
                        input_buffer = input_buffer[:-1]
                    elif 32 <= key <= 126:  # Printable characters
                        input_buffer += chr(key)
                    continue
                if key == curses.KEY_UP:
                    selected = (selected - 1) % len(options)
                elif key == curses.KEY_DOWN:
                    selected = (selected + 1) % len(options)
                elif key == 10:  # Enter
                    return options[selected]
                elif key == 27:  # ESC
                    return None
        
        curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        result = curses.wrapper(curses_menu)
        return result

def get_terminal_height():
    if platform.system() == "Windows":
        return int(os.get_terminal_size().lines)
    else:
        return int(os.popen('tput lines').read())