@{
    RootModule        = 'Emistr.Mcp.psm1'
    ModuleVersion     = '0.1.0'
    GUID              = '3d8e1e3a-7d3e-4b3f-9e3c-8b0d8d7f2a11'
    Author            = 'Local'
    CompanyName       = 'Local'
    Copyright        = '(c) Local. All rights reserved.'
    PowerShellVersion = '5.1'
    Description       = 'PowerShell klient pro eMISTR MCP HTTP endpoint.'
    FunctionsToExport = @('Invoke-EmistrMcp','Get-EmistrOrders','Get-EmistrOrderDetail','Search-EmistrOrders')
    CmdletsToExport   = @()
    VariablesToExport = @()
    AliasesToExport   = @()
    PrivateData       = @{}
}
