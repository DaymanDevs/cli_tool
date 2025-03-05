import pandas as pd

def format_criteria_value(key, value):
    """Format criteria values for display."""
    if key == "Targeted Feed":
        return str(value) if value is not None else "None"
    elif key == "Links":
        return str(value) if value is not None else "None"
    elif not isinstance(value, dict):  # Handle unexpected non-dict values
        return str(value) if value is not None else "None"
    elif key == "DevBal":
        max_val = value.get("max", float('inf'))
        return f"{max_val:.2f}" if max_val != float('inf') else "No max"
    elif key == "Funding":
        min_val = value.get("min", 0)
        return f"{min_val:.0f}h" if min_val != 0 else "No min"
    elif key == "Bundle":
        max_val = value.get("max", float('inf'))
        return f"{max_val*100:.2f}%" if max_val != float('inf') else "No max"
    elif key in ["AG", "F", "KYC", "Unq", "SM"]:
        min_val = value.get("min", float('-inf'))
        max_val = value.get("max", float('inf'))
        if min_val == float('-inf') and max_val == float('inf'):
            return "No range"
        elif min_val == float('-inf'):
            return f"<= {max_val:.0f}"
        elif max_val == float('inf'):
            return f">= {min_val:.0f}"
        else:
            return f"{min_val:.0f} - {max_val:.0f}"
    else:  # Mcap, Liq, MaxMcap, X's
        min_val = value.get("min", float('-inf'))
        max_val = value.get("max", float('inf'))
        if min_val == float('-inf') and max_val == float('inf'):
            return "No range"
        elif min_val == float('-inf'):
            return f"<= ${max_val:,.0f}"
        elif max_val == float('inf'):
            return f">= ${min_val:,.0f}"
        else:
            return f"${min_val:,.0f} - ${max_val:,.0f}"

def convert_fundtime_to_hours(fundtime):
    """Convert FundTime string to hours."""
    if pd.isna(fundtime) or not isinstance(fundtime, str):
        return float('nan')
    try:
        if 'h' in fundtime:
            return float(fundtime.replace('h', ''))
        elif 'm' in fundtime:
            return float(fundtime.replace('m', '')) / 60
        return float(fundtime)
    except ValueError:
        return float('nan')