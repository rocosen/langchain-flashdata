"""Find citable web results for an agent. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataGoogleSearch

tool = FlashDataGoogleSearch()
arguments = {"query": "LangGraph durable execution", "num": 3, "gl": "us", "hl": "en"}
result = tool.invoke(arguments)
for item in result["results"][0].get("organic", []):
    print(item.get("title"), item.get("link"), item.get("snippet"))
