function Invoke-EmistrMcp {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $false)][hashtable]$Params,
        [Parameter(Mandatory = $false)][string]$BaseUrl = 'http://localhost:9201/mcp'
    )

    if (-not $Params) { $Params = @{} }
    $body = @{ method = $Method; params = ($Params | ForEach-Object { $_ } ) } | ConvertTo-Json -Depth 8
    try {
        $resp = Invoke-RestMethod -Uri $BaseUrl -Method Post -ContentType 'application/json' -Body $body
        return $resp
    } catch {
        throw
    }
}

function Get-EmistrOrders {
    [CmdletBinding()]
    param(
        [int]$Limit = 50,
        [int]$Offset,
        [string]$Status,
        [int]$CustomerId,
        [string]$DateFrom,
        [string]$DateTo,
        [string]$BaseUrl = 'http://localhost:9201/mcp'
    )

    $paramMap = @{}
    if ($PSBoundParameters.ContainsKey('Limit')) { $paramMap.limit = $Limit }
    if ($PSBoundParameters.ContainsKey('Offset')) { $paramMap.offset = $Offset }
    if ($PSBoundParameters.ContainsKey('Status')) { $paramMap.status = $Status }
    if ($PSBoundParameters.ContainsKey('CustomerId')) { $paramMap.customer_id = $CustomerId }
    if ($PSBoundParameters.ContainsKey('DateFrom')) { $paramMap.date_from = $DateFrom }
    if ($PSBoundParameters.ContainsKey('DateTo')) { $paramMap.date_to = $DateTo }

    $resp = Invoke-EmistrMcp -Method 'get_orders' -Params $paramMap -BaseUrl $BaseUrl
    if ($resp.result -and $resp.result.data -and $resp.result.data.items) { return $resp.result.data.items }
    return $resp
}

function Get-EmistrOrderDetail {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$OrderId,
        [string]$BaseUrl = 'http://localhost:9201/mcp'
    )
    $paramMap = @{ order_id = $OrderId }
    $resp = Invoke-EmistrMcp -Method 'get_order_detail' -Params $paramMap -BaseUrl $BaseUrl
    if ($resp.result -and $resp.result.data) { return $resp.result.data }
    return $resp
}

function Search-EmistrOrders {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$SearchTerm,
        [int]$Limit = 20,
        [string]$BaseUrl = 'http://localhost:9201/mcp'
    )
    $paramMap = @{ search_term = $SearchTerm }
    if ($PSBoundParameters.ContainsKey('Limit')) { $paramMap.limit = $Limit }
    $resp = Invoke-EmistrMcp -Method 'search_orders' -Params $paramMap -BaseUrl $BaseUrl
    if ($resp.result -and $resp.result.data -and $resp.result.data.items) { return $resp.result.data.items }
    return $resp
}

Export-ModuleMember -Function Invoke-EmistrMcp, Get-EmistrOrders, Get-EmistrOrderDetail, Search-EmistrOrders

