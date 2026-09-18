; Inno Setup script for Humanoid Bot Assistant OS.
; Build (on Windows, after PyInstaller): ISCC packaging\installer.iss
; Requires Inno Setup 6: https://jrsoftware.org/isinfo.php

#define MyAppName "Humanoid Bot Assistant"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "HumanoidBot"
#define MyAppExeName "HumanoidBotAssistant.exe"

[Setup]
AppId={{7E1F2B44-90F8-4C61-9B7A-HUMANOIDBOT01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\HumanoidBot
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputBaseFilename=HumanoidBotAssistant-Setup
OutputDir=dist
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "autostart"; Description: "Start {#MyAppName} with Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "..\dist\HumanoidBotAssistant\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
