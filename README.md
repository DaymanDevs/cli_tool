# CLI Tool for Crypto Feed Analysis

This is a command-line interface (CLI) tool built in Python to analyze cryptocurrency feed data from CSV files, manage wallet configurations, and display results in a terminal-based UI. It’s designed to process data from multiple feeds (e.g., PF, Fomo, BB) and their "Top" variants, integrating market cap data from MCAPS files.

## Project Overview

- **Purpose**: Analyze crypto token data, apply wallet configurations, and provide filtering and search capabilities.
- **Current State**: Step 6 (Wallet Configs) is implemented and being stabilized as of March 05, 2025.
- **Next Steps**: Step 7 (Strategies) pending stabilization of Step 6.
- **Maintainer**: Developed with assistance from Grok (xAI) in a continuous chat instance.

## Repository Structure

cli_tool/
├── data/               # CSV data files (ignored by .gitignore)
│   ├── fomo.csv       # Sample regular feed data
│   ├── fomo10.csv     # Sample top feed data
│   └── MCAPS-*.csv    # Market cap data (fetched via dune_fetcher.py)
├── exports/           # Exported CSV files (ignored)
├── config.py          # Configuration (DATA_DIRECTORY = 'data')
├── data_loader.py     # Loads and combines CSV data
├── dune_fetcher.py    # Fetches MCAPS data from Dune Analytics
├── main.py            # Main CLI entry point
├── table_display.py   # Table display and interaction logic
├── table_format.py    # Formats tables for display
├── table_utils.py     # Filtering, searching, and wallet summary utils
├── ui_utils.py        # Menu selection and UI helpers
├── utils.py           # General utilities (e.g., convert_fundtime_to_hours)
├── wallet_config.py   # Wallet configuration management
├── wallet_utils.py    # Wallet table formatting and editing
├── .gitignore         # Ignores pycache, logs, exports, data/
├── debug.log          # Debug output (ignored)
└── README.md          # This file

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/DaymanDevs/cli_tool.git
   cd cli_tool

Install Dependencies:
Requires Python 3.8+.

Install required packages:
bash

pip install pandas colorama dune-client

Prepare Data:
Place CSV files (e.g., fomo.csv, fomo10.csv, MCAPS-*.csv) in data/.

Sample data available in chat history (March 05, 2025).

Run the Tool:
bash

python main.py

Features
Main Menu:
"Tables": View feeds (e.g., PF, Fomo, Fomo Top).

"Wallets": Manage wallet configs (create, edit, delete, duplicate).

"Search by contract": Search across feeds by contract address.

"Exit": Quit the program.

Table View:
Filter tables by columns (e.g., Mcap, Date).

Search in PF for contract history.

Export filtered tables to CSV.

Apply wallet configs to classify rows (buy/skip/rug).

Wallet Configs:
Stored in data/wallets.json.

Criteria: Mcap, Liq, AG, DevBal, Funding, Bundle, Links, F, KYC, Unq, SM, MaxMcap, X's, Targeted Feed.

Summary stats: Buys, Skips, Rugs, X’s thresholds, Best X, Profit X.

Development Details
Step 6 (Wallet Configs):
Implemented: Create, edit, apply, remove wallet configs.

Issues Fixed: Filtering, Top table data priority, wallet display.

Known Bugs: None as of last commit; verify stability.

Data Processing:
data_loader.py: Combines CSVs, prioritizes Top table data (*10.csv) over MCAPS for MaxMcap and X's.

dune_fetcher.py: Fetches MCAPS data (API key: h4ZLtm3ncY1JawdkTP42iGEzJrb2f5RY, Query ID: 4580261).

UI:
Arrow-key navigation with ui_utils.py.

Color-coded output via colorama.

Sample Data
fomo.csv:

Contract,Name,Mcap,HighestMcap,Multiples
28fxheg5wKecHikhxdvo4eGxhGjJ9fHCKsfwmgUSpump,RTBM,54400.0,843700.0,15.5x
...

fomo10.csv (Top 10):

Contract,Name,Mcap,HighestMcap,Multiples
7HGmekaiyGHmAcycy9HrmPoTaXc6azJJTz14xNe3pump,UPF,11100.0,188600.0,17.0x
...

wallets.json: 9 wallet configs (see chat history).

Troubleshooting
Common Errors:
NameError: 'menu_selection' not defined: Ensure ui_utils imports are correct.

KeyError: 'max': Check utils.py for robust criteria formatting.

TypeError: str doesn't define __round__': Verify table_format.py numeric handling.

Debugging:
Check debug.log for data loading issues.

Add print statements in functions to trace execution.

Resuming Development
Pull Latest:
bash

git pull origin main

Review Chat History:
Start from March 05, 2025, Grok chat instance with DaymanDevs.

Key updates: Step 6 fixes, Git setup.

Test Current State:
Run python main.py, verify all menu options.

Check Top tables use *10.csv data correctly.

Next Steps:
Stabilize Step 6 (wallet configs).

Implement Step 7 (Strategies).

Commit History
Initial Commit: "Initial commit with CLI tool files".

Latest Commit: "Fixed filtering, top tables, and wallet configs" (pending your test).

Contact
GitHub: DaymanDevs

Issues: File at cli_tool/issues

