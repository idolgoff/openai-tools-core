"""Test script to check environment variables loading."""
import os
from dotenv import load_dotenv

# Force reload of environment variables
load_dotenv(override=True)

# Print the token
print(f"TELEGRAM_BOT_TOKEN: {os.getenv('TELEGRAM_BOT_TOKEN')}")
