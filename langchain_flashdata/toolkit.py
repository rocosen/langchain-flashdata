"""Choose task-scoped tools with shared credentials."""

from langchain_core.tools import BaseTool, BaseToolkit
from pydantic import ConfigDict, Field, SecretStr, field_validator

from langchain_flashdata.tools import (
    SOURCE_TOOLS,
    FlashDataDownloadJob,
    FlashDataDownloadResult,
    _key_from_env,
)


class FlashDataToolkit(BaseToolkit):
    """Select sources explicitly; the default preserves the original four tools."""

    model_config = ConfigDict(hide_input_in_errors=True)
    api_key: SecretStr = Field(default_factory=_key_from_env, exclude=True, repr=False)
    sources: tuple[str, ...] = (
        "google_search",
        "youtube_search",
        "youtube_metadata",
        "youtube_transcript",
    )
    download_storage: SecretStr | None = Field(default=None, exclude=True, repr=False)

    @field_validator("sources")
    @classmethod
    def _validate_sources(cls, values):
        if not values or len(values) != len(set(values)) or set(values) - SOURCE_TOOLS.keys():
            raise ValueError("Select unique, supported FlashData sources.")
        return values

    def get_tools(self) -> list[BaseTool]:
        """Return only selected data tools, plus readers when download is selected."""
        tools = []
        for source in self.sources:
            settings = {"api_key": self.api_key}
            if source == "youtube_download" and self.download_storage is not None:
                settings["download_storage"] = self.download_storage
            tools.append(SOURCE_TOOLS[source](**settings))
        if "youtube_download" in self.sources:
            tools.extend(
                [
                    FlashDataDownloadJob(api_key=self.api_key),
                    FlashDataDownloadResult(api_key=self.api_key),
                ]
            )
        return tools
