"""Explore phrasing before video search. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataYouTubeSuggestions

tool = FlashDataYouTubeSuggestions()
arguments = {"query": "python async", "language": "en", "region": "US"}
result = tool.invoke(arguments)
for phrase in result["results"][0]:
    print(phrase)
