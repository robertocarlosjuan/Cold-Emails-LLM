def get_query(advice, draft_email):
    return f"""
ADVICE:
{advice}

DRAFT EMAIL:
{draft_email}

Task:
Rewrite the email to incorporate all the points from the advice.
Keep a helpful, personal tone, a simple structure, and a single clear call to action.
""" 