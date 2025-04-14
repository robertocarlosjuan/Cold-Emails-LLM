import datetime
from peewee import (
    SqliteDatabase, Model, 
    IntegerField, CharField, TextField, DateTimeField, 
    ForeignKeyField, AutoField, DoesNotExist
)
from src import config

# Initialize the database connection
# Use DATABASE_FILE from config
db = SqliteDatabase(config.DATABASE_FILE)

class BaseModel(Model):
    """Base model class to specify the database."""
    class Meta:
        database = db

class Clients(BaseModel):
    client_id = AutoField() # Primary Key
    client_name = CharField(null=False)
    product_name = CharField(null=True)
    product_info_source_type = CharField(null=True) # 'email', 'web', 'manual'
    product_info_detail = TextField(null=True) # email file name, web url, features
    reference_email_text = TextField(null=True)
    zero_shot_advice_template = TextField(null=True)
    created_utc = DateTimeField(default=datetime.datetime.utcnow)

class Prompts(BaseModel):
    prompt_id = AutoField() # Primary Key
    # e.g., 'product_description_web', 'target_description', 'summary'
    stage_name = CharField(null=False) 
    prompt_type = CharField(null=False) # 'system' or 'query'
    prompt_template = TextField(null=False) # Can contain f-string style placeholders like {var}
    created_utc = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        # Ensure only one active prompt per stage/type for this simple model
        indexes = (
            (('stage_name', 'prompt_type'), True), # Unique constraint
        )

class GeneratedEmails(BaseModel):
    output_id = AutoField() # Primary Key
    client = ForeignKeyField(Clients, backref='generated_emails', null=False)
    recipient_name = CharField(null=False)
    recipient_title = CharField(null=True)
    recipient_company = CharField(null=True)
    generation_timestamp_utc = DateTimeField(default=datetime.datetime.utcnow)
    
    # --- Stage Outputs ---
    product_description_output = TextField(null=True)
    target_description_output = TextField(null=True)
    summary_output = TextField(null=True)
    first_draft_email_output = TextField(null=True)
    one_shot_email_output = TextField(null=True)
    zero_shot_email_output = TextField(null=True)
    
    # --- Final Selection ---
    final_selected_email_type = CharField(null=True) # 'one_shot', 'zero_shot', 'first_draft'
    final_selected_email_output = TextField(null=True)
    
    # --- Status ---
    status = CharField(default='processing') # 'processing', 'completed', 'failed'
    error_message = TextField(null=True)

def get_prompt_template(stage_name, prompt_type):
    """Helper function to retrieve the current active prompt template."""
    try:
        prompt = Prompts.get(Prompts.stage_name == stage_name, Prompts.prompt_type == prompt_type)
        return prompt.prompt_template
    except DoesNotExist:
        print(f"Error: Prompt not found in DB for stage '{stage_name}', type '{prompt_type}'.")
        # Consider raising an exception or returning a default/error string
        raise ValueError(f"Prompt not found for {stage_name}/{prompt_type}") 