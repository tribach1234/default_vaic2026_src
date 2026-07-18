$ErrorActionPreference = "Stop"
$uri = "http://127.0.0.1:5000/api/health"
Write-Host "Testing $uri"
$response = Invoke-RestMethod -Uri $uri -Method Get
$response | ConvertTo-Json -Depth 5
