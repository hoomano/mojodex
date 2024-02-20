# Google search tool

## Definition
> ```json
> {
>     "name": "google_search",
>     "definition": "Make some research on Google"
> }
> ```

## Usage
Used in "Qualify Lead" with usage:
```
"Use this tool to search for information that could help you qualify the lead.\n Start with a general research about the company to find its industry. A google query made only of the company name is usually the best way to go at first. Make sure you spell the company name correctly. Then look for the company's industry trends, news, and recent events."
```

## Code
Google Search Tool uses the [SERP API](https://serpapi.com/) to search Google.

A SERP API KEY is required to use this tool. It is stored in the environment variable `SERP_API_KEY`.

### n_total_usages
The tool can be used to make 3 queries by execution (defined in `background/app/models/task_tool_execution/tools/google_search.py` as `n_total_usages`). This allows the assistant to go step by step deeper in the information gathering process.

### tool_specifications
```json
{
    "query": "<query you want to search on Google. It has to be really short, mainly keywords and precise. Only one information to search.>",
    "gl":"<Country to use for the Google search. Two-letter country code>",
    "hl":"<Language to use for the Google search. Two-letter language code.>"
}
```

### run_tool
The `run_tool` method executes 1 query from given parameters.
As it is coded, it:
- Grasps 5 first results from Google search
- Keep preview results if any relevant is available

```python
[...]
if "answer_box" in res.keys() and "answer" in res["answer_box"].keys():
    toret = res["answer_box"]["answer"]
elif "answer_box" in res.keys() and "snippet" in res["answer_box"].keys():
    toret = res["answer_box"]["snippet"]
elif "answer_box" in res.keys() and "snippet_highlighted_words" in res["answer_box"].keys():
    toret = res["answer_box"]["snippet_highlighted_words"][0]
elif "sports_results" in res.keys() and "game_spotlight" in res["sports_results"].keys():
    toret = res["sports_results"]["game_spotlight"]
elif "shopping_results" in res.keys() and "title" in res["shopping_results"][0].keys():
    toret = res["shopping_results"][:3]
elif "knowledge_graph" in res.keys() and "description" in res["knowledge_graph"].keys():
    toret = res["knowledge_graph"]["description"]
[...]
```


- Keep title, snippet and links for others

```python
[...]
elif "organic_results" in res.keys():
    toret = []
    for organic_result in res["organic_results"]:
        result = {}
        if "title" in organic_result.keys():
            result["title"] = organic_result["title"]
        if "snippet" in organic_result.keys():
            result["snippet"] = organic_result["snippet"]
        if "link" in organic_result.keys():
            result["link"] = organic_result["link"]
        toret.append(result)
[...]
```

- For those links:
    - ignores pdf and other download files as they are usually too long to fit prompt context window.
    - scrap content of the page from link using a dedicated prompt and extract relevant information regarding query from it.

## Results

Result of a query is made of a source link if any and the summary of relevant information as scrapped from the page:
```json
[
    {
        "source": "https://www.source.com",
        "extracted": "Relevant information from the page"
    }
]
```

The results of each query are then concatenated and passed to the assistant so that it can write a message presenting the results to the user.
