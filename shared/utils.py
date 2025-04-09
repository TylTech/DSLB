import re
import pandas as pd

def strip_leading_articles(text):
    """Remove leading 'a', 'an', or 'the' (case-insensitive) from a single string."""
    return re.sub(r"^(a |an |the )", "", text.strip(), flags=re.IGNORECASE)

def strip_leading_articles_series(series: pd.Series):
    """Apply article stripping to a Pandas Series of strings (for sorting)."""
    return series.str.lower().map(strip_leading_articles)
