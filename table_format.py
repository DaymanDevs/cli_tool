import pandas as pd
import colorama
from colorama import Fore, Style

def format_table_columns(df, configs):
    if df.empty:
        return "No data available."
    
    headers = df.columns.tolist()
    column_widths = {
        '#': 4, 'Contract': 8, 'Date': 16, 'Name': 9, 'Mcap': 9, 'Liq': 9, 
        'AG': 4, 'Bundle': 7, 'Dev%': 7, 'DevBal': 6, 'Links': 5, 'F': 4, 
        'KYC': 4, 'Unq': 4, 'SM': 4, 'Funding': 14, 'MaxMcap': 11, 'X\'s': 6,
        'Iteration': 9
    }
    for header in headers:
        if header not in column_widths:
            column_widths[header] = min(10, max(4, len(str(header))))
    for config in configs or []:
        column_widths[config] = max(8, len(config))

    formatted_rows = []
    header_row = " | ".join(f"{Fore.CYAN}{header:<{column_widths.get(header, 10)}}{Style.RESET_ALL}" for header in headers)
    formatted_rows.append(header_row)
    formatted_rows.append("-" * len(header_row))  # Dynamic length based on header row

    for _, row in df.iterrows():
        formatted_row = []
        for header in headers:
            value = row.get(header, pd.NA)
            if pd.isna(value):
                formatted_value = "NaN"
            elif header in ["Mcap", "Liq", "MaxMcap"]:
                formatted_value = f"${value:,.0f}"
                if len(formatted_value) > column_widths[header]:
                    formatted_value = formatted_value[:column_widths[header]-1] + '+'
            elif header == "X's":
                formatted_value = f"{value:.2f}x"
            elif header in ["Bundle", "Dev%"]:
                formatted_value = f"{value*100:.2f}%"
            elif header in ["AG", "F", "KYC", "Unq", "SM", "DevBal", "Iteration", "Token Age"]:
                if isinstance(value, (int, float)):
                    formatted_value = f"{value:.2f}" if header == "DevBal" else f"{value:.0f}"
                else:
                    formatted_value = str(value)
            else:
                formatted_value = str(value)
                if len(formatted_value) > column_widths[header]:
                    formatted_value = formatted_value[:column_widths[header]-1] + '>'
            if configs and header in configs and value != "buy" and not pd.isna(value):
                formatted_value = f"{Fore.RED}{formatted_value}{Style.RESET_ALL}"
            formatted_row.append(f"{formatted_value:<{column_widths.get(header, 10)}}")
        formatted_rows.append(" | ".join(formatted_row))
    
    return "\n".join(formatted_rows)