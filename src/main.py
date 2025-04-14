import sys
import os
import traceback
from peewee import DoesNotExist

# Add project root to sys.path to allow running with `python src/main.py`
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src import processors
from src.database.models import db, Clients, GeneratedEmails

def run_pipeline_for_recipient(client_id, recipient_name, recipient_title, recipient_company):
    """Runs the full email generation pipeline for a specific recipient and logs to DB."""
    
    db.connect(reuse_if_open=True) # Ensure DB connection is open
    generated_email_record = None # Initialize
    client = None

    try:
        # 1. Fetch Client Data
        try:
            client = Clients.get_by_id(client_id)
            print(f"Found client: {client.client_name} (ID: {client.client_id})")
        except DoesNotExist:
            print(f"Error: Client with ID {client_id} not found.")
            db.close()
            return

        # 2. Create Initial Log Record
        generated_email_record = GeneratedEmails.create(
            client=client,
            recipient_name=recipient_name,
            recipient_title=recipient_title,
            recipient_company=recipient_company,
            status='processing' 
        )
        print(f"Created initial log record ID: {generated_email_record.output_id} for recipient: {recipient_name}")

        # --- Execute Pipeline Stages --- 
        # Wrap stages in try/except to update final status
        
        # Stage 1: Product Description
        product_description = processors.generate_product_description(client, generated_email_record)
        
        # Stage 2: Target Description
        target_description = processors.generate_target_description(client, generated_email_record, product_description)
        
        # Optional: Baseline Email (Not logged directly to main record)
        # processors.generate_baseline_email(client, recipient_name, product_description, target_description)
        
        # Stage 3: Summary
        summary = processors.generate_summary(client, generated_email_record, product_description, target_description)
        
        # Stage 4: First Draft Email
        first_draft_email = processors.generate_first_draft_email(client, generated_email_record, summary)
        
        # --- Improvement Stages & Final Selection --- 
        # Decide which improvement method to prioritize or use based on success
        one_shot_email = None
        zero_shot_email = None
        final_email = None
        final_type = None

        # Stage 5: One-Shot Improvement (Attempt if reference exists)
        if client.reference_email_text:
            one_shot_email = processors.generate_one_shot_email(client, generated_email_record, first_draft_email)
        
        # Stage 6: Zero-Shot Improvement (Attempt if advice exists)
        if client.zero_shot_advice_template:
            zero_shot_email = processors.generate_zero_shot_email(client, generated_email_record, first_draft_email)

        # Simple selection logic: Prioritize One-Shot, then Zero-Shot, then First Draft
        if one_shot_email and not one_shot_email.startswith("Error:"):
            final_email = one_shot_email
            final_type = 'one_shot'
        elif zero_shot_email and not zero_shot_email.startswith("Error:"):
            final_email = zero_shot_email
            final_type = 'zero_shot'
        elif first_draft_email and not first_draft_email.startswith("Error:"):
             final_email = first_draft_email
             final_type = 'first_draft'
        else:
             # If all stages failed somehow
             raise Exception("All email generation stages failed or returned errors.")
             
        # Log final selected email
        generated_email_record.final_selected_email_type = final_type
        generated_email_record.final_selected_email_output = final_email
        generated_email_record.status = 'completed'
        print(f"\n######### Final Selected Email ({final_type}) #########\n{final_email}")

    except Exception as e:
        print(f"\n--- PIPELINE FAILED --- ")
        print(f"Error during pipeline execution: {e}")
        detailed_error = traceback.format_exc()
        print(detailed_error)
        if generated_email_record:
            generated_email_record.status = 'failed'
            generated_email_record.error_message = detailed_error 
            # Ensure partial results are saved before setting status
            generated_email_record.save() 
        else:
            # Error happened before record creation or client fetch
            print("Failed before database record could be created or updated.")
            
    finally:
        if generated_email_record and generated_email_record.status == 'processing':
            # If loop finished somehow without completing or failing explicitly
            print("Warning: Pipeline finished unexpectedly in 'processing' state.")
            generated_email_record.status = 'unknown_error'
            generated_email_record.save()
            
        if db and not db.is_closed():
            db.close()
            print("Database connection closed.")

if __name__ == "__main__":
    print("Starting email generation pipeline...")
    
    # --- Define recipient details --- 
    # For MVP, hardcode the target recipient and client ID
    # In a real app, this would come from user input, a queue, API call, etc.
    target_client_id = 1 # Assuming the sample client created by setup_database.py is ID 1
    target_recipient_name = "Alex Phillips"
    target_recipient_title = "Director of E-commerce"
    target_recipient_company = "Coca-Cola"
    
    run_pipeline_for_recipient(
        client_id=target_client_id,
        recipient_name=target_recipient_name,
        recipient_title=target_recipient_title,
        recipient_company=target_recipient_company
    )
    
    print("Pipeline finished.") 