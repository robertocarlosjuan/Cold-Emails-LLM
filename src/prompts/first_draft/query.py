def get_query(summary, target_name):
    return f"""
    {summary}

    Now write an email to {target_name} using the information above. Follow the general structure below:

    NOTE: Write sentences of varying length, but no more than 15 words each.
    NOTE: Write like you talk.
    NOTE: Do not use em-dash.
    NOTE: Vary the number of sentences in each paragraph. Use no more than 4 sentences for each paragraph.
    NOTE: Do not use links.
    NOTE: Get to the point. FOLLOW the general structure below.
    NOTE: Use varying active and passive voice.
    NOTE: Don't sell too hard. Be humble about your product. You are just seeking to see if recipient would be interested in a demo.

    NOTE: The general flow of email is:
    1) Start with a short description of the {target_name}'s work,
    2) Describe the challenges the receiver thinks they have in relation to the work done by {target_name},
    3) Describe how the product could help,
    4) Describe the customer testimonial,
    5) Ask for a quick chat.


    Hey {target_name},

    [I came across/I saw] [short description of {target_name}'s work] [relate briefly to {target_name}'s challenges].

    [Specific example of what {target_name}'s challenges would look like on the day to day] [relate to Product]

    [How product can help] [Relate to customer testimonial]

    [Ask for a quick chat]
    """ 