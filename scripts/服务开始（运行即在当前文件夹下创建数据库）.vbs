' Start Document Search System in background
Set objShell = CreateObject("WScript.Shell")
' Run document-search command with hidden window
objShell.Run "document-search", 0, False
' Show message
MsgBox "Document Search System started!" & vbCrLf & "Please visit http://localhost:3000", vbInformation, "Service Started"