"""Find image candidates with source pages. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataGoogleImages

tool = FlashDataGoogleImages()
arguments = {"query": "solar panel installation diagram", "num": 5}
result = tool.invoke(arguments)
for item in result["results"][0].get("images", []):
    print(item.get("imageUrl"), item.get("imageWidth"), item.get("imageHeight"), item.get("link"))
