# Loose assertions

A check that cannot fail gives a green run against a broken API. Each pattern below passes when the endpoint returns the wrong data, so do not use one as the only check on a response.

## Patterns to avoid

| Loose check | Why it passes on a broken endpoint | Assert this instead |
|---|---|---|
| `Object    response body    required=["id"]` alone | it proves the key exists, not its value | `String    response body name    Alice` for the value, `Integer    response body id    minimum=1` for the range |
| `Integer    response body id` alone | any integer passes | the value the test expects, or the bound the contract sets |
| `Integer    response status    200` alone after a write | the server can accept the request and store something else | a `GET` of the new record, then the field checks |

## Rules

- Use the exact expected value for each field the test cares about.
- Use types and constraints for shape only, never as the only check of a value.
- Prove a new check can fail: change the expected value once, run the test, confirm it turns red, then restore the value.
- After a write, check the stored result with a read-back, not with the write's own status.
