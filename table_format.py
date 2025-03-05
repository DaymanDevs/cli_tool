import pandas as pd
import colorama
from colorama import Fore, Style

def format_table_columns(df, applied_configs=None):
    """Format table with column dividers, colors, and fixed widths to match the provided image."""
    headers = list(df.columns)
    column_widths = {
        col: max(len(str(col)), df[col].apply(lambda x: len(str(x)) if pd.notnull(x) else 3).max() + 2)
        for col in headers
    }
    column_widths['Contract'] = 8  # 4 chars + "..."
    column_widths['Bundle'] = 7  # e.g., "5.24%"
    column_widths['Dev%'] = 7  # e.g., "5.24%"
    column_widths['X\'s'] = 8  # e.g., "15.50x"
    max_mcap_value = df['MaxMcap'].apply(lambda x: len(f"${int(round(x, 0)):,}") if pd.notnull(x) else 3).max()
    column_widths['MaxMcap'] = max(8, min(12, max_mcap_value + 2))
    for col in ['AG', 'F', 'KYC', 'Unq', 'SM']:
        if col in column_widths:
            column_widths[col] = 4
    
    formatted_lines = []
    
    header_line = " | ".join(f"{Fore.CYAN}{col:<{column_widths[col]}}{Style.RESET_ALL}" for col in headers)
    formatted_lines.append(header_line)
    formatted_lines.append("-" * (sum(column_widths.values()) + 3 * (len(headers) - 1)))
    
    for _, row in df.iterrows():
        line = []
        for col in headers:
            if pd.isna(row[col]):
                value = "NaN"
                color = Fore.RED
            else:
                if col == 'Contract':
                    value = f"{row[col][:4]}..."
                elif col == 'Date':
                    date_str = row[col]
                    if isinstance(date_str, str) and " " in date_str:
                        date_part, time_part = date_str.split(" ", 1)
                        value = f"{date_part}{time_part}"
                    else:
                        value = date_str
                elif col in ['Mcap', 'Liq', 'MaxMcap']:
                    value = f"${int(round(float(row[col]) if pd.notnull(row[col]) else 0)):,.0f}"
                elif col in ['Bundle', 'Dev%']:
                    value = f"{float(row[col])*100:.2f}%" if pd.notnull(row[col]) else "NaN"
                elif col == 'Funding':
                    value = str(row[col])
                elif col == 'X\'s':
                    value = f"{float(row[col]):.2f}x" if pd.notnull(row[col]) else "0.00x"
                elif col in ['DevBal', 'AG', 'F', 'KYC', 'Unq', 'SM']:
                    try:
                        num_val = float(row[col]) if pd.notnull(row[col]) else 0
                        value = f"{num_val:.2f}" if col == 'DevBal' else f"{int(round(num_val))}"
                    except (ValueError, TypeError):
                        value = str(row[col])  # Fallback to string if conversion fails
                else:
                    value = str(row[col])
                if applied_configs and col in applied_configs.keys():
                    color = Fore.GREEN
                else:
                    color = get_column_color(col, row[col])
            formatted = f"{color}{value:<{column_widths[col]}}{Style.RESET_ALL}"
            line.append(formatted)
        formatted_lines.append(" | ".join(line))
    
    return "\n".join(formatted_lines)

def get_column_color(column, value):
    """Assign colors based on column and value."""
    if pd.isna(value):
        return Fore.RED
    if column in ['Mcap', 'Liq', 'MaxMcap']:
        return Fore.GREEN if float(value) > 0 else Fore.RED
    elif column in ['Bundle', 'Dev%']:
        return Fore.YELLOW
    elif column == 'Funding':
        return Fore.WHITE
    elif column == 'X\'s':
        return Fore.GREEN if float(value) > 0 else Fore.RED
    elif column in ['DevBal', 'Links', 'AG', 'F', 'KYC', 'Unq', 'SM']:
        return Fore.WHITE
    elif column == 'Contract':
        return Fore.CYAN
    return Fore.WHITE