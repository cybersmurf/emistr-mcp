$payload = @{ method = 'tools/call'; params = @{ name = 'get_orders'; arguments = @{ limit = 50 } } } | ConvertTo-Json -Depth 6
Invoke-RestMethod -Uri 'http://localhost:9201/mcp' -Method Post -ContentType 'application/json' -Body $payload | ConvertTo-Json -Depth 12
