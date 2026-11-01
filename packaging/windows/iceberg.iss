; Inno Setup script for Iceberg (ST-022).  Built by scripts/build_release.py when
; ISCC.exe is on the PATH (https://jrsoftware.org/isinfo.php); otherwise the
; zip archive is the Windows artifact.
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef DistDir
  #define DistDir "..\..\dist\Iceberg"
#endif

[Setup]
AppId={{7C1E1E8E-2F7B-4B9F-9C57-ICEBERG-ACCT}
AppName=Iceberg Accounting Suite
AppVersion={#AppVersion}
AppPublisher=Iceberg Accounting Suite
AppPublisherURL=https://github.com/iceberg-accounting/iceberg
DefaultDirName={autopf}\Iceberg
DefaultGroupName=Iceberg Accounting Suite
UninstallDisplayIcon={app}\Iceberg.exe
OutputDir=..\..\release
OutputBaseFilename=Iceberg-{#AppVersion}-windows-x64-setup
SetupIconFile=..\iceberg.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
LicenseFile=..\..\LICENSE

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Iceberg Accounting Suite"; Filename: "{app}\Iceberg.exe"
Name: "{autodesktop}\Iceberg Accounting Suite"; Filename: "{app}\Iceberg.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\Iceberg.exe"; Description: "Start Iceberg now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; The program folder only.  Books, backups, and logs live in %LOCALAPPDATA%\Iceberg
; and are deliberately left in place (see docs/DEPLOYMENT.md).
Type: filesandordirs; Name: "{app}\_internal"
