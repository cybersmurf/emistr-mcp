<#
PowerShell wrapper: calls `mcp_client.py` and copies its JSON output to clipboard.
Usage:
 .\run_mcp_and_clip.ps1 -Name get_orders -Arguments '{"limit":10}'
 or
 MCP_URL=http://127.0.0.1:9201/mcp .\run_mcp_and_clip.ps1 -Name get_orders
#>
param(
 [Parameter(Mandatory=$true)][string]$Name,
 [string]$Arguments = "{}",
 [string]$Python = "",
 [string]$ClientScript = "mcp_client.py"
)

# Resolve script path relative to repo root (this script is in tools/)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
$clientPath = Join-Path $repoRoot $ClientScript

if (-not (Test-Path $clientPath)) {
 Write-Error "Client script not found at $clientPath"
 exit2
}

# Detect python if not provided
if (-not $Python) {
 if ($env:MCP_PYTHON) { $Python = $env:MCP_PYTHON }
 else {
 $pyCmd = Get-Command python -ErrorAction SilentlyContinue
 if (-not $pyCmd) { $pyCmd = Get-Command python3 -ErrorAction SilentlyContinue }
 if ($pyCmd) { $Python = $pyCmd.Source }
 else {
 # Try Windows py launcher
 $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
 if ($pyLauncher) { $Python = "$($pyLauncher.Source) -3" }
 }
 }
}

if (-not $Python) {
 Write-Error "Python interpreter not found. Set MCP_PYTHON env var or install Python and ensure 'python' or 'py' is on PATH."
 exit3
}

# Validate JSON arguments
try {
 $null = ConvertFrom-Json $Arguments -ErrorAction Stop
} catch {
 Write-Error "Invalid JSON in -Arguments"
 exit4
}

# Build argument list for process; ensure proper quoting
# If $Python contains spaces or includes '-3', handle accordingly
$pythonExe = $Python
$pythonArgsPrefix = @()
if ($pythonExe -match ' ') {
 # If contains space and additional arguments, split
 $parts = $pythonExe -split ' '
 $pythonExe = $parts[0]
 if ($parts.Count -gt1) { $pythonArgsPrefix = $parts[1..($parts.Count-1)] }
}

$argList = @()
$argList += $clientPath
$argList += '--name'
$argList += $Name
$argList += '--arguments'
$argList += $Arguments

# Combine prefix args and argList
$finalArgs = @()
$finalArgs += $pythonArgsPrefix
$finalArgs += $argList

$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = $pythonExe
$startInfo.Arguments = [string]::Join(' ', ($finalArgs | ForEach-Object { if ($_.Contains(' ')) { '"' + $_ + '"' } else { $_ } }))
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $startInfo
$proc.Start() | Out-Null
$output = $proc.StandardOutput.ReadToEnd()
$err = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()

if ($proc.ExitCode -ne0) {
 Write-Error "Client exited with code $($proc.ExitCode)"
 if ($err) { Write-Error $err }
 if ($output) { Write-Output $output }
 exit $proc.ExitCode
}

# Try to parse as JSON and pretty-print; copy to clipboard
try {
 $obj = ConvertFrom-Json $output
 $pretty = $obj | ConvertTo-Json -Depth10
} catch {
 $pretty = $output
}

# Copy to clipboard (works in Windows PowerShell and PowerShell Core)
try {
 Set-Clipboard -Value $pretty
 Write-Host "Output copied to clipboard"
} catch {
 # Fallback: write to temp file
 $tmp = [System.IO.Path]::GetTempFileName()
 Set-Content -Path $tmp -Value $pretty -Encoding UTF8
 Write-Host "Clipboard not available; output written to $tmp"
}

# Also print to console
Write-Output $pretty
