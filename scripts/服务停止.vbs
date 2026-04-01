' Stop Document Search System
Set objShell = CreateObject("WScript.Shell")
Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")

' Find Python processes containing document-search
Set colProcesses = objWMIService.ExecQuery _
    ("SELECT * FROM Win32_Process WHERE Name = 'python.exe'")

Dim intProcessesKilled
intProcessesKilled = 0

For Each objProcess In colProcesses
    ' Check if process command line contains document-search
    If InStr(objProcess.CommandLine, "document-search") > 0 Then
        ' Terminate process
        objProcess.Terminate()
        intProcessesKilled = intProcessesKilled + 1
    End If
Next

' Show result
If intProcessesKilled > 0 Then
    MsgBox "Successfully stopped " & intProcessesKilled & " Document Search System process(es)!", vbInformation, "Service Stopped"
Else
    MsgBox "No running Document Search System service found.", vbInformation, "Service Stop"
End If