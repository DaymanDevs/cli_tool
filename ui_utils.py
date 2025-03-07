import os
import platform
import time

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def display_menu(options):
    """Display a menu and get user selection with retry logic."""
    while True:
        clear_screen()
        print("\nMenu:")
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        try:
            choice = int(input("Select an option: "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            print(f"Please select a number between 1 and {len(options)}.")
            time.sleep(1)  # Brief pause to avoid spamming
        except ValueError:
            print("Invalid input. Please enter a number.")
            time.sleep(1)

def get_user_input(options):
    """Get user input from a list of options with validation."""
    while True:
        clear_screen()
        print("\nOptions:")
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        try:
            choice = int(input("Select an option: "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            print(f"Please select a number between 1 and {len(options)}.")
            time.sleep(1)
        except ValueError:
            print("Invalid input. Please enter a number.")
            time.sleep(1)

def display_message(message, delay=2):
    """Display a message for a specified duration."""
    print(message)
    time.sleep(delay)

# Placeholder for additional functions that might have been in your original file
def validate_input(prompt, valid_options=None):
    """Validate user input against a list of options or type."""
    while True:
        value = input(prompt).strip()
        if valid_options and value not in valid_options:
            print(f"Invalid input. Please enter one of {valid_options}")
            continue
        return value