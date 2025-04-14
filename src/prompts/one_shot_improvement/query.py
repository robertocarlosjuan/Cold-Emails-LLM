def get_query(reference_email, draft_email):
    return f"""
You are given the following content:

Email 1 (Reference Email):
{reference_email}

Email 2 (Draft):
{draft_email}

Please advise me on improvements to Email 2 and then provide a revised version following the guidelines in the system prompt.
""" 