# [Experimental] Mistral AI

!!! warning
    This provider is experimental and not yet fully supported.

To use Mistral AI, you need to have a Mistral AI account and create an API key.

👉 [Mistral AI Platform](https://console.mistral.ai/)

## Configure Mistral AI

In your `.env` file, add the following:

```bash
MISTRAL_API_KEY=your-api-key
```

## Coverage

> For the assessment, `mistral-medium`has been tested on the most challenging task: `"ANSWER_USER"`, which is the most challenging task.
> 
> See blog post for a better understanding of the challenge: [Advanced Prompting Strategies for Digital Assistant Development](https://blog.hoomano.com/advanced-prompting-strategies-for-digital-assistant-development-b6698996954f)

The results are promising, but the full coverage is not yet available.

!!! note "Some results so far"
    
    Overall `mistral-medium` gets the idea behind the `data/prompts/tasks/run.txt` with the following limitations observed:

    - 👍 Straightforward implementation of the API
    - 👍 Follows the overall logic of the prompt
    - 😕 Big variations between runs in interpretation
    - 😕 Not reliably steerable to <tags> defined in the prompt


## Work in progress

- [X] Prepare the Mistral AI provider implementation
- [X] Run basic tests with existing prompts
- [ ] Complete the assessment on all features for `mistral-medium`
- [ ] Complete the assessment on all features for `mistral-tiny`
- [ ] Prompt Tuning: `data/prompts/*` has been crafted for GPT-4 and GPT-4 Turbo. We need to craft prompts for Mistral AI more specifically.
- [ ] Explore guardrailing strategies to steer the model to the desired output
- [ ] For non-supported features, we can explore fine-tuning the model on our own data gathered in `/data/prompts_dataset`