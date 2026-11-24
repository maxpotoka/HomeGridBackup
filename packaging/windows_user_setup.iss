#ifndef AppVersion
  #define AppVersion "2.25"
#endif

#ifndef OutputBaseFilename
  #define OutputBaseFilename "HomeGridBackup_Setup"
#endif

#ifndef AppDirName
  #define AppDirName "HomeGridBackup"
#endif

#ifndef AppIdGuid
  #define AppIdGuid "{849CA065-D972-41A1-BA97-1B3858B1CA4B}"
#endif

[Setup]
AppId={#AppIdGuid}
AppName=HomeGrid Backup
AppVersion={#AppVersion}
AppPublisher=HomeGrid
DefaultDirName={localappdata}\Programs\{#AppDirName}
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
MinVersion=6.1
OutputDir=installer_output
OutputBaseFilename={#OutputBaseFilename}
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\HomeGridBackup.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "installer_payload\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\HomeGrid Backup"; Filename: "{app}\HomeGridBackup.exe"
Name: "{userdesktop}\HomeGrid Backup"; Filename: "{app}\HomeGridBackup.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\HomeGridBackup.exe"; Description: "Launch HomeGrid Backup"; Flags: postinstall nowait skipifsilent
