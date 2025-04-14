def get_query(target_name, target_title, target_company, product_description):
    return f"""
    Do a search on {target_name}, the {target_title} at {target_company} and give a concise description of who they are,
    highlighting key achievements in their career and challenges they are currently facing that the following product can help.

    Product Description:
    {product_description}
    """ 