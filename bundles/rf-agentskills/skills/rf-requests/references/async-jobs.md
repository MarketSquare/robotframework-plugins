# Wait for an async job

Use this when an endpoint starts a job (an export, an import, a batch run, a provisioning step) and answers before the work is done. A status endpoint tells you when the job finished.

## Poll with a bounded WHILE loop

Do not use one long `Sleep` to wait. A fixed pause is too short on a slow run and wastes time on a fast one. Poll the status endpoint in a `WHILE` loop with a time-based `limit`, pause briefly between polls, and fail with a message when the limit is reached. Put the loop in a keyword; the test only calls it:

```robotframework
*** Test Cases ***
Export Finishes
    ${res}=    POST On Session    api    /exports    json=${body}
    Status Should Be    202    ${res}
    ${id}=    Set Variable    ${res.json()}[id]
    ${state}=    Wait For Export To Finish    ${id}
    Should Be Equal    ${state}    done    msg=Export ${id} ended as ${state}

*** Keywords ***
Wait For Export To Finish
    [Arguments]    ${id}
    ${state}=    Set Variable    queued
    WHILE    $state not in ['done', 'failed']    limit=60s    on_limit_message=Export ${id} not finished after 60s
        Sleep    2s
        ${res}=    GET On Session    api    /exports/${id}
        Status Should Be    200    ${res}
        ${state}=    Set Variable    ${res.json()}[status]
    END
    RETURN    ${state}
```

`$state` (no braces) passes the variable itself to the Python expression, so a value with quotes in it cannot break the condition.

## Rules

- **Set the limit from the measured run time.** `limit=60s` is a time limit; a bare number such as `limit=60` counts iterations instead. Measure how long a normal run takes, then allow a little more. A large limit turns a stuck job into a long wait.
- **Pause between polls.** A short `Sleep` inside the loop (1 to 5 seconds) keeps the loop from hammering the endpoint. If the API offers a long-poll or wait option, use it instead of the `Sleep`.
- **Control flow lives in keywords.** Keep the `WHILE` loop in a keyword such as `Wait For Export To Finish`, not in the test body.
- **Check the effect, not only the state.** When the job reports `done`, read the record or file it produced and assert its fields. A status alone is a loose check.
- **One loop per job.** Do not wrap `Wait Until Keyword Succeeds` around a keyword that already polls; the timeouts multiply.
- **Clean up.** Delete what the job created in the test teardown, by its exact id.

`WHILE` and its `limit` option exist since Robot Framework 5.0; `on_limit_message` needs Robot Framework 6.1 or later.
