import pandas as pd

def filter_data(data, query_params):
    """Filters data based on query parameters."""
    if not query_params:
        return data  # Return all data if no filters are applied

    filtered_data = data.copy()
    for key, value in query_params.items():
        if key in filtered_data.columns:
            try:
                value = float(value)  # Convert numerical values for filtering
                filtered_data = filtered_data[filtered_data[key] == value]
            except ValueError:
                filtered_data = filtered_data[filtered_data[key].astype(str) == value]

    return filtered_data

def display_results(stdscr, results):
    """Displays query results in the CLI using a paginated format."""
    if results.empty:
        stdscr.addstr(2, 0, "No matching results found.")
        stdscr.refresh()
        stdscr.getch()
        return

    rows, cols = results.shape
    page_size = 10  # Number of results per page
    total_pages = (rows // page_size) + (1 if rows % page_size else 0)
    current_page = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Displaying results (Page {current_page + 1}/{total_pages})")
        
        start = current_page * page_size
        end = start + page_size
        display_data = results.iloc[start:end]

        for i, row in enumerate(display_data.itertuples(), start=2):
            stdscr.addstr(i, 0, f"{row.Index}: {', '.join(map(str, row[1:]))}")

        stdscr.addstr(page_size + 4, 0, "Use UP/DOWN to navigate, ENTER to exit.")
        stdscr.refresh()

        key = stdscr.getch()
        if key in [10, 13]:  # Enter key
            break
        elif key == curses.KEY_DOWN and current_page < total_pages - 1:
            current_page += 1
        elif key == curses.KEY_UP and current_page > 0:
            current_page -= 1
