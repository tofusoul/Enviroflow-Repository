# Xero Python SDK Documentation Summary

## Key API Usage Patterns

### Authentication
- Use OAuth2.0 for all API requests.
- Store and refresh token sets using decorators:
  ```python
  @api_client.oauth2_token_getter
  def obtain_xero_oauth2_token():
      return session.get("token")

  @api_client.oauth2_token_saver
  def store_xero_oauth2_token(token):
      session["token"] = token
      session.modified = True
  ```

### Making API Calls
- Always pass a valid `xero_tenant_id` (can be an empty string for custom connections).
- For most API methods, parameters like `statuses`, `summarize_errors`, etc. should be omitted or set to `None` if not used.
- Example for invoices:
  ```python
  invoices = accounting_api.get_invoices(xero_tenant_id)
  # or with filters
  invoices = accounting_api.get_invoices(xero_tenant_id, statuses=["DRAFT", "SUBMITTED"])
  ```

### Error Handling
- Catch `AccountingBadRequestException` and use `.reason` and `.error_data` attributes.
- Always check for attribute existence before accessing.

### Iteration and Return Types
- Many SDK methods return lists, but some may return single objects or non-iterable types (e.g., Enum, ApplyResult).
- Always check type before iterating.

### Example: Safe Iteration
```python
connections = identity_api.get_connections()
if connections is None:
    pass
elif isinstance(connections, (list, tuple)):
    for connection in connections:
        # ...
elif hasattr(connections, 'tenant_type'):
    # single object
    # ...
```

### Common Pitfalls
- Do not use `empty` as a parameter value; use `None` or omit the parameter.
- Always check for attribute existence before accessing (e.g., `.invoices`, `.contacts`).
- String concatenation with possible `None` values should use f-strings or explicit checks.

## References
- [Xero Python SDK GitHub](https://github.com/XeroAPI/xero-python)
- [Xero Developer Docs](https://developer.xero.com/documentation/api-guides)

---
This summary was generated from the official Xero Python SDK documentation and usage examples. For more details, see the README and sample apps in the SDK repository.
