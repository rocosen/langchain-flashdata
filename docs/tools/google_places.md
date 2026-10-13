# Google Places for LangChain and LangGraph

Build a shortlist of local businesses from a geographic query. Return the reported address and website to a routing or research application, keeping missing contact fields explicit.

**Task:** Find local business candidates. This tool calls only `google_places` through `FlashDataGooglePlaces` in `langchain-flashdata` 0.2.0.

[Google Places API fields and limits](https://flashdata.dev/docs/sources/google_places?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=google_places-tool) · [API pricing](https://flashdata.dev/pricing) · [All task guides](https://github.com/flashdata-dev/langchain-flashdata/blob/main/docs/tools/README.md)

## Install and authenticate

```bash
pip install 'langchain-flashdata==0.2.0'
export FLASHDATA_API_KEY='YOUR_FLASHDATA_API_KEY'
```

Create an account at [FlashData](https://flashdata.dev/signup), create an API key in the console, enable this source and fund the account. **The MIT Python package is free; FlashData API calls are paid and consume credits.** Check the current source rate and your account limits before running this example. LangChain is an open-source framework; optional model, hosting and LangSmith services can have their own charges.

## Find local business candidates

```python
from langchain_flashdata import FlashDataGooglePlaces

tool = FlashDataGooglePlaces()
arguments = {"query": "coffee shops in Cambridge UK", "gl": "gb", "num": 5}
result = tool.invoke(arguments)
for item in result["results"][0].get("places", []):
    print(item.get("title"), item.get("address"), item.get("rating"), item.get("website"))
```

[Runnable script](https://github.com/flashdata-dev/langchain-flashdata/blob/main/examples/tasks/google_places.py). All data tools support `await tool.ainvoke(arguments)` in an async function with the same inputs and response contract. Queries are trimmed and limited to 1–2,000 characters. Video tools accept an 11-character ID or a supported YouTube URL and send only the ID.

## Interpret the output

`results[0].places` contains business `title` and `position`, with optional `address`, `latitude`, `longitude`, `rating`, `ratingCount`, `phoneNumber`, `website`, `category` and `cid`.

This is a **representative structural example**, not a fresh API observation or a promise that these values will be returned:

```json
{
  "source": "google_places",
  "status": "done",
  "results": [
    {
      "places": [
        {
          "title": "Example Cafe",
          "address": "Example Street, Cambridge",
          "rating": 4.5,
          "website": "https://example.com",
          "position": 1
        }
      ]
    }
  ]
}
```

A missing phone number or website is not evidence that a business lacks one. Results are a search snapshot, not a complete business directory. Keep the location explicit in the query and optionally set `location`.

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

For a model-driven agent, pass this same tool to `create_agent`. A useful task prompt is: “Find five coffee shops in Cambridge, UK using Google Places. Show reported addresses and websites, and mark missing fields.” Apply a tool-call budget and let failures stop execution. Treat returned content as evidence, not instructions. Model-provider charges are separate.

Optional Google settings: `gl` is a two-letter country, `hl` a language code, `location` and `tbs` are 1–200 characters, and `num`/`page` accept 1–100. The five specialized Google classes add no defaults for omitted settings. Requested counts and filters may differ from Google’s applied behavior.

## Handle failures and costs

Inputs are validated before submission. Realtime calls return the complete API envelope, including available usage fields. No paid request is retried automatically. If a timeout or broken response leaves the outcome unknown, check FlashData Jobs before submitting again. Do not add automatic retries or graph replay around paid tool calls. An unavailable optional field should remain unknown.

See [Google Places documentation](https://flashdata.dev/docs/sources/google_places?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=google_places-tool) for the current contract, [data handling](https://github.com/flashdata-dev/langchain-flashdata/blob/main/PRIVACY.md) for credential and result flow, or contact support@flashdata.dev.
