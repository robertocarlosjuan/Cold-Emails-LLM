def get_query(product_description, target_description, target_name):
    return f"""Product Description:
    {product_description}

    {target_description}

    Write an email to {target_name} to sell the product.
    """ 