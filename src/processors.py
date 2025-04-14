from . import openai_client as ai
from . import config
from . import data_handler
from .prompts.product_description import system as pd_system, query as pd_query
from .prompts.target_description import system as td_system, query as td_query
from .prompts.baseline_email import system as be_system, query as be_query
from .prompts.summary import system as s_system, query as s_query
from .prompts.first_draft import system as fd_system, query as fd_query
from .prompts.one_shot_improvement import system as osi_system, query as osi_query
from .prompts.zero_shot_improvement import system as zsi_system, query as zsi_query
from .database.models import db, Clients, Prompts, GeneratedEmails, get_prompt_template
import traceback 

# --- Helper function for prompt formatting ---
def format_prompt(template, **kwargs):
    """Formats a prompt template string using provided kwargs."""
    try:
        # Basic check for f-string prefix - relies on setup script storing it
        if template.startswith('f"""'):
            # Eval is risky, but necessary here to render the stored f-string template.
            # Ensure templates stored in DB are safe and controlled.
            # This executes the f-string formatting.
            return eval(template, {}, kwargs)
        else:
            # Use standard .format() for non-f-string templates
            return template.format(**kwargs)
    except Exception as e:
        print(f"Error formatting prompt template: {e}")
        print(f"Template: {template[:100]}...") # Log snippet
        print(f"Args: {kwargs}")
        # Decide on fallback: raise error, return unformatted, return error message?
        # Raising error seems appropriate here to stop processing.
        raise ValueError(f"Failed to format prompt template: {e}")

# --- Product Description Generation ---

def get_product_description_from_web(product_name):
    """Generates product description by searching the web."""
    system_prompt = pd_system.SYSTEM_PROMPT_WEB
    query = pd_query.get_query_web(product_name)
    return ai.search_web(query, system_prompt)

def get_product_description_from_email(product_name):
    """Generates product description from email content."""
    email_content = data_handler.read_email(product_name)
    if not email_content:
        return None
    
    system_prompt = pd_system.SYSTEM_PROMPT_EMAIL
    query = pd_query.get_query_email(email_content)
    # Note: Using reason model as per original logic for email source
    return ai.reason(query, system_prompt) 

def generate_product_description(client, generated_email_record):
    """Fetches or generates the product description, logs to DB."""
    # Check saved data override first (for debugging)
    saved_desc = config.get_saved_data('product_description')
    if saved_desc:
        print("Using saved product description (override).")
        generated_email_record.product_description_output = saved_desc
        generated_email_record.save()
        return saved_desc

    print(f"Generating product description for client {client.client_id}...")
    description = None
    system_prompt_template = None
    query_template = None
    error = None
    stage_name_suffix = 'web' if client.product_info_source_type == 'web' else 'email'
    stage_name = f"product_description_{stage_name_suffix}"

    try:
        system_prompt_template = get_prompt_template(stage_name, 'system')
        query_template = get_prompt_template(stage_name, 'query')

        if client.product_info_source_type == 'web':
            system_prompt = format_prompt(system_prompt_template) # No args needed for this system prompt
            query = format_prompt(query_template, product_name=client.product_name)
            description = ai.search_web(query, system_prompt)
        elif client.product_info_source_type == 'email':
            email_content = data_handler.read_email(client.product_info_detail)
            if not email_content:
                raise ValueError(f"Email content not found for {client.product_info_detail}")
            system_prompt = format_prompt(system_prompt_template)
            query = format_prompt(query_template, email_content=email_content)
            description = ai.reason(query, system_prompt)
        else:
            raise ValueError(f"Unsupported product_info_source_type: {client.product_info_source_type}")

    except Exception as e:
        print(f"Error in {stage_name}: {e}")
        error = traceback.format_exc()
        description = None # Ensure description is None on error

    # Log to DB
    generated_email_record.product_description_output = description if description else f"Error: {error}"
    generated_email_record.save()

    if description:
        print(f"######### Product Description #########\n{description}")
    else:
        print(f"Failed to generate product description. Error logged.")
        # Decide if pipeline should stop on error
        raise Exception(f"Stopping pipeline: Failed product description generation. Error: {error}") 

    return description

# --- Target Description Generation ---

