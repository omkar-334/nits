import asyncio

from scraper import scrape

# Example usage:
condition = "diabetes"
email = "example_email@example.com"

# Running the scrape function with the condition and email
asyncio.run(scrape(condition, email))
