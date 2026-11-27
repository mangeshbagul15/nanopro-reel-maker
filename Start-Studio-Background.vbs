' ------------------------------------------------------------------
'  NanoPro Reel Maker - silent background launcher (Windows)
'  Runs Start-Studio-Background.bat with NO console window.
'  Used by the Windows login auto-start shortcut.
' ------------------------------------------------------------------
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = base
sh.Run """" & base & "\Start-Studio-Background.bat""", 0, False
