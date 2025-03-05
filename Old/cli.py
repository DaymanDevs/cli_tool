import click
from settings_manager import settings_manager
from combine_data import load_and_combine_csv

# Load CSV data into a global variable
data_directory = 'data'
all_data = load_and_combine_csv(data_directory)

@click.group()
def cli():
    """CLI for managing bot settings and querying data."""
    pass

@cli.command()
def list_profiles():
    """List all bot setting profiles."""
    profiles = settings_manager.list_profiles()
    print("Available profiles:")
    for profile in profiles:
        print(profile)

@cli.command()
@click.argument('profile_name')
def show_settings(profile_name):
    """Show settings for a specific bot profile."""
    settings = settings_manager.get_settings(profile_name)
    print(f"Settings for {profile_name}: {settings}")

@cli.command()
@click.argument('profile_name')
@click.option('--mcap', type=int, help='Minimum market cap.')
@click.option('--liquidity', type=int, help='Minimum liquidity.')
@click.option('--ag-score', type=int, help='Minimum AG score.')
@click.option('--dev-wallets', type=int, help='Developer wallets.')
@click.option('--ag-score2', type=int, help='Additional AG score.')
def update_settings(profile_name, **kwargs):
    """Update settings for a specific bot profile."""
    filtered_kwargs = {key: value for key, value in kwargs.items() if value is not None}
    settings_manager.update_settings(profile_name, filtered_kwargs)
    print(f"Updated settings for {profile_name}: {settings_manager.get_settings(profile_name)}")

@cli.command()
@click.argument('profile_name')
def delete_profile(profile_name):
    """Delete a specific bot profile."""
    settings_manager.delete_profile(profile_name)
    print(f"Deleted profile {profile_name}")

@cli.command()
@click.argument('setting_name')
def add_setting(setting_name):
    """Add a new setting option."""
    settings_manager.add_setting_option(setting_name)
    print(f"Added setting option: {setting_name}")

@cli.command()
@click.argument('setting_name')
def remove_setting(setting_name):
    """Remove a setting option."""
    settings_manager.remove_setting_option(setting_name)
    print(f"Removed setting option: {setting_name}")

@cli.command()
@click.argument('profile_name')
def query_by_profile(profile_name):
    """Query data using a bot profile configuration."""
    settings = settings_manager.get_settings(profile_name)
    if not settings:
        print(f"No settings found for profile {profile_name}")
        return

    for channel, data in all_data.items():
        filtered = data
        for key, value in settings.items():
            if value is not None and key in data.columns:
                filtered = filtered[filtered[key] >= value]
        print(f"Filtered data for {channel} using profile {profile_name}:")
        print(filtered.head())

if __name__ == '__main__':
    cli()
