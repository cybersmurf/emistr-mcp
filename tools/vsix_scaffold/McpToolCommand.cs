using System;
using System.ComponentModel.Design;
using System.Diagnostics;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.VisualStudio.Shell;

namespace EmistrMcpVsix
{
 internal sealed class McpToolCommand
 {
 public const int CommandId =0x0100;
 public static readonly Guid CommandSet = new Guid("b1e7d7e8-4c3a-4ad0-9c9a-7b9f1d2f8e4e");
 private readonly AsyncPackage package;

 private McpToolCommand(AsyncPackage package, OleMenuCommandService commandService)
 {
 this.package = package ?? throw new ArgumentNullException(nameof(package));

 var menuCommandID = new CommandID(CommandSet, CommandId);
 var menuItem = new MenuCommand(this.Execute, menuCommandID);
 commandService.AddCommand(menuItem);
 }

 public static McpToolCommand Instance { get; private set; }

 private Microsoft.VisualStudio.Shell.IAsyncServiceProvider ServiceProvider => this.package;

 public static async Task InitializeAsync(AsyncPackage package)
 {
 // Switch to main thread for VS services
 await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync(package.DisposalToken);
 var commandService = await package.GetServiceAsync(typeof(IMenuCommandService)) as OleMenuCommandService;
 Instance = new McpToolCommand(package, commandService);
 }

 private void Execute(object sender, EventArgs e)
 {
 // Run the MCP client in background and show output in a MessageBox for scaffold
 _ = RunAndShowAsync();
 }

 private async Task RunAndShowAsync()
 {
 await TaskScheduler.Default;
 try
 {
 var pythonPath = "python"; // can be read from options
 var scriptPath = System.IO.Path.Combine(System.IO.Path.GetDirectoryName(typeof(McpToolCommand).Assembly.Location), "..\\..\\..\\mcp_client.py");
 var argumentsJson = "{}";

 var psi = new ProcessStartInfo(pythonPath, $"\"{scriptPath}\" --name \"get_orders\" --arguments \"{argumentsJson}\"")
 {
 RedirectStandardOutput = true,
 RedirectStandardError = true,
 UseShellExecute = false,
 CreateNoWindow = true
 };

 using (var proc = Process.Start(psi))
 {
 var output = proc.StandardOutput.ReadToEnd();
 var err = proc.StandardError.ReadToEnd();
 proc.WaitForExit();
 if (proc.ExitCode !=0)
 {
 MessageBox.Show($"MCP client failed: {err}", "MCP Client", MessageBoxButtons.OK, MessageBoxIcon.Error);
 }
 else
 {
 MessageBox.Show(output, "MCP Client Output", MessageBoxButtons.OK, MessageBoxIcon.Information);
 }
 }
 }
 catch (Exception ex)
 {
 MessageBox.Show(ex.ToString(), "MCP Client Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
 }
 }
 }
}
