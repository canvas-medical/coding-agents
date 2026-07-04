# Canvas Plugin Sandbox — Full Allowlist

Canvas plugins run in a RestrictedPython sandbox. Only the imports listed below are accepted by the runner. Anything not listed will fail at deploy time with `ImportError: '<name>' is not an allowed import`.

This list mirrors the official documentation at <https://docs.canvasmedical.com/sdk/sandboxing-and-allowed-imports/> and the canonical definition in [`plugin_runner/sandbox.py`](https://github.com/canvas-medical/canvas-plugins/blob/main/plugin_runner/sandbox.py) in the open-source canvas-plugins repo.

For the compact "before you write an import" rules, see the **Sandbox** section of `CLAUDE.md`.

## Standard library modules

Only the names listed under each module are importable.

| Module | Allowed names |
|---|---|
| `__future__` | `annotations` |
| `abc` | `ABC`, `abstractmethod` |
| `base64` | `b64decode`, `b64encode` |
| `collections` | `Counter`, `defaultdict` |
| `dataclasses` | `asdict`, `astuple`, `dataclass`, `field`, `Field`, `fields`, `InitVar`, `replace` |
| `datetime` | `date`, `datetime`, `timedelta`, `timezone`, `UTC` |
| `decimal` | `Decimal` |
| `enum` | `Enum`, `StrEnum` |
| `functools` | `reduce`, `wraps` |
| `hashlib` | `sha256` |
| `hmac` | `compare_digest`, `new` |
| `http` | `HTTPStatus` |
| `json` | `dumps`, `loads` |
| `operator` | `and_` |
| `random` | `choices`, `uniform`, `randint` |
| `re` | `compile`, `DOTALL`, `findall`, `IGNORECASE`, `match`, `search`, `split`, `sub` |
| `string` | `ascii_lowercase`, `digits` |
| `time` | `time`, `sleep` |
| `typing` | `Any`, `Callable`, `cast`, `ClassVar`, `Dict`, `Final`, `Iterable`, `List`, `Literal`, `NamedTuple`, `NotRequired`, `Pattern`, `Protocol`, `Optional`, `Sequence`, `Tuple`, `Type`, `TypedDict`, `TypeGuard`, `Union` |
| `urllib` | `parse` (the submodule itself) |
| `urllib.parse` | `urlencode`, `quote` |
| `uuid` | `uuid4`, `UUID` |
| `zoneinfo` | `ZoneInfo` |

**Not on the list — these stdlib modules are blocked entirely:**
`csv`, `os`, `os.path`, `pathlib`, `pickle`, `shelve`, `shutil`, `subprocess`, `socket`, `ssl`, `xml.*` (use `defusedxml`), `http.client`, `http.cookiejar`, `urllib.request`, `urllib.error`, `urllib.robotparser`, `importlib`, `inspect`, `gc`, `signal`, `threading`, `multiprocessing`, `asyncio`, `queue`, `tempfile`, `logging` (use the `logger` builtin instead — see below), `argparse`, `configparser`.

## Third-party modules

| Module | Allowed names |
|---|---|
| `arrow` | `get`, `now`, `utcnow` |
| `dateutil` | `relativedelta` |
| `dateutil.relativedelta` | `relativedelta` |
| `defusedxml.ElementTree` | `fromstring` |
| `django.db` | `IntegrityError` |
| `django.db.transaction` | `atomic`, `on_commit`, `on_rollback` |
| `django.db.models` | `Avg`, `BigIntegerField`, `BooleanField`, `CASCADE`, `Case`, `CharField`, `Count`, `DO_NOTHING`, `DateField`, `DateTimeField`, `DecimalField`, `Exists`, `F`, `FloatField`, `ForeignKey`, `Func`, `Index`, `IntegerField`, `JSONField`, `ManyToManyField`, `Max`, `Min`, `Model`, `OneToOneField`, `OuterRef`, `Prefetch`, `Q`, `RowRange`, `SET_NULL`, `Subquery`, `Sum`, `TextField`, `UniqueConstraint`, `Value`, `ValueRange`, `When`, `Window` |
| `django.db.models.expressions` | `Case`, `Exists`, `OuterRef`, `Subquery`, `Value`, `When` |
| `django.db.models.functions` | `Coalesce`, `CumeDist`, `DenseRank`, `FirstValue`, `Lag`, `LastValue`, `Lead`, `NthValue`, `Ntile`, `PercentRank`, `Rank`, `RowNumber`, `Trim` |
| `django.db.models.query` | `Prefetch`, `QuerySet` |
| `django.utils.functional` | `cached_property` |
| `jwt` | `decode`, `encode`, `ExpiredSignatureError`, `InvalidTokenError`, `PyJWKClient` |
| `pydantic` | `BaseModel`, `conint`, `ConfigDict`, `constr`, `Field`, `RootModel`, `ValidationError` |
| `rapidfuzz` | `fuzz`, `process`, `utils` |
| `requests` | `delete`, `get`, `patch`, `post`, `put`, `request`, `RequestException`, `Response`, `Session` |