def generate_target_description(client, generated_email_record, product_description):
    """Generates the target description, logs to DB."""
    stage_name = 'target_description'
    saved_desc = config.get_saved_data('target_description')
    if saved_desc:
        print("Using saved target description (override).")
        generated_email_record.target_description_output = saved_desc
        generated_email_record.save()
        return saved_desc

    print(f"Generating target description for recipient {generated_email_record.recipient_name}...")
    description = None
    error = None

    try:
        if not product_description:
            raise ValueError("Product description is required.")
        
        system_prompt_template = get_prompt_template(stage_name, 'system')
        query_template = get_prompt_template(stage_name, 'query')

        system_prompt = format_prompt(system_prompt_template)
        query = format_prompt(
            query_template, 
            target_name=generated_email_record.recipient_name, 
            target_title=generated_email_record.recipient_title, 
            target_company=generated_email_record.recipient_company, 
            product_description=product_description
        )
        description = ai.search_web(query, system_prompt)

    except Exception as e:
        print(f"Error in {stage_name}: {e}")
        error = traceback.format_exc()
        description = None

    # Log to DB
    generated_email_record.target_description_output = description if description else f"Error: {error}"
    generated_email_record.save()

    if description:
        print(f"######### Target Description #########\n{description}")
    else:
        print(f"Failed to generate target description. Error logged.")
        raise Exception(f"Stopping pipeline: Failed target description generation. Error: {error}")

    return description

# --- Baseline Email Generation ---

def generate_baseline_email(client, recipient_name, product_description, target_description):
    """Generates a baseline email. Not typically logged unless needed."""
    stage_name = 'baseline_email'
    print("Generating baseline email (for comparison, not logged by default)...")
    try:
        # Note: Baseline prompt might not need system prompt based on simplified DB
        system_prompt_template = get_prompt_template(stage_name, 'system')
        query_template = get_prompt_template(stage_name, 'query')
        
        system_prompt = format_prompt(system_prompt_template) if system_prompt_template else None
        query = format_prompt(
            query_template, 
            product_description=product_description, 
            target_description=target_description, 
            target_name=recipient_name
        )
        email = ai.reason(query, system_prompt=system_prompt)
        if email:
            print(f"######### Baseline Email #########\n{email}")
        return email
    except Exception as e:
        print(f"Error generating baseline email: {e}")
        return None

# --- Information Summary Generation ---

def generate_summary(client, generated_email_record, product_description, target_description):
    """Generates a structured summary, logs to DB."""
    stage_name = 'summary'
    saved_summary = config.get_saved_data('summary')
    if saved_summary:
        print("Using saved summary (override).")
        generated_email_record.summary_output = saved_summary
        generated_email_record.save()
        return saved_summary

    print(f"Generating summary for {generated_email_record.recipient_name}...")
    summary = None
    error = None

    try:
        if not product_description or not target_description:
             raise ValueError("Product and target descriptions are required.")
             
        system_prompt_template = get_prompt_template(stage_name, 'system')
        query_template = get_prompt_template(stage_name, 'query') # Renamed from message_prompt

        # System prompt for summary might need formatting
        system_prompt = format_prompt(system_prompt_template, target_name=generated_email_record.recipient_name)
        query = format_prompt(
            query_template,
            product_description=product_description,
            target_description=target_description,
            target_name=generated_email_record.recipient_name
        )
        summary = ai.reason(query, system_prompt)

    except Exception as e:
        print(f"Error in {stage_name}: {e}")
        error = traceback.format_exc()
        summary = None

    # Log to DB
    generated_email_record.summary_output = summary if summary else f"Error: {error}"
    generated_email_record.save()

    if summary:
        print(f"######### Summary #########\n{summary}")
    else:
        print(f"Failed to generate summary. Error logged.")
        raise Exception(f"Stopping pipeline: Failed summary generation. Error: {error}")

    return summary

# --- First Draft Email Generation ---

