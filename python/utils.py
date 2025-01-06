def format_number(num):
    """Format a number with commas and K/M/B suffixes where appropriate."""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:,.1f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:,.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:,.1f}K"
    else:
        return f"{num:,}"

