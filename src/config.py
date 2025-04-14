import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Core Configuration ---
DATABASE_FILE = "email_generator.db"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REASONING_MODEL = "o1"
SEARCH_MODEL = "gpt-4o"

# --- Runtime Flags ---
# Flag to use saved data (for debugging/testing - less relevant with DB logging)
# Set to None to disable, or a key from saved.py (e.g., 'option1', 'option2')
USE_SAVED_DATA_KEY = None # Disabled by default when using DB

# --- Saved Data Import (Keep for fallback/testing if USE_SAVED_DATA_KEY is set) ---
try:
    # Assuming saved.py is in the root directory
    import sys
    # Temporarily add root dir to path to import saved.py if needed
    # This is a bit of a hack, consider better structure if saved.py is crucial
    sys.path.append(os.path.join(os.path.dirname(__file__), '..')) 
    from saved import saved as SAVED_DATA
    sys.path.pop() # Clean up path
except ImportError:
    SAVED_DATA = {}

def get_saved_data(key, default=None):
    """Safely retrieves data from the saved dictionary if USE_SAVED_DATA_KEY is active."""
    if USE_SAVED_DATA_KEY and USE_SAVED_DATA_KEY in SAVED_DATA:
        return SAVED_DATA[USE_SAVED_DATA_KEY].get(key, default)
    return None

# --- Removed DB-related static config ---
# PRODUCT_NAME, TARGET_NAME, etc. will be fetched based on client_id
# REFERENCE_EMAIL and ZERO_SHOT_ADVICE will be fetched from the Clients table

# Target Information (Example - could be loaded from elsewhere)
# Option 1: OptimizeX Target
# PRODUCT_NAME = "OptimizeX" # Corresponds to email file emails/OptimizeX.txt
# TARGET_NAME = "Fred Crehan"
# TARGET_TITLE = "Area Vice President for Emerging Markets"
# TARGET_COMPANY = "Confluent"
# SOURCE = 'email' # 'email' or 'web'

# Option 2: ShelfIQ Target
PRODUCT_NAME = "ShelfIQ"
TARGET_NAME = "Alex Phillips"
TARGET_TITLE = "Director of E-commerce"
TARGET_COMPANY = "Coca-Cola"
SOURCE = 'web' # 'email' or 'web'

# Reference email for one-shot improvement
REFERENCE_EMAIL = """Hi Jamie,
I was checking out the redesign you did for Westbrook's site last month (that hero
animation is seriously impressive!) and it got me wondering about your team's
process.
I work with a tool called DesignFlow that's helping agencies like yours cut down on
the back-and-forth nightmare of client feedback cycles. One of our customers, Studio
Bright, was telling me they've shortened their revision rounds by almost half since
they started using it.
If your team is drowning in screenshot annotations and "can you move this 2px to the
left" comments, I'd love to show you how it works. No pressure though - just thought
it might be useful based on the complex work you're doing.
Would you be open to a quick 10-min demo sometime next week?
"""

# Advice for zero-shot improvement
ZERO_SHOT_ADVICE = f"""
• Add a personal touch early on—acknowledge {TARGET_NAME}'s specific accomplishment and show genuine interest or admiration.  
• Break up paragraphs for easier reading; shorter paragraphs highlight key points more effectively.  
• Provide a clear, concise statement of why you're reaching out—explain the specific problem your solution can address (e.g., compliance, real-time analytics, saving time).  
• Use direct, simple language to describe your product's value.  
• Include only one call to action—offer a brief chat or demo in a way that feels casual and low-pressure.  
• Keep the language friendly and helpful rather than salesy.  
""" 