def generate_first_draft_email(client, generated_email_record, summary):
    """Generates the first draft email, logs to DB."""
    stage_name = 'first_draft'
    saved_email = config.get_saved_data('email')
    if saved_email:
        print("Using saved first draft email (override).")
        generated_email_record.first_draft_email_output = saved_email
        generated_email_record.save()
        return saved_email

    print(f"Generating first draft email for {generated_email_record.recipient_name}...")
    email = None
    error = None

    try:
        if not summary:
            raise ValueError("Summary is required.")

        system_prompt_template = get_prompt_template(stage_name, 'system')
        query_template = get_prompt_template(stage_name, 'query')

        system_prompt = format_prompt(system_prompt_template)
        query = format_prompt(
            query_template,
            summary=summary,
            target_name=generated_email_record.recipient_name
        )
        email = ai.reason(query, system_prompt)

    except Exception as e:
        print(f"Error in {stage_name}: {e}")
        error = traceback.format_exc()
        email = None

    # Log to DB
    generated_email_record.first_draft_email_output = email if email else f"Error: {error}"
    generated_email_record.save()

    if email:
        print(f"######### First Draft Email #########\n{email}")
    else:
        print(f"Failed to generate first draft email. Error logged.")
        raise Exception(f"Stopping pipeline: Failed first draft email generation. Error: {error}")

    return email

# --- One-Shot Email Improvement ---

def generate_one_shot_email(client, generated_email_record, draft_email):
    """Improves the draft email using a reference email (one-shot), logs to DB."""
    stage_name = 'one_shot_improvement'
    saved_email = config.get_saved_data('one_shot_email')
    if saved_email:
        print("Using saved one-shot email (override).")
        generated_email_record.one_shot_email_output = saved_email
        # Don't save final selected here, let main logic decide
        generated_email_record.save()
        return saved_email

    print(f"Generating one-shot improved email for {generated_email_record.recipient_name}...")
    improved_email = None
    error = None

    try:
        if not draft_email:
            raise ValueError("Draft email is required.")
        if not client.reference_email_text:
             raise ValueError(f"Reference email text not found for client {client.client_id}")

        system_prompt_template = get_prompt_template(stage_name, 'system')
        query_template = get_prompt_template(stage_name, 'query')

        system_prompt = format_prompt(system_prompt_template)
        query = format_prompt(
            query_template,
            reference_email=client.reference_email_text,
            draft_email=draft_email
        )
        improved_email = ai.reason(query, system_prompt)

    except Exception as e:
        print(f"Error in {stage_name}: {e}")
        error = traceback.format_exc()
        improved_email = None

    # Log to DB
    generated_email_record.one_shot_email_output = improved_email if improved_email else f"Error: {error}"
    generated_email_record.save()

    if improved_email:
        print(f"######### One-shot Email #########\n{improved_email}")
    else:
        print(f"Failed to generate one-shot email. Error logged.")
        # Don't necessarily stop pipeline here, maybe fallback to zero-shot or first draft

    return improved_email

# --- Zero-Shot Email Improvement ---

def generate_zero_shot_email(client, generated_email_record, draft_email):
    """Improves the draft email using provided advice (zero-shot), logs to DB."""
    stage_name = 'zero_shot_improvement'
    saved_email = config.get_saved_data('zero_shot_email')
    if saved_email:
        print("Using saved zero-shot email (override).")
        generated_email_record.zero_shot_email_output = saved_email
        # Don't save final selected here, let main logic decide
        generated_email_record.save()
        return saved_email

    print(f"Generating zero-shot improved email for {generated_email_record.recipient_name}...")
    improved_email = None
    error = None

    try:
        if not draft_email:
            raise ValueError("Draft email is required.")
        if not client.zero_shot_advice_template:
             raise ValueError(f"Zero-shot advice template not found for client {client.client_id}")

        system_prompt_template = get_prompt_template(stage_name, 'system')
        query_template = get_prompt_template(stage_name, 'query')

        # Format the advice template from the client record
        advice = format_prompt(client.zero_shot_advice_template, target_name=generated_email_record.recipient_name)
        
        system_prompt = format_prompt(system_prompt_template)
        query = format_prompt(
            query_template,
            advice=advice, 
            draft_email=draft_email
        )
        improved_email = ai.reason(query, system_prompt)

    except Exception as e:
        print(f"Error in {stage_name}: {e}")
        error = traceback.format_exc()
        improved_email = None

    # Log to DB
    generated_email_record.zero_shot_email_output = improved_email if improved_email else f"Error: {error}"
    generated_email_record.save()

    if improved_email:
        print(f"######### Zero-shot Email #########\n{improved_email}")
    else:
        print(f"Failed to generate zero-shot email. Error logged.")

    return improved_email 