Set shell = CreateObject("WScript.Shell")
projectDir = Replace(WScript.ScriptFullName, "run_frame2file.vbs", "")
shell.CurrentDirectory = projectDir
shell.Run "pyw.exe -m frame2file.app", 0, False
