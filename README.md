# DigitalOcean Cost Alert

This repository contains a Python script that fetches daily DigitalOcean costs and saves them as markdown tables, organized by year and month.

## Structure

```
YYYY/
  MM/
    DD.md
```

Each markdown file contains a table with the daily costs and total amount.

## Setup

1. Fork/Clone this repository
2. Set up your DigitalOcean API token:
   - Go to DigitalOcean's [API settings](https://cloud.digitalocean.com/account/api/tokens)
   - Create a new read-only token
   - Go to your GitHub repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `DO_TOKEN`
   - Value: Your DigitalOcean API token

## GitHub Actions

The script runs automatically every day at 00:00 UTC via GitHub Actions. It will:
1. Fetch the daily costs from DigitalOcean
2. Generate a markdown table with the costs
3. Save it in the appropriate year/month directory
4. Commit and push the changes

You can also trigger the workflow manually from the Actions tab in your repository.

## Output Format

### Daily Cost Report
Each daily report (`YYYY/MM/DD.md`) includes:
- Date and timestamp
- Table with service descriptions and costs
- Total daily cost

Example:
```markdown
# DigitalOcean Cost Report - 2025-02-16

| Description | Amount ($) | Duration |
|------------|------------|----------|
| Droplet: web-server | 10.00 | 24h |
| Spaces Storage | 5.00 | N/A |
| **Total** | **15.00** | |

*Generated at: 2025-02-16 08:00:00*
```

### Monthly Summary
Each month also has a summary file (`YYYY/MM/monthly_summary.md`) that shows:
- Daily costs
- Running total for the month

Example:
```markdown
# DigitalOcean Cost Summary - February 2025

| Day | Cost ($) | Running Total ($) |
|-----|----------|------------------|
| 1   | 15.00    | 15.00           |
| 2   | 15.00    | 30.00           |
| 3   | 15.00    | 45.00           |
```

## Error Handling

If any errors occur (e.g., invalid token, API issues), they will be appended to the daily file with details about the error and timestamp.
