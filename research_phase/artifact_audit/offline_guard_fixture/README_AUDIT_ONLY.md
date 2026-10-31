# Offline guard demonstration fixture

This copied fixture is deliberately altered to test the runner's fresh-cache
request-integrity check. It is not a study dataset, inference run, or scientific
result. The transport function was replaced in memory with a sentinel exception.
No network request was made, no credential was read, and no model response was
created. All original Study B files remain unchanged. See
`../guard_check_result.json` and `../independent_audit.py`.
