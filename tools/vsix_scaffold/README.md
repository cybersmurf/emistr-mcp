VSIX Starter Scaffold (high-level instructions)

This folder contains a minimal scaffold and instructions to create a Visual Studio extension (VSIX) that invokes the `mcp_client.py` and displays results in a tool window.

What to do manually in Visual Studio:
1. Create a new VSIX project
 - File -> New -> Project -> Visual Studio Extensibility -> VSIX Project (.NET Framework or .NET6 depending on your target)
 - Name: EmistrMcpVsix

2. Add a Tool Window
 - Add -> New Item -> Visual C# -> Extensibility -> Tool Window
 - Name: McpToolWindow

3. Add a command to the tool window UI to call the MCP client
 - Use `System.Diagnostics.Process` to run Python with `mcp_client.py` (path configurable via Options or settings)
 - Capture stdout and stderr, parse JSON and display in the tool window (e.g., in a `TextBox` or `WebView2` control)

4. Example C# code snippet to call the client (synchronous call in a background task):

```csharp
using System.Diagnostics;
using System.Threading.Tasks;

public async Task<string> RunMcpClientAsync(string pythonPath, string clientScript, string name, string argumentsJson)
{
 return await Task.Run(() => {
 var psi = new ProcessStartInfo(pythonPath, $"\"{clientScript}\" --name \"{name}\" --arguments \"{argumentsJson}\"")
 {
 RedirectStandardOutput = true,
 RedirectStandardError = true,
 UseShellExecute = false,
 CreateNoWindow = true,
 };
 using var p = Process.Start(psi);
 var output = p.StandardOutput.ReadToEnd();
 var err = p.StandardError.ReadToEnd();
 p.WaitForExit();
 if (p.ExitCode !=0) throw new Exception($"MCP client failed: {err}");
 return output;
 });
}
```

5. Packaging and debugging
 - Set the VSIX project as startup project and press F5 to launch an experimental instance of Visual Studio for debugging the extension.

Notes
- This scaffold is a starting point. Implement proper options, error handling, async flows, and UI polish before shipping.
- Consider embedding an HTTP client in the extension (HttpClient) instead of calling Python if you want to avoid bundling Python.
