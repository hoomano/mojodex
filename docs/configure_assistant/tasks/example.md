# Task creation example

## Crafting the Perfect Sales Pitch: A Mojodex Tale

### Context
In the bustling heart of a startup district, I recently crossed paths with Mia, a passionate **salesperson** navigating the turbulent seas of entrepreneurship. Over coffee and conversations, Mia confided in me her struggles. Amidst the dynamic landscape of ever-evolving offers, she found herself grappling with a persistent dilemma - how to keep her pitch razor-sharp without succumbing to the dreaded "white page syndrome."

### Understanding the Process
As we delved deeper, Mia unveiled the anatomy of her sales pitch:

- **Identifying the Problem**: Articulating the core issue her company and product address.

- **Presenting the Solution**: Conveying how her offering tackles the identified problem.

- **Highlighting Uniqueness**: Showcasing what sets her company and product apart from competitors.

- **Defining the Target Market**: Painting a vivid picture of the ideal customer.

Additionally, Mia emphasized the **need for brevity**, stressing that her pitch must be succinct yet captivating, always **concluding with a compelling question** to spark dialogue.

### Crafting the Task
Eager to assist Mia in her quest for the perfect pitch, I set out to create a tailored solution on Mojodex. Drawing from our conversation, I meticulously crafted a task specification:

#### Task Specification
```
{
    "platforms": [
        "mobile",
        "webapp"
    ],
    "predefined_actions": [],
    "task_displayed_data": [
        {
            "language_code": "en",
            "name_for_user": "1 Minute Pitch",
            "definition_for_user": "Prepare a 1 minute pitch to briefly present your company and product",
            "json_input": [
                {
                    "input_name": "company_and_product_informations",
                    "description_for_user": "Let's make a great pitch!",
                    "description_for_system": "Information about the company and product (ex: company background, product, target market, unique selling points)",
                    "placeholder": "What problem are you solving? How do you solve it? What makes you different from other solutions? Who is your ideal customer?",
                    "type": "text_area"
                }
            ]
        }
    ],
    "name_for_system": "create_one_minute_pitch",
    "definition_for_system": "The user needs assistance to create a 1-minute pitch for presenting their company and product",
    "final_instruction": "Write a 1-minute pitch to briefly present the company and product; finish with a question to engage conversation.",
    "output_format_instruction_title": "1 MINUTE PITCH - COMPANY NAME",
    "output_format_instruction_draft": "PITCH CONTENT",
    "output_type": "document",
    "icon": "🎤",
    "infos_to_extract": [
        {
            "info_name": "problem_solved",
            "description": "The problem the company and product are solving"
        },
        {
            "info_name": "solution",
            "description": "How the company and product solve the problem"
        },
        {
            "info_name": "unique_selling_points",
            "description": "What makes the company and product different from other solutions"
        },
        {
            "info_name": "target_market",
            "description": "The target market represented by an ideal customer description"
        }
    ]
}
```

> Note how:
>
> - The **infos_to_extract** lists all the information Mia - and now her assistant - needs to craft her pitch.
>
> - The **final_instruction** provides a clear directive to the assistant, ensuring the pitch is concise and ends with a question as Mia requested.
>
> - The user data are clear so that Mia easily finds the task and knows what to expect.

### Conclusion

With the task configuration complete, I eagerly shared it with Mia through Mojodex. 

Now armed with a personalized tool perfectly aligned with her needs, Mia can effortlessly craft compelling pitches, leaving behind the days of writer's block and embracing the art of persuasive communication with confidence.







