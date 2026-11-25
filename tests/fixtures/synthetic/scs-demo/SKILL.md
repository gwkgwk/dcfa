---
name: synthetic-summary
input:
  data_type: Text
  sensitivity: Private
  trust_origin: local
output: Text
effect:
  name: persistent-state write
  requires_authorization: true
context_exposure: workspace
trust_boundary:
  source: local
  destination: persistent state
---
# Synthetic example
Accept text.
Return text.
Consider formatting preferences.
