param(
    [int]$Limit = 50,
    [string]$BaseUrl = 'http://localhost:9201/mcp'
)

$modulePath = Join-Path $PSScriptRoot '..\module\Emistr.Mcp.psd1' | Resolve-Path
Import-Module $modulePath -Force

$orders = Get-EmistrOrders -Limit $Limit -BaseUrl $BaseUrl

if ($orders -is [System.Collections.IEnumerable]) {
    $orders | Select-Object code, name, customer_name, start, finish, kusu, priorita, id, bar_id | Sort-Object start | Format-Table -AutoSize
} else {
    $orders | ConvertTo-Json -Depth 12 | Write-Output
}
