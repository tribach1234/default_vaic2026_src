$ErrorActionPreference = "Stop"

$body = @{
    investor = @{
        id = 26
        name = "Agile SaaS Fund"
    }
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod `
    -Uri "http://127.0.0.1:5000/api/calendar/schedule" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$response | ConvertTo-Json -Depth 10
