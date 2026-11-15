# Wait for an async job

Use this when an endpoint starts a job (an export, an import, a batch run, a provisioning step) and answers before the work is done. A status endpoint tells you when the job finished.

## Poll with a bounded WHILE loop

Do not use `Sleep` to wait. A fixed pause is too short on a slow run and wastes time on a fast one. Poll the status endpoint in a `WHILE` loop with a `limit`, and fail with a message when the limit is reached:

```robotframework
*** Test Cases ***
Export Finishes
    ${res}=    POST On Session    api    /exports    json=${body}
    Status Should Be    202    ${res}
    ${id}=    Set Variable    ${res.json()}[id]

    ${state}=    Set Variable    queued
    WHILE    '${state}' not in ['done', 'failed']    limit=60    on_limit_message=Export ${id} still queued after 60 polls
        ${res}=    GET On Session    api    /exports/${id}
        Status Should Be    200    ${res}
        ${state}=    Set Variable    ${res.json()}[status]
    END
    Should Be Equal    ${state}    done    msg=Export ${id} ended as ${state}
```

## Rules

- **Set the limit from the measured run time.** Measure how long a normal run takes, then allow a little more. A large limit turns a stuck job into a long wait.
- **No pause between polls.** The loop polls as fast as the status call returns. If the API offers a long-poll or wait option, use it to space the calls.
- **Check the effect, not only the state.** When the job reports `done`, read the record or file it produced and assert its fields. A status alone is a loose check.
- **One loop per job.** Do not wrap `Wait Until Keyword Succeeds` around a keyword that already polls; the timeouts multiply.
- **Clean up.** Delete what the job created in the test teardown, by its exact id.

The `WHILE` options `limit` and `on_limit_message` need Robot Framework 7, the version this skill requires.
