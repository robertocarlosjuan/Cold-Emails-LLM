def get_message_prompt(product_description, target_description, target_name):
    return f"""
    Product Description:
    {product_description}

    Details about {target_name}:
    {target_description}

    Identify the following information and answer in the format with the header. Keep each answer to 1 sentence, written in simple english only using jargons where absolutely necessary:
    1. {target_name}'s work: {target_name}'s recent work and where it was publicised
    2. {target_name}'s challenges: {target_name}'s challenges relevant to the product
    3. Product: 1 sentence description of product that is relevant to {target_name}'s challenges
    4. Customer testimonial: Customer testimonial including what it was used for, the benefit the product provided with quantitative result.
    """ 