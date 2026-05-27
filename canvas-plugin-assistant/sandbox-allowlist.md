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
| `django.db.models` | `Avg`, `BigIntegerField`, `Case`, `CharField`, `Count`, `Exists`, `IntegerField`, `Max`, `Min`, `Model`, `OuterRef`, `Prefetch`, `Q`, `Subquery`, `Sum`, `Value`, `When` |
| `django.db.models.expressions` | `Case`, `Exists`, `OuterRef`, `Subquery`, `Value`, `When` |
| `django.db.models.query` | `Prefetch`, `QuerySet` |
| `django.utils.functional` | `cached_property` |
| `jwt` | `decode`, `encode`, `ExpiredSignatureError`, `InvalidTokenError`, `PyJWKClient` |
| `pydantic` | `BaseModel`, `conint`, `ConfigDict`, `constr`, `Field`, `RootModel`, `ValidationError` |
| `rapidfuzz` | `fuzz`, `process`, `utils` |
| `requests` | `delete`, `get`, `patch`, `post`, `put`, `request`, `RequestException`, `Response`, `Session` |

**Not on the list — frequently attempted but blocked:**
`yaml` (PyYAML), `httpx`, `aiohttp`, `urllib3`, `lxml`, `beautifulsoup4`, `numpy`, `pandas`, `boto3` (use `canvas_sdk.clients.aws`), `openai` / `anthropic` / `google-generativeai` (use `canvas_sdk.clients.llms`), `twilio` (use `canvas_sdk.clients`), `sendgrid` (use `canvas_sdk.clients`).

## Canvas SDK modules

All `canvas_sdk.*` modules are available — no allowlist on submodules or names:

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
- **No `@dataclass(frozen=True)`** (uses `exec()` internally, which the sandbox blocks). `@dataclass(slots=True)` is also out. For immutable records use `typing.NamedTuple`. Plain `@dataclass` (mutable) is fine.
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

The sandbox exposes Django's *query builders* (`Q`, `Count`, `Sum`, `Avg`, `Prefetch`, `Case`, `When`, `Exists`, `Subquery`, `OuterRef`, `Value`) but NOT the model *field types* (`CharField`, `TextField`, `IntegerField`, `BigIntegerField`, `DateTimeField`, `BooleanField`, `JSONField`, `UUIDField`). If you're declaring a `CustomModel` subclass, use Canvas SDK's field declarations from `canvas_sdk.v1.data` instead.

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
