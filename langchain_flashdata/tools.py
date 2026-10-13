"""FlashData tools implementing LangChain's BaseTool interface."""

import os
from typing import Any, ClassVar

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from langchain_flashdata import _client
from langchain_flashdata._inputs import (
    DownloadJobInput,
    GoogleInput,
    GoogleSearchInput,
    YouTubeCaptionsInput,
    YouTubeChannelInput,
    YouTubeDownloadInput,
    YouTubeExtendedSearchInput,
    YouTubeMetadataInput,
    YouTubeSearchInput,
    YouTubeSuggestionsInput,
    YouTubeTrainabilityInput,
    YouTubeTranscriptInput,
)
from langchain_flashdata._storage import storage_config


def _key_from_env() -> SecretStr:
    value = os.environ.get("FLASHDATA_API_KEY", "").strip()
    if not value:
        raise ValueError("Set FLASHDATA_API_KEY or pass api_key when constructing the tool.")
    return SecretStr(value)


class _FlashDataTool(BaseTool):
    model_config = ConfigDict(hide_input_in_errors=True)
    api_key: SecretStr = Field(default_factory=_key_from_env, exclude=True, repr=False)
    source: ClassVar[str]

    @field_validator("api_key")
    @classmethod
    def _validate_key(cls, value: SecretStr) -> SecretStr:
        key = value.get_secret_value().strip()
        if not key:
            raise ValueError("FlashData API key must not be empty.")
        return SecretStr(key)

    def _payload(self, values: dict[str, Any]) -> dict[str, Any]:
        # Apply defaults again: BaseTool only forwards explicitly supplied arguments.
        params = (
            self.get_input_schema()
            .model_validate(values)
            .model_dump(exclude_none=True, by_alias=True)
        )
        primary = next(field for field in ("query", "video_id", "handle") if field in params)
        return {"source": self.source, primary: params.pop(primary), "params": params}

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        return _client.query(self.api_key, self._payload(kwargs))

    async def _arun(self, **kwargs: Any) -> dict[str, Any]:
        return await _client.aquery(self.api_key, self._payload(kwargs))


class FlashDataGoogleSearch(_FlashDataTool):
    """Search Google for current web results with source URLs."""

    name: str = "flashdata_google_search"
    description: str = (
        "Search Google for current web results, titles, snippets and source URLs. "
        "Uses FlashData credits. Do not repeat a query after an unknown outcome; check Jobs first."
    )
    args_schema: type[BaseModel] = GoogleSearchInput
    source: ClassVar[str] = "google_search"


class FlashDataYouTubeSearch(_FlashDataTool):
    """Search YouTube videos."""

    name: str = "flashdata_youtube_search"
    description: str = (
        "Find YouTube videos by search query. Returns video IDs and available video metadata. "
        "Uses FlashData credits. Do not repeat a query after an unknown outcome; check Jobs first."
    )
    args_schema: type[BaseModel] = YouTubeSearchInput
    source: ClassVar[str] = "youtube_search"


class FlashDataYouTubeMetadata(_FlashDataTool):
    """Retrieve metadata for a YouTube video."""

    name: str = "flashdata_youtube_metadata"
    description: str = (
        "Get YouTube video metadata by ID or URL, with optional chapters and format metadata. "
        "Uses FlashData credits. Do not repeat a query after an unknown outcome; check Jobs first."
    )
    args_schema: type[BaseModel] = YouTubeMetadataInput
    source: ClassVar[str] = "youtube_metadata"


class FlashDataYouTubeTranscript(_FlashDataTool):
    """Retrieve captions for a YouTube video."""

    name: str = "flashdata_youtube_transcript"
    description: str = (
        "Get a YouTube transcript with timestamped segments by video ID or URL. Specify language "
        "and auto=true for automatic captions or auto=false for manual captions. "
        "No implicit fallback. "
        "Uses FlashData credits. Do not repeat a query after an unknown outcome; check Jobs first."
    )
    args_schema: type[BaseModel] = YouTubeTranscriptInput
    source: ClassVar[str] = "youtube_transcript"


