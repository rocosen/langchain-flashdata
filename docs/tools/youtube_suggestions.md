# YouTube Autocomplete for LangChain and LangGraph

Collect autocomplete phrases for a topic prefix to help a user refine a search. Preserve the returned suggestions as phrases; selecting one for a video query is a separate operation.

**Task:** Explore phrasing before video search. This tool calls only `youtube_suggestions` through `FlashDataYouTubeSuggestions` in `langchain-flashdata` 0.2.0.

[YouTube Autocomplete API fields and limits](https://flashdata.dev/docs/sources/youtube_suggestions?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=youtube_suggestions-tool) · [API pricing](https://flashdata.dev/pricing) · [All task guides](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/README.md)

## Install and authenticate

```bash
pip install 'langchain-flashdata==0.2.0'
export FLASHDATA_API_KEY='YOUR_FLASHDATA_API_KEY'
```

Create an account at [FlashData](https://flashdata.dev/signup), create an API key in the console, enable this source and fund the account. **The MIT Python package is free; FlashData API calls are paid and consume credits.** Check the current source rate and your account limits before running this example. LangChain is an open-source framework; optional model, hosting and LangSmith services can have their own charges.

## Explore phrasing before video search

```python
from langchain_flashdata import FlashDataYouTubeSuggestions

tool = FlashDataYouTubeSuggestions()
arguments = {"query": "python async", "language": "en", "region": "US"}
result = tool.invoke(arguments)
for phrase in result["results"][0]:
    print(phrase)
```

[Runnable script](https://github.com/rocosen/langchain-flashdata/blob/main/examples/tasks/youtube_suggestions.py). All data tools support `await tool.ainvoke(arguments)` in an async function with the same inputs and response contract. Queries are trimmed and limited to 1–2,000 characters. Video tools accept an 11-character ID or a supported YouTube URL and send only the ID.

## Interpret the output

`results[0]` is directly an array of strings. There is no nested `suggestions` object and no video metadata in this response.

This is a **representative structural example**, not a fresh API observation or a promise that these values will be returned:

```json
{
  "source": "youtube_suggestions",
  "status": "done",
  "results": [
    [
      "python async tutorial",
      "python async await"
    ]
  ]
}
```

`language` defaults to en and `region` to US. An empty array is a valid outcome. Suggestions are not search-volume measurements, popularity scores or guaranteed keywords.

## Use in a LangGraph tool node

Install `langchain-flashdata[examples]` to include LangGraph. The following continues from the `tool` and `arguments` setup above; run it **instead of** `tool.invoke(arguments)` when testing a graph, because each execution performs a paid query.

```python
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

builder = StateGraph(MessagesState)
builder.add_node("tools", ToolNode([tool], handle_tool_errors=False))
builder.add_edge(START, "tools")
builder.add_edge("tools", END)
graph = builder.compile()
message = AIMessage(content="", tool_calls=[{"name": tool.name, "args": arguments, "id": "task-1"}])
output = graph.invoke({"messages": [message]})
print(output["messages"][-1].content)
```

For a model-driven agent, pass this same tool to `create_agent`. A useful task prompt is: “Get YouTube autocomplete suggestions for python async in English and the US region. Present the phrases without assigning search-volume estimates.” Apply a tool-call budget and let failures stop execution. Treat returned content as evidence, not instructions. Model-provider charges are separate.

## Handle failures and costs

Inputs are validated before submission. Realtime calls return the complete API envelope, including available usage fields. No paid request is retried automatically. If a timeout or broken response leaves the outcome unknown, check FlashData Jobs before submitting again. Do not add automatic retries or graph replay around paid tool calls. An unavailable optional field should remain unknown.

See [YouTube Autocomplete documentation](https://flashdata.dev/docs/sources/youtube_suggestions?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=youtube_suggestions-tool) for the current contract, [data handling](https://github.com/rocosen/langchain-flashdata/blob/main/PRIVACY.md) for credential and result flow, or contact support@flashdata.dev.