**Not on the list — frequently attempted but blocked:**
`yaml` (PyYAML), `httpx`, `aiohttp`, `urllib3`, `lxml`, `beautifulsoup4`, `numpy`, `pandas`, `boto3` (use `canvas_sdk.clients.aws`), `openai` / `anthropic` / `google-generativeai` (use `canvas_sdk.clients.llms`), `twilio` (use `canvas_sdk.clients`), `sendgrid` (use `canvas_sdk.clients`).

## Canvas SDK modules

The `canvas_sdk.*` top-level packages below are importable, and there is no per-name allowlist *within* a real module. But only submodules that actually exist resolve — a mistyped or not-yet-existing path fails at load exactly like a blocked import (`'<path>' is not an allowed import`). Confirm a submodule exists before importing it rather than assuming a plausible-looking path (e.g. a guessed `canvas_sdk.effects.<x>`) is real; `canvas validate` / `canvas install` runs the sandbox load and will report a bad path.

Django constructs are **not** re-exported from `canvas_sdk.v1.data.base` — `from canvas_sdk.v1.data.base import UniqueConstraint` (or `models`) fails at load. Import those from Django directly (`from django.db.models import UniqueConstraint`) and import the specific Canvas model classes you need from `canvas_sdk.v1.data`. (`from canvas_sdk.v1.data.base import CustomModel` is fine — that's the base class for your own models.)

- `canvas_sdk.caching`
- `canvas_sdk.commands`
- `canvas_sdk.effects`
- `canvas_sdk.events`
- `canvas_sdk.handlers`
- `canvas_sdk.protocols`
- `canvas_sdk.questionnaires`
- `canvas_sdk.templates`
- `canvas_sdk.utils`
- `canvas_sdk.v1.data` (Canvas database models — read-only)
- `canvas_sdk.value_set`
- `canvas_sdk.views`

Plus the implicit `logger` builtin (use as `from logger import log`) — this replaces `import logging`.

## Builtin functions

The sandbox exposes a curated set of builtins on top of RestrictedPython's safe defaults:

`all`, `any`, `classmethod`, `dict`, `enumerate`, `filter`, `getattr`, `hasattr`, `iter`, `list`, `map`, `max`, `min`, `next`, `property`, `reversed`, `staticmethod`, `sum`, `super`, `vars`

Plus RestrictedPython's safe basics: `bool`, `int`, `float`, `str`, `bytes`, `tuple`, `set`, `frozenset`, `len`, `range`, `zip`, `print`, type checks, etc.

**Not available:** `open`, `input`, `eval`, `exec`, `compile`, `__import__`, `globals`, `locals`, `id`, `dir`, `help`, `breakpoint`, `memoryview`.

## RestrictedPython feature limits

Even with the right imports, the sandbox rejects several normal Python constructs. These were the single largest source of failed deploys in real-customer use — every entry here cost at least one project at least one failed deploy to discover.

- **Augmented assignment on subscripts / slices.** `d["k"] += 1`, `arr[i] += 1`, `arr[i:j] += [...]` all fail with `Code is invalid: Augmented assignment of object items and slices is not allowed.` Rewrite as explicit reassignment: `d["k"] = d["k"] + 1`. Search your code for `[*] +=`, `[*] -=`, `[*] *=`, `[*] /=` — there are usually several offenders in the same file.
- **`@dataclass` is fine, including `frozen=True` and `slots=True`.** All three load and run in the sandbox (`dataclass` runs its codegen in the trusted `dataclasses` module, not under restriction).
- **No deep attribute access through dotted module paths.** Reading `pkg.sub.NAME` at the use site after `import pkg` may raise `AttributeError: "pkg.sub.NAME" is an invalid attribute name (not in ALLOWED_MODULES)`. Import the name explicitly: `from pkg.sub import NAME`. This applies to YOUR OWN plugin's modules too — always `from my_plugin.x import Y`, never `import my_plugin.x` then `my_plugin.x.Y(...)`.
- **No `setattr()` / `delattr()`.** These are blocked entirely. Re-design to use direct attribute assignment (`obj.attr = value`) or rethink the abstraction.
- **No `type(...)` as a callable on a class** for purposes other than introspection. `type(x)` to compare against a class is allowed; `type("NewClass", ...)` to create a class is blocked.
- **No `__slots__` on classes.** Plain classes work; just omit slots.
- **No underscore-prefixed string keys in dictionaries that the sandbox inspects** (e.g. `_debug_step`). Rename without the prefix.
- **No `bytearray`.** Blocked. Use `bytes` if you need binary, or build a string and encode.
- **No `random.Random()` class** (and `random` requires specific names). Only `from random import choices, uniform, randint` are exposed.
- **No bare `import datetime` / `import random` / `import uuid`.** Always `from datetime import datetime, timedelta, timezone` etc. The bare module import is rejected even though the names inside are allowed.
- **No relative imports** (`from .x import Y`). Always use the full plugin-namespace path.
- **No `exec` / `eval` / `compile` / `__import__`.**
- **No `del` on subscripts** in some restricted forms — prefer `dict.pop(k, None)`.
- **No filesystem reads.** `open(path)`, `Path(...).read_text()`, `json.load(f)` are blocked. Use `json.loads(string)` and embed content into Python source if you genuinely need static data.

### Django field types

The sandbox exposes both Django's *query builders* (`Q`, `Count`, `Sum`, `Avg`, `Prefetch`, `Case`, `When`, `Exists`, `Subquery`, `OuterRef`, `Value`) and the model *field types* used to declare `CustomModel` subclasses (`CharField`, `TextField`, `IntegerField`, `BigIntegerField`, `DateField`, `DateTimeField`, `DecimalField`, `FloatField`, `BooleanField`, `JSONField`, `ForeignKey`, `OneToOneField`, `ManyToManyField`, plus `CASCADE`/`DO_NOTHING`/`SET_NULL` and `UniqueConstraint`/`Index`) — see the `django.db.models` row above. Import them directly from `django.db.models`; `canvas validate` reports anything that isn't exposed. Note `UUIDField` is not on the list.

## Custom Data model gotchas

For plugins that declare a `custom_data` block and define `CustomModel` subclasses:

- **`CustomModel` uses `dbid` (NOT `id`) as the primary key.** `.filter(id=…)` / `.get(id=…)` will FieldError at runtime. Always `.filter(dbid=…)`. This was responsible for ~8 of the failed deploys in real-customer use.
- **Models MUST live in `<plugin>/models/`.** A flat `models.py`, a `data_models/` directory, or any other layout will silently produce no tables. The Canvas loader only scans the `models/` subdirectory.
- **`CustomModel` subclasses without a `custom_data` block in the manifest produce no tables.** The plugin loads cleanly but every query returns empty. Always declare in the manifest:
  ```json
  "custom_data": {
    "namespace": "<org>__<plugin_name>",
    "access": "read_write"
  }
  ```
- **Avoid lazy string ForeignKey refs** (`models.ForeignKey("OtherModel", ...)`). They can silently fail at table-creation time, dropping the table without an error. Use direct class refs when possible.

## Manifest configuration variables — modern `variables` schema only

Declare every configurable value in the manifest's `variables` array. The legacy `"secrets": [...]` array is **deprecated** and is the leading cause of misrendered Configuration panels — without per-variable `sensitive` metadata, Studio falls back to masking every input (URLs and IDs included), making the form unusable.

```json
"variables": [
  {"name": "SENDGRID_API_KEY", "sensitive": true},
  {"name": "DIGEST_FROM_ADDRESS"},
  {"name": "DIGEST_FROM_NAME"},
  {"name": "POLL_INTERVAL_SECONDS", "default": "60"}
]
```

Rules:
- `sensitive: true` for credentials/tokens/passwords/API keys (masked input).
- Omit `sensitive` (or set `false`) for URLs, IDs, durations, display names, file paths, etc. (plain text — user must be able to see what they're typing).
- `default` is allowed only on non-sensitive variables.
- NEVER write a bare `"secrets": [...]` array on its own — always use `variables`. `canvas validate` warns on a legacy `secrets`-only manifest, and Studio's install gate rejects it outright.
- Some pieces of Canvas SDK reference documentation still show the legacy `secrets` form in older examples — ignore them; the runner accepts both, but Studio's UI cannot render the legacy form correctly.

## Internal-import rules

Imports within your own plugin must always use the full plugin-namespace prefix:

```python
# GOOD — full plugin-namespace path
from my_plugin.utils.helpers import format_date
from my_plugin.services.session import Session

# BAD — bare module names, sandbox rejects with "'X' is not an allowed import"
import thresholds
from models.cache import get
from utils.helpers import format_date
```

The plugin name must match the inner snake_case folder name (e.g. inner folder `vitals_alert/` ⇒ `from vitals_alert.protocols.handler import ...`).

## Requesting additional imports

If you need a library or function not on this list, file a request on the [Canvas developer forum](https://github.com/canvas-medical/canvas-plugins/discussions). Additions can usually be made after a security review. Do not work around the sandbox locally — the runner enforces these limits in production.
