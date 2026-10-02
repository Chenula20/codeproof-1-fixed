# Local desktop API, version 1

This additive desktop-facing contract is implemented in `backend/`. The existing
AI coaching contract and its Python request/response models are unchanged.
The cross-component integration was explicitly approved for this task.

Run a single backend process on `127.0.0.1:8000`. Every `/v1` request requires
`Authorization: Bearer <CODEPROOF_TOKEN>`. Tokens must contain at least 32
characters. `python -m backend` generates a session token if none is configured.
Do not bind this service to a network interface. Browser Origin requests are
rejected; there is no browser CORS access. Desktop clients do not follow redirects.

| Method | Route | Input | Output |
| --- | --- | --- | --- |
| GET | `/health` | none | status and API version |
| GET | `/v1/capabilities` | none | AI configuration, Docker executable availability, runners |
| POST | `/v1/sessions` | `path` (empty = bundled sample) | SessionView |
| DELETE | `/v1/sessions/{id}` | none | closes session and deletes its temporary copy |
| POST | `/v1/sessions/{id}/analysis` | `use_ai` | SessionView |
| POST | `/v1/sessions/{id}/challenge` | `issue`, `target_file` | SessionView |
| POST | `/v1/sessions/{id}/hint` | empty object | SessionView |
| POST | `/v1/sessions/{id}/explanation` | `explanation` | SessionView |
| POST | `/v1/sessions/{id}/patch` | empty object | SessionView |
| POST | `/v1/sessions/{id}/validation` | `runner` | SessionView |
| GET | `/v1/sessions/{id}/report` | none | structured review evidence |

`backend/models.py` is the source of truth for field names and limits. The Dart
models in `desktop/lib/domain/workspace.dart` mirror SessionView. Each operation
returns the authoritative complete session state. Mutations are serialized per
session. The client disables duplicate operations while an operation is pending.

Phases: `analyzed → investigating → review → applied → validated`. A rejected
explanation stays in investigating. Validation may run before a patch, but only
an applied patch with passing test evidence and an unchanged original snapshot
can enter validated. Validation statuses are `not_run`, `passed`, `failed`,
`unavailable`, and `timeout`.

AI is opt-in per session. An explicit desktop confirmation precedes the first
external transmission. Set `OPENROUTER_API_KEY` and `CODEPROOF_MODEL` only in the
backend environment. No API key is sent to or persisted by Flutter. Existing
ProjectAnalyzer, HintEngine, ExplanationEvaluator, and PatchGenerator services
are reused. Absolute project roots are replaced before AI receives a snapshot.
Provider failures return generic errors without exposing provider exceptions.

Practice coaching is deterministic. Arbitrary real projects receive local
inspection without a key; AI coaching and generated patches require AI analysis
to be enabled before investigation. Only the bundled sample has a predefined
fault injection. Real-project investigations use a developer-described issue.

Session storage is ephemeral, with at most eight active sessions. Closing a
session or shutting down the backend removes its temporary copy. When opening a
new session, idle sessions older than two hours are reclaimed. Crash recovery and
persistent workspaces are not implemented.
