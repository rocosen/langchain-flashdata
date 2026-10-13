"""Compare merchant result snapshots. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataGoogleShopping

tool = FlashDataGoogleShopping()
arguments = {"query": "USB C docking station", "gl": "us", "num": 5}
result = tool.invoke(arguments)
for item in result["results"][0].get("shopping", []):
    print(item.get("title"), item.get("source"), item.get("price"), item.get("link"))
