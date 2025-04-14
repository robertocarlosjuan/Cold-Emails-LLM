def get_query_web(product_name):
    return f"""
    Do a search on {product_name} and give a concise description of its features, its benefits and a customer testimonial with associated company name with a qualitative or quantitative result.
    """

def get_query_email(email_content):
    return f"""
    {email_content}
    Based on the email, give a concise description of the product and its benefits.
    """ 