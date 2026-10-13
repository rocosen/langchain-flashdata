"""Shortlist videos by topic. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataYouTubeSearch

tool = FlashDataYouTubeSearch()
arguments = {
    "query": "LangGraph tutorial",
    "max_results": 5,
    "filters": {"type": "video", "subtitles": True},
}
result = tool.invoke(arguments)
for item in result["results"][0].get("results", []):
    print(item.get("videoId"), item.get("title"), item.get("channel"))
