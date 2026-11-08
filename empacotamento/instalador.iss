; Instalador do Dedo-Duro (Inno Setup 6). Compilado pelo build.ps1, que passa /DAppVersion=<versão>.
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppName "Dedo-Duro"
#define AppExe "DedoDuro.exe"

[Setup]
; AppId identifica o app para atualizações e desinstalação: nunca mude.
AppId={{6F1D2B7A-3C4E-4E8B-9A51-D3D0C0DED00D}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Thalles Lopes
AppPublisherURL=https://github.com/thalleslopes-dev/dedo-duro
AppSupportURL=https://github.com/thalleslopes-dev/dedo-duro/issues
; instala só para o usuário atual: não pede senha de administrador
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\DedoDuro
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; avisa (e oferece fechar) se o app estiver aberto, usando o mesmo mutex do app
AppMutex=DedoDuro_instancia_unica
CloseApplications=yes
OutputDir=..\dist
OutputBaseFilename=DedoDuro-Setup-{#AppVersion}
SetupIconFile=..\src\dedo_duro\recursos\icone.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
LicenseFile=..\LICENSE
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\DedoDuro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/IM {#AppExe} /F"; Flags: runhidden; RunOnceId: "FecharApp"

[UninstallDelete]
; o próprio app cria este atalho ("Executar quando o computador ligar"); some junto na desinstalação
Type: files; Name: "{userstartup}\Dedo-Duro.lnk"
