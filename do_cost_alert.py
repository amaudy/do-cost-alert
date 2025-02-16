#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import digitalocean
from tabulate import tabulate
import requests.exceptions

class DigitalOceanError(Exception):
    """Base exception class for DigitalOcean API errors."""
    pass

class TokenError(DigitalOceanError):
    """Exception raised for token-related issues."""
    pass

class APIError(DigitalOceanError):
    """Exception raised for DigitalOcean API issues."""
    pass

def get_do_manager():
    """Initialize DigitalOcean manager with API token."""
    token = os.getenv('DO_TOKEN')
    if not token:
        raise TokenError("DigitalOcean API token not found. Please set DO_TOKEN environment variable.")
    
    try:
        manager = digitalocean.Manager(token=token)
        # Verify token by making a simple API call
        manager.get_account()
        return manager
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise TokenError("Invalid DigitalOcean API token. Please check your token and try again.")
        raise APIError(f"HTTP Error: {str(e)}")
    except requests.exceptions.ConnectionError:
        raise APIError("Connection error. Please check your internet connection.")
    except requests.exceptions.Timeout:
        raise APIError("Request timed out. Please try again later.")
    except requests.exceptions.RequestException as e:
        raise APIError(f"An error occurred while connecting to DigitalOcean: {str(e)}")
    except Exception as e:
        raise APIError(f"Unexpected error: {str(e)}")

def get_billing_history(manager):
    """Fetch billing history from DigitalOcean."""
    try:
        return manager.get_billing_history()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise TokenError("Token authorization failed while fetching billing history.")
        elif e.response.status_code == 429:
            raise APIError("Rate limit exceeded. Please try again later.")
        raise APIError(f"HTTP Error while fetching billing history: {str(e)}")
    except Exception as e:
        raise APIError(f"Error fetching billing history: {str(e)}")

def calculate_daily_cost(billing_history):
    """Calculate the cost for the current day."""
    today = datetime.now().date()
    daily_costs = []
    
    for item in billing_history:
        date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        if date == today:
            daily_costs.append({
                'description': item['description'],
                'amount': item['amount'],
                'duration': item.get('duration', 'N/A')
            })
    
    return daily_costs

def create_markdown_table(daily_costs):
    """Create a markdown table from daily costs."""
    if not daily_costs:
        return "No costs recorded for today.", 0
    
    headers = ["Description", "Amount ($)", "Duration"]
    table_data = [
        [item['description'], f"{item['amount']:.2f}", item['duration']]
        for item in daily_costs
    ]
    
    total_cost = sum(item['amount'] for item in daily_costs)
    table_data.append(["**Total**", f"**{total_cost:.2f}**", ""])
    
    return tabulate(table_data, headers=headers, tablefmt="pipe"), total_cost

def update_monthly_summary(daily_costs, total_cost):
    """Update the monthly summary table."""
    now = datetime.now()
    year_dir = Path(str(now.year))
    month_dir = year_dir / f"{now.month:02d}"
    summary_file = month_dir / "monthly_summary.md"
    
    # Initialize monthly data structure
    monthly_data = {}
    
    # Read existing monthly summary if it exists
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            content = f.read()
            # Skip header and find the table content
            if '|' in content:
                lines = [line.strip() for line in content.split('\n') if '|' in line]
                # Skip header and separator lines
                for line in lines[2:]:
                    if '|' in line:
                        cols = [col.strip() for col in line.split('|')[1:-1]]
                        if len(cols) >= 2:
                            try:
                                day = int(cols[0])
                                cost = float(cols[1].replace('$', '').replace(',', ''))
                                monthly_data[day] = cost
                            except (ValueError, IndexError):
                                continue

    # Update today's cost
    monthly_data[now.day] = total_cost
    
    # Create the monthly summary table
    headers = ["Day", "Cost ($)", "Running Total ($)"]
    table_data = []
    running_total = 0
    
    for day in range(1, 32):  # Support all possible days in a month
        if day in monthly_data:
            running_total += monthly_data[day]
            table_data.append([
                str(day),
                f"{monthly_data[day]:.2f}",
                f"{running_total:.2f}"
            ])
    
    monthly_table = tabulate(table_data, headers=headers, tablefmt="pipe")
    
    # Save the monthly summary
    with open(summary_file, 'w') as f:
        f.write(f"# DigitalOcean Cost Summary - {now.strftime('%B %Y')}\n\n")
        f.write(monthly_table)
        f.write("\n\n")
        f.write(f"*Last Updated: {now.strftime('%Y-%m-%d %H:%M:%S')}*\n")

def save_daily_file(content, is_error=False):
    """Save content to a daily markdown file."""
    now = datetime.now()
    year_dir = Path(str(now.year))
    month_dir = year_dir / f"{now.month:02d}"
    
    # Create directories if they don't exist
    month_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the daily markdown file
    file_path = month_dir / f"{now.day:02d}.md"
    
    # If file exists and we're reporting an error, append to it
    if is_error and file_path.exists():
        with open(file_path, 'a') as f:
            f.write("\n\n")
            f.write("---\n\n")  # Add separator
            f.write(content)
    else:
        with open(file_path, 'w') as f:
            f.write(content)

def save_cost_report(content, total_cost):
    """Save the cost report to a markdown file."""
    now = datetime.now()
    report_content = f"# DigitalOcean Cost Report - {now.strftime('%Y-%m-%d')}\n\n"
    report_content += content
    report_content += f"\n\n*Generated at: {now.strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    save_daily_file(report_content)

def save_error_report(error):
    """Save error information to the daily file."""
    now = datetime.now()
    error_content = f"# DigitalOcean Error Report - {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    error_content += "```\n"
    error_content += f"Error Type: {type(error).__name__}\n"
    error_content += f"Error Message: {str(error)}\n"
    error_content += "```\n"
    error_content += f"\n*Error recorded at: {now.strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    save_daily_file(error_content, is_error=True)

def main():
    """Main function to run the cost alert script."""
    try:
        manager = get_do_manager()
        billing_history = get_billing_history(manager)
        daily_costs = calculate_daily_cost(billing_history)
        markdown_table, total_cost = create_markdown_table(daily_costs)
        save_cost_report(markdown_table, total_cost)
        update_monthly_summary(daily_costs, total_cost)
        print("Cost report generated successfully!")
    except TokenError as e:
        error_msg = f"Token Error: {str(e)}"
        print(error_msg, file=sys.stderr)
        save_error_report(e)
        sys.exit(1)
    except APIError as e:
        error_msg = f"API Error: {str(e)}"
        print(error_msg, file=sys.stderr)
        save_error_report(e)
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg, file=sys.stderr)
        save_error_report(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
