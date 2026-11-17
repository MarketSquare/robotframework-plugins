# Loose assertions

A check that cannot fail gives a green run against a broken API. Each pattern below passes when the endpoint returns the wrong data, so do not use one as the only check on a response.

## Patterns to avoid

| Loose check | Why it passes on a broken endpoint | Assert this instead |
|---|---|---|
| `Should Not Be Empty    ${resp.json()}` | any body with one key passes, an error object included | the field and value the contract names: `Should Be Equal    ${resp.json()}[status]    active    msg=status` |
| `Should Be True    ${resp.ok}` | `ok` is true for every status below 400, 3xx included | `Status Should Be    200    ${resp}` and the field checks |
| A status check alone after a write | the server can accept the request and store something else | a read-back: `GET On Session` the new record and compare the fields you sent |
| `Should Be Equal    ${x}    ${x}` | compares a value with itself | the expected value from the spec, the requirement or a fixture |
| A helper that turns a non-200 response into an empty result | the caller sees nothing to check and the test passes | let the status check raise, or pass `expected_status` on the one call that expects the error |

## Rules

- Give each check a `msg=` that names the field, so a failure says what was wrong.
- Assert the exact value the test sets up or the spec defines. Use a type or schema check for shape only.
- Prove a new check can fail: change the expected value once, run the test, confirm it turns red, then restore the value.
- After a write, check the stored result with a read-back, not with the write's own status.
