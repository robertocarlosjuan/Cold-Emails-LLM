import os
import sys
import inspect
import src.config as config

# --- Add src to path to allow importing from src --- 
# Calculate the path to the project root directory (assuming setup_database.py is in the root)
# If it's elsewhere, adjust the path accordingly.
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
# --- End Add src to path ---

from src.database.models import db, Clients, Prompts, GeneratedEmails
from src.prompts.product_description import system as pd_system, query as pd_query
from src.prompts.target_description import system as td_system, query as td_query
from src.prompts.baseline_email import system as be_system, query as be_query
from src.prompts.summary import system as s_system, query as s_query
from src.prompts.first_draft import system as fd_system, query as fd_query
from src.prompts.one_shot_improvement import system as osi_system, query as osi_query
from src.prompts.zero_shot_improvement import system as zsi_system, query as zsi_query

# Dictionary mapping stage names to their prompt modules/constants
# We need to handle cases where prompts are functions (for f-strings)
PROMPT_SOURCES = {
    'product_description_web': {'system': pd_system.SYSTEM_PROMPT_WEB, 'query': pd_query.get_query_web},
    'product_description_email': {'system': pd_system.SYSTEM_PROMPT_EMAIL, 'query': pd_query.get_query_email},
    'target_description': {'system': td_system.SYSTEM_PROMPT, 'query': td_query.get_query},
    'baseline_email': {'system': be_system.SYSTEM_PROMPT, 'query': be_query.get_query},
    'summary': {'system': s_system.get_system_prompt, 'query': s_query.get_message_prompt},
    'first_draft': {'system': fd_system.SYSTEM_PROMPT, 'query': fd_query.get_query},
    'one_shot_improvement': {'system': osi_system.SYSTEM_PROMPT, 'query': osi_query.get_query},
    'zero_shot_improvement': {'system': zsi_system.SYSTEM_PROMPT, 'query': zsi_query.get_query},
}

def get_prompt_template_string(prompt_source):
    """Extracts the raw template string, handling functions vs strings."""
    if callable(prompt_source):
        # Get the source code of the function
        source_lines, _ = inspect.getsourcelines(prompt_source)
        source_code = "".join(source_lines)
        
        # Heuristic: Find the triple-quoted string return value
        # This is fragile and depends on the function structure
        start_f = source_code.find('f"""')
        start_plain = source_code.find('"""')
        
        start_index = -1
        is_fstring = False

        if start_f != -1 and (start_plain == -1 or start_f < start_plain):
            start_index = start_f + 1 # Keep the f prefix
            is_fstring = True
        elif start_plain != -1:
            start_index = start_plain
        
        if start_index != -1:
            end_index = source_code.find('"""', start_index + 3) 
            if end_index != -1:
                # +3 to include the closing triple quotes if needed, or adjust as necessary
                template = source_code[start_index:end_index+3]
                # Optional: Clean up indentation if needed (complex)
                return template.strip()
        
        print(f"Warning: Could not automatically extract template from {prompt_source.__name__}. Storing function name.")
        return f"<Function: {prompt_source.__name__}>" # Fallback
    elif isinstance(prompt_source, str):
        return prompt_source.strip()
    elif prompt_source is None:
        return "" # Store empty string for None prompts
    else:
        print(f"Warning: Unknown prompt source type: {type(prompt_source)}. Storing as string.")
        return str(prompt_source)

def clear_data():
    """Deletes all data from the tables."""
    print("Clearing existing data...")
    # Delete in reverse order of foreign key dependencies
    deleted_emails = GeneratedEmails.delete().execute()
    deleted_prompts = Prompts.delete().execute()
    deleted_clients = Clients.delete().execute()
    print(f"  Deleted {deleted_emails} email records.")
    print(f"  Deleted {deleted_prompts} prompt records.")
    print(f"  Deleted {deleted_clients} client records.")

def populate_prompts():
    """Populates the Prompts table from the imported sources."""
    print("Populating prompts...")
    with db.atomic(): # Use a transaction
        for stage_name, types in PROMPT_SOURCES.items():
            for prompt_type, source in types.items():
                template_str = get_prompt_template_string(source)
                
                # Use create_or_get to avoid duplicates if run again, 
                # or update if needed (though update logic isn't added here)
                prompt, created = Prompts.get_or_create(
                    stage_name=stage_name,
                    prompt_type=prompt_type,
                    defaults={'prompt_template': template_str}
                )
                if created:
                    print(f"  Created prompt: {stage_name} / {prompt_type}")
                else:
                    # Optionally update if the template changed
                    if prompt.prompt_template != template_str:
                        print(f"  Updating prompt: {stage_name} / {prompt_type}")
                        prompt.prompt_template = template_str
                        prompt.save()
                    else:
                         print(f"  Prompt exists: {stage_name} / {prompt_type}")
                         
def add_sample_client():
    """Adds a sample client for testing."""
    print("Adding sample client...")
    client, created = Clients.get_or_create(
        client_name="Sample Client Inc.",
        defaults={
            "product_name": "ShelfIQ",
            "product_info_source_type": "web",
            "product_info_detail": "No specific URL, generate via web search",
            "reference_email_text": """Hi Jamie,\nI was checking out the redesign... (rest of your example)""",
            "zero_shot_advice_template": """• Add a personal touch early on—acknowledge {target_name}’s specific accomplishment... (rest of your template)"""
        }
    )
    if created:
        print(f"  Created sample client: {client.client_name} (ID: {client.client_id})")
    else:
        print(f"  Sample client already exists: {client.client_name} (ID: {client.client_id})")

def setup():
    """Creates database tables, clears old data, and populates initial data."""
    print(f"Connecting to database: {config.DATABASE_FILE}")
    db.connect()
    print("Creating tables (if they don't exist)...")
    # safe=True prevents errors if tables already exist
    db.create_tables([Clients, Prompts, GeneratedEmails], safe=True)
    print("Tables checked/created.")
    
    # Clear existing data before populating
    clear_data()

    # Populate with fresh data
    populate_prompts()
    add_sample_client() # Add a sample client
    
    db.close()
    print("Database setup complete.")

if __name__ == "__main__":
    setup() 