# Migrating from RequestsLibrary to RESTinstance

A keyword map for moving API suites from RequestsLibrary to RESTinstance. Verify each replacement with `robotcode doc keyword <Library> "<Keyword>"` before you use it; argument orders differ.

| RequestsLibrary | RESTinstance | Note |
|---|---|---|
| `GET On Session    api    /path` | `GET    /path` | base URL in the library import |
| `POST On Session    api    /path    json=${data}` | `POST    /path    ${data}` | |
| `expected_status=200` | `Integer    response status    200` | assertion after the request |
| `${resp.json()}[key]` | `String    response body key` | typed field assertions |
| manual schema checks | `Expect Response Body    schema.json` | |

RESTinstance keeps expectations and headers for the whole suite; see `rf-restinstance`.

After each file, check it with `robotcode analyze code` and run the affected tests by longname. The `rf-migration-guide` subagent (plugin `rf-core`) runs the phased migration and reports each file as migrated or unverified.