class FlashDataGoogleNews(_FlashDataTool):
    """Find news coverage with publication links and dates."""

    name: str = "flashdata_google_news"
    description: str = (
        "Search Google News by topic, country, language and time filter. Returns headlines, "
        "links, publishers and available dates/snippets, not article full text. "
        "Uses FlashData credits."
    )
    args_schema: type[BaseModel] = GoogleInput
    source: ClassVar[str] = "google_news"


class FlashDataGoogleImages(_FlashDataTool):
    """Discover original image URLs and their source pages."""

    name: str = "flashdata_google_images"
    description: str = (
        "Search Google Images for image URLs, thumbnails, dimensions and source pages. "
        "Does not download images or grant reuse rights. Uses FlashData credits."
    )
    args_schema: type[BaseModel] = GoogleInput
    source: ClassVar[str] = "google_images"


class FlashDataGoogleShopping(_FlashDataTool):
    """Compare product search snapshots and merchant links."""

    name: str = "flashdata_google_shopping"
    description: str = (
        "Search Google Shopping for products, merchants and available price/rating fields. "
        "A search snapshot does not guarantee stock or checkout price. Uses FlashData credits."
    )
    args_schema: type[BaseModel] = GoogleInput
    source: ClassVar[str] = "google_shopping"


class FlashDataGoogleVideos(_FlashDataTool):
    """Find video pages across websites through Google."""

    name: str = "flashdata_google_videos"
    description: str = (
        "Search Google Videos across websites for video titles, links and available durations "
        "and source information. Different from YouTube-only search. Uses FlashData credits."
    )
    args_schema: type[BaseModel] = GoogleInput
    source: ClassVar[str] = "google_videos"


class FlashDataGooglePlaces(_FlashDataTool):
    """Look up local businesses and available address/contact fields."""

    name: str = "flashdata_google_places"
    description: str = (
        "Search Google Places for local businesses, addresses, coordinates and available ratings "
        "or contact details. Phone numbers may be absent. Uses FlashData credits."
    )
    args_schema: type[BaseModel] = GoogleInput
    source: ClassVar[str] = "google_places"


class FlashDataYouTubeExtendedSearch(_FlashDataTool):
    """Request larger YouTube result sets with structured filters."""

    name: str = "flashdata_youtube_search_extended"
    description: str = (
        "Search YouTube with an extended limit of up to 700 requested results and optional "
        "filters. Actual count may be lower. Uses a separate FlashData source and credit rate."
    )
    args_schema: type[BaseModel] = YouTubeExtendedSearchInput
    source: ClassVar[str] = "youtube_search_extended"


class FlashDataYouTubeCaptions(_FlashDataTool):
    """Read existing uploader caption tracks in a chosen language."""

    name: str = "flashdata_youtube_captions"
    description: str = (
        "Retrieve YouTube captions with timestamped segments. Defaults to manual uploader "
        "captions (auto=false), language en. No transcription, translation or automatic "
        "fallback. Uses FlashData credits."
    )
    args_schema: type[BaseModel] = YouTubeCaptionsInput
    source: ClassVar[str] = "youtube_captions"


class FlashDataYouTubeTrainability(_FlashDataTool):
    """Inspect Creative Commons license-label metadata."""

    name: str = "flashdata_youtube_trainability"
    description: str = (
        "Inspect YouTube license metadata for a Creative Commons label. The trainability "
        "source does not read creator training settings or grant training permission. "
        "Uses FlashData credits."
    )
    args_schema: type[BaseModel] = YouTubeTrainabilityInput
    source: ClassVar[str] = "youtube_trainability"


class FlashDataYouTubeChannel(_FlashDataTool):
    """Snapshot a channel and its recent videos."""

    name: str = "flashdata_youtube_channel"
    description: str = (
        "Get YouTube channel data by handle and up to 100 requested recent videos. "
        "Statistics and some fields may be unavailable. Uses FlashData credits."
    )
    args_schema: type[BaseModel] = YouTubeChannelInput
    source: ClassVar[str] = "youtube_channel"


