# Data handling

Realtime tools send the validated query, video ID or channel handle, selected
parameters and an `X-API-Key` header to `https://data.flashdata.dev/v1/queries/realtime`.
Download submits to `https://data.flashdata.dev/v1/queries`, including the customer
storage destination and credentials configured by your application. FlashData uses
those credentials to deliver media to that storage provider.

Download readers call `https://api.flashdata.dev/v2/jobs` and `/v2/api-access`.
Completed result JSON is fetched from the trusted result origin reported by
FlashData, using a signed URL and **without** the API key. The client does not
fetch the delivered media file, write results/credentials to disk, follow arbitrary
redirects or retry paid requests. Authenticated requests include a random request
ID and package version user agent. Result JSON reads are limited to 20 MiB.

FlashData handles requests according to its [privacy policy](https://flashdata.dev/legal/privacy).
Queries consume credits according to your account and the current pricing.

If you use the agent example, your question and tool results are also sent to
your configured model provider. LangChain tracing, callbacks, or application
logging can retain inputs/results if you enable them. Configure those services
according to your own data requirements. Credentials are excluded from tool
argument schemas and serialization; do not log your environment or raw HTTP headers.

The optional MCP example connects to `https://data.flashdata.dev/mcp` with the
same header. It only discovers tools and prints their names.

Support: support@flashdata.dev.
