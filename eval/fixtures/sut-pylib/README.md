# sut-pylib

Robot Framework project (RF 7.0+). Project keyword libraries and listeners live
in `libraries/`, which is on the python-path (`robot.toml`
`python-path = ["libraries"]`). Needs only `robotframework`.

Run from this directory:

```bash
robot --pythonpath libraries tests
```
