# Mistral AI

To use Mistral AI, 2 ways:

- ☝️ > [🔌 Mistral AI Platform](https://console.mistral.ai/): create a Mistral AI account and an API key.

!!! code "Configure your .env with Mistral API key"
    ```bash
    # Mistral API
    MISTRAL_API_KEY=your-api-key
    ```

- ✌️ > [📖 Azure Mistral AI](https://techcommunity.microsoft.com/t5/ai-machine-learning-blog/mistral-large-mistral-ai-s-flagship-llm-debuts-on-azure-ai/ba-p/4066996): create an Azure account and an API key.

!!! code "Azure Mistral API"
    ```bash
    # Azure Mistral API
    MISTRAL_AZURE_API_BASE=<your-azure-api-endpoint>
    MISTRAL_AZURE_API_KEY=<your-azure-api-key>
    ```


## Coverage


> For the assessment, `mistral` models have been tested on the most challenging feature: `"ANSWER_USER"` on the Mojodex platform.
> 
> See blog post for a better understanding of the challenge: [Advanced Prompting Strategies for Digital Assistant Development](https://blog.hoomano.com/advanced-prompting-strategies-for-digital-assistant-development-b6698996954f)


### `mistral-large` ✅

!!! success "🎉 full coverage"
    `mistral-large` has been tested on all features and provides a full coverage of the Mojodex cognitive functions.

### `mistral-medium` 🚧

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
- [X] Complete the assessment on all features for `mistral-large`
- [X] Complete the assessment on all features for `mistral-medium`
- [ ] Prompt Tuning: `data/prompts/*` has been crafted for GPT-4 and GPT-4 Turbo. We need to craft prompts for Mistral AI more specifically.
- [ ] Explore guardrailing strategies to steer the model to the desired output
- [ ] For non-supported features, we can explore fine-tuning the model on our own data gathered in `/data/prompts_dataset`
