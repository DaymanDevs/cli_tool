import pandas as pd
import colorama
from colorama import Fore, Style

def format_table_columns(df, applied_configs):
    if df.empty:
        return "No data available."
    
    df = df.copy()
    col_widths = {}
    for col in df.columns:
        if col == "token":
            df[col] = df[col].apply(lambda x: f"{str(x)[:8]}..." if pd.notna(x) and len(str(x)) > 8 else str(x))
        elif col == "Links":
            df[col] = df[col].apply(lambda x: "Yes" if pd.notna(x) and x else "No")
        elif col in ["Bundle", "Dev%"]:
            df[col] = df[col].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "NaN")
        elif col == "Date":
            df[col] = df[col].apply(lambda x: x.strftime('%d/%m/%y %H:%M') if pd.notna(x) and isinstance(x, pd.Timestamp) else "NaN")
        elif col == "X's":
            df[col] = df[col].apply(lambda x: f"{x:.2f}x" if pd.notna(x) else "NaN")
        elif col in ["Mcap", "Liq", "MaxMcap", "DevBal"]:
            df[col] = df[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "NaN")
        else:
            df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) else "NaN")
        col_widths[col] = max(len(str(col)), df[col].str.len().max())
    
    header = " | ".join(f"{Fore.CYAN}{col:<{col_widths[col]}}{Style.RESET_ALL}" for col in df.columns)
    separator = " | ".join("-" * col_widths[col] for col in df.columns)
    rows = []
    for _, row in df.iterrows():
        formatted_row = []
        for col in df.columns:
            value = str(row[col])
            if col in applied_configs:
                color = Fore.GREEN if value == "buy" else Fore.RED if value == "skip" else Fore.WHITE
                formatted_row.append(f"{color}{value:<{col_widths[col]}}{Style.RESET_ALL}")
            else:
                formatted_row.append(f"{value:<{col_widths[col]}}")
        rows.append(" | ".join(formatted_row))
    
    return "\n".join([header, separator] + rows)