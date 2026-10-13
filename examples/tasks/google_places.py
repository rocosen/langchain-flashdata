"""Find local business candidates. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataGooglePlaces

tool = FlashDataGooglePlaces()
arguments = {"query": "coffee shops in Cambridge UK", "gl": "gb", "num": 5}
result = tool.invoke(arguments)
for item in result["results"][0].get("places", []):
    print(item.get("title"), item.get("address"), item.get("rating"), item.get("website"))
