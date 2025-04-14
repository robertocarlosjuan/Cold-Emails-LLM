import os

def read_email(email_name):
    """Reads email content from a file in the 'emails' directory."""
    # Construct the path relative to the project root or a known location
    # Assuming 'emails' directory is at the same level as 'src'
    emails_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'emails')
    file_path = os.path.join(emails_dir, f"{email_name}.txt")
    
    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: Email file not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading email file {file_path}: {e}")
        return None 