class FlashDataYouTubeSuggestions(_FlashDataTool):
    """Get search-prefix autocomplete suggestions."""

    name: str = "flashdata_youtube_suggestions"
    description: str = (
        "Get YouTube autocomplete suggestions for a query prefix, language and region. "
        "Returns phrases, not videos or search-volume estimates. Uses FlashData credits."
    )
    args_schema: type[BaseModel] = YouTubeSuggestionsInput
    source: ClassVar[str] = "youtube_suggestions"


def _storage_from_env() -> SecretStr:
    value = os.environ.get("FLASHDATA_DOWNLOAD_STORAGE", "")
    if not value.strip():
        raise ValueError("Set FLASHDATA_DOWNLOAD_STORAGE or pass download_storage JSON.")
    return SecretStr(value)


class FlashDataYouTubeDownload(_FlashDataTool):
    """Submit media delivery to an application-configured storage destination."""

    name: str = "flashdata_youtube_download"
    description: str = (
        "Submit a paid YouTube video/audio download to configured customer cloud storage. "
        "Returns an asynchronous job ID, not a completed file. Save the ID and use download "
        "job readers; never resubmit just because it is pending. Billed on delivered bytes."
    )
    args_schema: type[BaseModel] = YouTubeDownloadInput
    source: ClassVar[str] = "youtube_download"
    download_storage: SecretStr = Field(default_factory=_storage_from_env, exclude=True, repr=False)

    @field_validator("download_storage")
    @classmethod
    def _validate_storage(cls, value: SecretStr) -> SecretStr:
        storage_config(value.get_secret_value())
        return value

    def _payload(self, values: dict[str, Any]) -> dict[str, Any]:
        payload = super()._payload(values)
        payload["params"]["storage"] = storage_config(self.download_storage.get_secret_value())
        return payload

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        return _client.submit_download(self.api_key, self._payload(kwargs))

    async def _arun(self, **kwargs: Any) -> dict[str, Any]:
        return await _client.asubmit_download(self.api_key, self._payload(kwargs))


class FlashDataDownloadJob(_FlashDataTool):
    """Read status of an existing download job without submitting a query."""

    name: str = "flashdata_download_job"
    description: str = (
        "Read an existing YouTube download job by ID. No new paid query is submitted."
    )
    args_schema: type[BaseModel] = DownloadJobInput
    source: ClassVar[str] = "youtube_download"

    def _run(self, job_id: str) -> dict[str, Any]:
        return _client.get_download_job(self.api_key, job_id)

    async def _arun(self, job_id: str) -> dict[str, Any]:
        return await _client.aget_download_job(self.api_key, job_id)


class FlashDataDownloadResult(FlashDataDownloadJob):
    """Read delivery metadata after completion; never download media into the agent."""

    name: str = "flashdata_download_result"
    description: str = (
        "Read completed YouTube download delivery metadata, including file URL and size. "
        "Returns status while unfinished. No new query; does not fetch the media file."
    )

    def _run(self, job_id: str) -> dict[str, Any]:
        return _client.get_download_result(self.api_key, job_id)

    async def _arun(self, job_id: str) -> dict[str, Any]:
        return await _client.aget_download_result(self.api_key, job_id)


SOURCE_TOOLS = {
    tool.source: tool
    for tool in (
        FlashDataGoogleSearch,
        FlashDataGoogleNews,
        FlashDataGoogleImages,
        FlashDataGoogleShopping,
        FlashDataGoogleVideos,
        FlashDataGooglePlaces,
        FlashDataYouTubeSearch,
        FlashDataYouTubeExtendedSearch,
        FlashDataYouTubeMetadata,
        FlashDataYouTubeTranscript,
        FlashDataYouTubeCaptions,
        FlashDataYouTubeTrainability,
        FlashDataYouTubeChannel,
        FlashDataYouTubeSuggestions,
        FlashDataYouTubeDownload,
    )
}
