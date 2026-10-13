"""Collect a larger video discovery set. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataYouTubeExtendedSearch

tool = FlashDataYouTubeExtendedSearch()
arguments = {
    "query": "urban farming",
    "max_results": 50,
    "filters": {"type": "video", "upload_date": "this_month", "sort_by": "view_count"},
}
result = tool.invoke(arguments)
page = result["results"][0]
print("Returned:", len(page.get("results", [])))
for item in page.get("results", []):
    print(item.get("videoId"), item.get("title"), item.get("viewCount"))
