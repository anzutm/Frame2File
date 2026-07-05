Set shell = CreateObject("WScript.Shell")
shell.Run "pyw.exe """ & Replace(WScript.ScriptFullName, "run_frame2file.vbs", "main.py") & """", 0, False
