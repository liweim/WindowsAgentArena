$ErrorActionPreference = "Continue" # until downloading from mirrors is more stable

# Section - General Setup
$shortcutShared = "C:\Users\Docker\Desktop\Setup"
$scriptFolder = "\\host.lan\Data"
$toolsFolder = "C:\Users\$env:USERNAME\Tools"

# Load the shared setup-tools module
Import-Module (Join-Path $scriptFolder -ChildPath "setup-tools.psm1")

# Create a shortcut to the shared folder if it doesn't exist
if (-not (Test-Path $shortcutShared)) {
    New-Item -ItemType SymbolicLink -Path $shortcutShared -Value $scriptFolder
}

# Check if profile exists
if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force
}

# Create a folder where we store all the standalone executables
if (-not (Test-Path $toolsFolder)) {
    New-Item -ItemType Directory -Path $toolsFolder -Force
    $envPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    $newPath = "$envPath;$toolsFolder"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")
}

# Section - Tools Installation

# Set TLS version to 1.2 or higher
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

# A benchmark golden image must not change underneath later rebuilds or runs.
$windowsUpdatePolicy = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
New-Item -Path $windowsUpdatePolicy -Force | Out-Null
Set-ItemProperty -Path $windowsUpdatePolicy -Name "NoAutoUpdate" -Type DWord -Value 1
Stop-Service -Name wuauserv -Force -ErrorAction SilentlyContinue
Set-Service -Name wuauserv -StartupType Disabled -ErrorAction SilentlyContinue

# Load the tools config json listing mirrors and aliases used for installing tools
$toolsConfigJsonPath = Join-Path $scriptFolder -ChildPath "tools_config.json"
$toolsConfigJson = Get-Content -Path $toolsConfigJsonPath -Raw
$toolsList = Get-Tools -toolsConfigJson $toolsConfigJson

## - Python
$pythonToolName = "Python"
$userPythonPath = "$env:LOCALAPPDATA\Programs\Python"
$pythonDetails = Get-ToolDetails -toolsList $toolsList -toolName $pythonToolName
$pythonAlias = $pythonDetails.alias

# Use one explicit interpreter path everywhere. Searching recursively can pick
# up another application's bundled python.exe after software installation.
$expectedPythonVersion = $pythonDetails.version
$pythonExecutablePath = "$userPythonPath\Python310\python.exe"
if (Test-Path $pythonExecutablePath) {
    $installedPythonVersion = (& $pythonExecutablePath --version 2>&1) -replace '^Python\s+', ''
    if ($installedPythonVersion -ne $expectedPythonVersion) {
        throw "Python $installedPythonVersion is installed; expected $expectedPythonVersion. Rebuild from a clean golden disk."
    }
    Write-Host "Python $installedPythonVersion is already installed."
} else {
    Write-Host "Downloading Python $expectedPythonVersion..."
    $pythonInstallerFilePath = "$env:TEMP\python_installer.exe"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $pythonDetails.mirrors -outfile $pythonInstallerFilePath
    if (-not $downloadResult) {
        throw "Failed to download Python $expectedPythonVersion."
    } else {
        Write-Host "Installing Python for current user..."
        Start-Process -FilePath $pythonInstallerFilePath -Args "/quiet InstallAllUsers=0 PrependPath=0" -NoNewWindow -Wait
        Remove-Item -Path $pythonInstallerFilePath -Force
    }
}
$setAliasExpression = "Set-Alias -Name $pythonAlias -Value `"$pythonExecutablePath`""
Add-Content -Path $PROFILE -Value $setAliasExpression
Invoke-Expression $setAliasExpression

## - Git
$gitToolName = "git"
$gitToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $gitToolName

# Check for Git installation
try {
    git --version | Out-Null
    Write-Host "Git is already installed."
} catch {
    Write-Host "Git is not installed. Downloading and installing Git..."
    $gitInstallerFilePath = "$env:TEMP\git_installer.exe"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $gitToolDetails.mirrors -outfile $gitInstallerFilePath
    if (-not $downloadResult) {
        Write-Host "Failed to download Git. Please try again later or install manually."
    } else {
        Start-Process -FilePath $gitInstallerFilePath -Args "/VERYSILENT /NORESTART /NOCANCEL /SP-" -Wait
        Add-ToEnvPath -NewPath "C:\Program Files\Git\bin"

        Write-Host "Git has been installed."
    }
}

# - 7zip
$7ZipToolName = "7zip"
$7ZipToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $7ZipToolName
Write-Host "$7ZipToolDetails"

if (Get-Command 7z -ErrorAction SilentlyContinue) {
    Write-Host "7-Zip is already installed."
}
else {
    Write-Host "Installing 7-Zip..."

    $7ZipInstallerFilePath = "$env:TEMP\7_zip.exe"
    Write-Host "$($7ZipToolDetails.mirrors)"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $7ZipToolDetails.mirrors -outfile $7ZipInstallerFilePath
    if (-not $downloadResult) {
        Write-Host "Failed to download 7-Zip. Please try again later or install manually."
    } else {
        Start-Process -FilePath $7ZipInstallerFilePath -Args "/S" -Verb RunAs -Wait
        Remove-Item $7ZipInstallerFilePath

        # add 7z to PATH
        Add-ToEnvPath -NewPath "${env:ProgramFiles}\7-Zip"
    }
}

# - ffpmeg
$ffpmegToolName = "ffmpeg"
$ffpmegToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $ffpmegToolName

if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Host "ffmpeg is already installed."
} else {
    Write-Host "ffmpeg is not installed. Installing it."
    $ffpmegInstallerFilePath = "C:\ffmpeg.7z"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $ffpmegToolDetails.mirrors -outfile $ffpmegInstallerFilePath
    if (-not $downloadResult) {
        Write-Host "Failed to download ffmpeg. Please try again later or install manually."
    } else {
        Write-Host "Extracting $ffpmegInstallerFilePath..."
        7z x -y -o"C:\" "C:\ffmpeg.7z"

        $ffmpegFolder = Get-ChildItem -Path "C:\" -Filter "ffmpeg-*" -Directory
        $ffmpegFolder = -join ("C:\",  $ffmpegFolder)
        #remove ffmpeg folder if exists
        if (Test-Path "C:\ffmpeg") {
            Remove-Item -Path "C:\ffmpeg" -Recurse -Force
        }
        Rename-Item -Path "$ffmpegFolder" -NewName "ffmpeg"

        Write-Host "Adding ffmpeg to PATH..."
        Add-ToEnvPath -NewPath "C:\ffmpeg\bin"

        Write-Host "ffmpeg is installed"
    }
}

# Disable Edge Auto Updates
Stop-Process -Name "MicrosoftEdgeUpdate" -Force -ErrorAction SilentlyContinue
$edgeUpdatePath = "${env:ProgramFiles(x86)}\Microsoft\EdgeUpdate"
Remove-Item -Path $edgeUpdatePath -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Edge Update processes terminated and directory removed."

# - Google Chrome
$chromeToolName = "Google Chrome"
$chromeToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $chromeToolName
$chromeExePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$chromeAlias = $chromeToolDetails.alias

# Install a fixed Chrome for Testing build. The upstream `latest` bootstrapper
# made both Chrome UI and CDP behavior depend on the date of image creation.
$expectedChromeVersion = $chromeToolDetails.version
if (Test-Path $chromeExePath) {
    $installedChromeVersion = (Get-Item $chromeExePath).VersionInfo.ProductVersion
    if (-not $installedChromeVersion.StartsWith($expectedChromeVersion)) {
        throw "Chrome $installedChromeVersion is installed; expected $expectedChromeVersion. Rebuild from a clean golden disk."
    }
    Write-Host "Google Chrome $installedChromeVersion is already installed."
} else {
    $chromeInstallerFilePath = "$env:TEMP\chrome-for-testing.zip"
    $chromeExtractPath = "$env:TEMP\chrome-for-testing"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $chromeToolDetails.mirrors -outfile $chromeInstallerFilePath
    if (-not $downloadResult) {
        throw "Failed to download Google Chrome $expectedChromeVersion."
    } else {
        Remove-Item -Path $chromeExtractPath -Recurse -Force -ErrorAction SilentlyContinue
        7z x -y "-o$chromeExtractPath" $chromeInstallerFilePath | Out-Null
        $chromeInstallPath = Split-Path $chromeExePath -Parent
        New-Item -ItemType Directory -Path $chromeInstallPath -Force | Out-Null
        Copy-Item -Path "$chromeExtractPath\chrome-win64\*" -Destination $chromeInstallPath -Recurse -Force
        Remove-Item -Path $chromeInstallerFilePath -Force
        Remove-Item -Path $chromeExtractPath -Recurse -Force
    }
}
if (-not (Test-Path $chromeExePath)) {
    throw "Chrome installation did not create $chromeExePath"
}

$setAliasExpression = "Set-Alias -Name $chromeAlias -Value `"$chromeExePath`""
Add-Content -Path $PROFILE -Value $setAliasExpression
Invoke-Expression $setAliasExpression
Add-ToEnvPath -NewPath "${env:ProgramFiles}\Google\Chrome\Application"

$chromePolicyPath = "HKLM:\SOFTWARE\Policies\Google\Chrome"
New-Item -Path $chromePolicyPath -Force | Out-Null
Set-ItemProperty -Path $chromePolicyPath -Name "BackgroundModeEnabled" -Type DWord -Value 0
Set-ItemProperty -Path $chromePolicyPath -Name "HideFirstRunExperience" -Type DWord -Value 1

$chromeUserDataPath = "$env:LOCALAPPDATA\Google\Chrome\User Data"
$chromeDefaultProfilePath = Join-Path $chromeUserDataPath "Default"
New-Item -ItemType Directory -Path $chromeDefaultProfilePath -Force | Out-Null
New-Item -ItemType File -Path (Join-Path $chromeUserDataPath "First Run") -Force | Out-Null
$chromePreferences = @{
    browser = @{ check_default_browser = $false }
    profile = @{ exit_type = "Normal"; exited_cleanly = $true }
}
$chromePreferences | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $chromeDefaultProfilePath "Preferences") -Encoding UTF8

# Chrome 136+ requires a non-default --user-data-dir for remote debugging.
# Use a junction so GUI and evaluators still read and write the same profile.
$chromeDebugProfilePath = "C:\Temp\winarena-chrome-user-data"
New-Item -ItemType Directory -Path "C:\Temp" -Force | Out-Null
if (Test-Path $chromeDebugProfilePath) {
    $isJunction = ((Get-Item $chromeDebugProfilePath).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
    if (-not $isJunction) {
        Remove-Item -Path $chromeDebugProfilePath -Recurse -Force
    }
}
if (-not (Test-Path $chromeDebugProfilePath)) {
    New-Item -ItemType Junction -Path $chromeDebugProfilePath -Target $chromeUserDataPath | Out-Null
}

# - LibreOffice
$libreOfficeToolName = "LibreOffice"
$libreOfficeToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $libreOfficeToolName

# Check for LibreOffice installation
$expectedLibreOfficeVersion = $libreOfficeToolDetails.version
$installedVersion = (Get-WmiObject -Query "SELECT * FROM Win32_Product WHERE Name like 'LibreOffice%'").Version
if (-not [string]::IsNullOrWhiteSpace($installedVersion)) {
    if (-not $installedVersion.StartsWith($expectedLibreOfficeVersion)) {
        throw "LibreOffice $installedVersion is installed; expected $expectedLibreOfficeVersion. Rebuild from a clean golden disk."
    }
    Write-Host "LibreOffice $installedVersion is already installed."
} else {
    Write-Host "LibreOffice is not installed. Downloading and installing LibreOffice..."
    $libreOfficeInstallerFilePath = "$env:TEMP\libreOffice_installer.msi"
    
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $libreOfficeToolDetails.mirrors -outfile $libreOfficeInstallerFilePath
    if (-not $downloadResult) {
        throw "Failed to download LibreOffice $expectedLibreOfficeVersion."
    } else {
        Assert-FileSha256 -Path $libreOfficeInstallerFilePath -ExpectedHash $libreOfficeToolDetails.sha256
        Start-Process "msiexec.exe" -ArgumentList "/i `"$libreOfficeInstallerFilePath`" /quiet" -Wait -NoNewWindow
        Write-Host "LibreOffice has been installed."
        Remove-Item -Path $libreOfficeInstallerFilePath -Force
    }
}
$sofficeExecutablePath = "C:\Program Files\LibreOffice\program\soffice.exe"
if (-not (Test-Path $sofficeExecutablePath)) {
    throw "LibreOffice installation did not create $sofficeExecutablePath"
}
Add-ToEnvPath -NewPath "C:\Program Files\LibreOffice\program"

# Create the normal user profile once in the golden image. Per-task code must
# reuse this profile instead of deleting it and re-triggering first-run dialogs.
Start-Process -FilePath $sofficeExecutablePath -ArgumentList "--headless", "--nofirststartwizard", "--norestore", "--terminate_after_init" -Wait

# - VLC
$vlcToolName = "VLC"
$vlcToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $vlcToolName
$vlcAlias = $vlcToolDetails.alias
$vlcExecutableFilePath = "C:\Program Files\VideoLAN\VLC\vlc.exe"

# Check if VLC is already installed by checking the VLC command
$expectedVlcVersion = $vlcToolDetails.version
if (Test-Path $vlcExecutableFilePath) {
    $installedVlcVersion = (Get-Item $vlcExecutableFilePath).VersionInfo.ProductVersion
    if (-not $installedVlcVersion.StartsWith($expectedVlcVersion)) {
        throw "VLC $installedVlcVersion is installed; expected $expectedVlcVersion. Rebuild from a clean golden disk."
    }
    Write-Host "VLC $installedVlcVersion is already installed."
} else {
    # Download the installer to the Temp directory
    $vlcInstallerFilePath = "$env:TEMP\vlc_installer.exe"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $vlcToolDetails.mirrors -outfile $vlcInstallerFilePath
    if (-not $downloadResult) {
        throw "Failed to download VLC $expectedVlcVersion."
    } else {
        Assert-FileSha256 -Path $vlcInstallerFilePath -ExpectedHash $vlcToolDetails.sha256
        # Execute the installer silently with elevated permissions
        Start-Process -FilePath $vlcInstallerFilePath -ArgumentList "/S" -Verb RunAs -Wait

        # Remove the installer file after installation
        Remove-Item -Path $vlcInstallerFilePath

    }
}
if (-not (Test-Path $vlcExecutableFilePath)) {
    throw "VLC installation did not create $vlcExecutableFilePath"
}
$setAliasExpression = "Set-Alias -Name $vlcAlias -Value `"$vlcExecutableFilePath`""
Add-Content -Path $PROFILE -Value $setAliasExpression
Invoke-Expression $setAliasExpression
Add-ToEnvPath -NewPath "C:\Program Files\VideoLAN\VLC"

# Suppress VLC's privacy/update wizard and make the Qt interface deterministic.
$vlcProfilePath = Join-Path $env:APPDATA "vlc"
New-Item -ItemType Directory -Path $vlcProfilePath -Force | Out-Null
@(
    "intf=qt"
    "qt-privacy-ask=0"
    "qt-updates-notif=0"
) | Set-Content -Path (Join-Path $vlcProfilePath "vlcrc") -Encoding ASCII

# - GIMP
$gimpToolName = "GIMP"
$gimpToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $gimpToolName
$gimpAlias = $gimpToolDetails.alias
$gimpExecutablePath = "C:\Program Files\GIMP 2\bin\gimp-2.10.exe"

# Check if GIMP is already installed by checking the GIMP executable path
if (Test-Path $gimpExecutablePath) {
    Write-Host "GIMP is already installed."
} else {
    # Download the installer to the Temp directory
    $gimpInstallerFilePath = "$env:TEMP\gimp_installer.exe"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $gimpToolDetails.mirrors -outfile $gimpInstallerFilePath
    if (-not $downloadResult) {
        Write-Host "Failed to download GIMP. Please try again later or install manually."
    } else {
        # Execute the installer silently with elevated permissions
        Start-Process -FilePath $gimpInstallerFilePath -ArgumentList "/VERYSILENT /ALLUSERS" -Verb RunAs -Wait

        # Remove the installer file after installation
        Remove-Item -Path $gimpInstallerFilePath

        # Set alias
        $setAliasExpression = "Set-Alias -Name $gimpAlias -Value `"$gimpExecutablePath`""
        Add-Content -Path $PROFILE -Value $setAliasExpression
        Invoke-Expression $setAliasExpression

        # Add GIMP to the system PATH environment variable
        Add-ToEnvPath -NewPath "C:\Program Files\GIMP 2\bin"
    }
}

# - VS Code
$vsCodeToolName = "VS Code"
$vsCodeToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $vsCodeToolName
$vsCodeAlias = $gimpToolDetails.alias
$vsCodeExecutablePath = "C:\Users\$env:USERNAME\AppData\Local\Programs\Microsoft VS Code\Code.exe"

# Check if VS Code is already installed by checking the VS Code executable path
if (Test-Path $vsCodeExecutablePath) {
    Write-Host "VS Code is already installed."
} else {
    # Download the installer to the Temp directory
    $vsCodeInstallerFilePath = "$env:TEMP\VSCodeSetup.exe"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $vsCodeToolDetails.mirrors -outfile $vsCodeInstallerFilePath
    if (-not $downloadResult) {
        Write-Host "Failed to download VS Code. Please try again later or install manually."
    } else {
        # Execute the installer silently with elevated permissions
        Start-Process -FilePath $vsCodeInstallerFilePath -ArgumentList "/VERYSILENT", "/mergetasks=!runcode" -Verb RunAs -Wait

        # Remove the installer file after installation
        Remove-Item -Path $vsCodeInstallerFilePath

        # Set alias
        $setAliasExpression = "Set-Alias -Name $vsCodeAlias -Value `"$vsCodeExecutablePath`""
        Add-Content -Path $PROFILE -Value $setAliasExpression
        Invoke-Expression $setAliasExpression

        # Add VS Code to the system PATH environment variable
        Add-ToEnvPath -NewPath "C:\Users\$env:USERNAME\AppData\Local\Programs\Microsoft VS Code\bin"

        # Disable Visual Studio Code Auto Updates
        $vsCodeSettingsPath = "${env:APPDATA}\Code\User\settings.json"
        if (-not (Test-Path $vsCodeSettingsPath)) {
            # Create the directory if it doesn't exist
            $dirPath = Split-Path -Path $vsCodeSettingsPath -Parent
            if (-not (Test-Path $dirPath)) {
                New-Item -ItemType Directory -Path $dirPath -Force
            }
            # Initialize an empty hashtable to act as the JSON object
            $settingsObj = @{}
            $settingsObj["update.mode"] = "none"  # Set update mode to none
            $settingsObj | ConvertTo-Json | Set-Content $vsCodeSettingsPath
        } else {
            # If the file exists, modify it
            $settingsObj = Get-Content $vsCodeSettingsPath | ConvertFrom-Json
            $settingsObj["update.mode"] = "none"
            $settingsObj | ConvertTo-Json | Set-Content $vsCodeSettingsPath
        }
    }
}

# - Thunderbird
$thunderbirdToolName = "Thunderbird"
$thunderbirdToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $thunderbirdToolName
$thunderbirdAlias = $thunderbirdToolDetails.alias
$thunderbirdExecutablePath = "C:\Program Files\Mozilla Thunderbird\thunderbird.exe"

# Check if Thunderbird is already installed by checking the Thunderbird executable path
if (Test-Path $thunderbirdExecutablePath) {
    Write-Host "Thunderbird is already installed."
} else {
    # Download the installer to the Temp directory
    $thunderbirdInstallerFilePath = "$env:TEMP\ThunderbirdSetup.exe"
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $thunderbirdToolDetails.mirrors -outfile $thunderbirdInstallerFilePath
    if (-not $downloadResult) {
        Write-Host "Failed to download Thunderbird. Please try again later or install manually."
    } else {
        # Execute the installer silently with elevated permissions
        Start-Process -FilePath $thunderbirdInstallerFilePath -ArgumentList "/S" -Verb RunAs -Wait

        # Remove the installer file after installation
        Remove-Item -Path $thunderbirdInstallerFilePath

        # Set alias
        $setAliasExpression = "Set-Alias -Name $thunderbirdAlias -Value `"$thunderbirdExecutablePath`""
        Add-Content -Path $PROFILE -Value $setAliasExpression
        Invoke-Expression $setAliasExpression

        # Add Thunderbird to the system PATH environment variable
        Add-ToEnvPath -NewPath "C:\Program Files\Mozilla Thunderbird"
    }
}

# - Caddy Proxy
$caddyProxyToolName = "Caddy Proxy"
$caddyProxyToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $caddyProxyToolName
$caddyProxyAlias = $caddyProxyToolDetails.alias
$caddyProxyExecutablePath = "C:\Users\$env:USERNAME\caddy_windows_amd64.exe"

# Check if Caddy is already installed by checking the Caddy executable path
if (Test-Path $caddyProxyExecutablePath) {
    Write-Host "Caddy Server is already installed."
} else {
    # Download the installer to the Temp directory
    $downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $caddyProxyToolDetails.mirrors -outfile $caddyProxyExecutablePath
    if (-not $downloadResult) {
        Write-Host "Failed to download Caddy Proxy. Please try again later or install manually."
    } else {
        # Set alias
        $setAliasExpression = "Set-Alias -Name $caddyProxyAlias -Value `"$caddyProxyExecutablePath`""
        Add-Content -Path $PROFILE -Value $setAliasExpression
        Invoke-Expression $setAliasExpression
    }
}

# - Windows Arena Server Setup 

$pythonServerPort = 5000
$onLogonTaskName = "WindowsArena_OnLogon"
$requirementsFile = "$scriptFolder\server\requirements.txt"

# - Microsoft Visual C++ Redistributable
$vcRedistToolName = "Microsoft Visual C++ Redistributable"
$vcRedistToolDetails = Get-ToolDetails -toolsList $toolsList -toolName $vcRedistToolName
$vcRedistInstallerFilePath = "$env:TEMP\vc_redist.x64.exe"

Write-Host "Downloading and installing Microsoft Visual C++ Redistributable..."
$downloadResult = Invoke-DownloadFileFromAvailableMirrors -mirrorUrls $vcRedistToolDetails.mirrors -outfile $vcRedistInstallerFilePath
if (-not $downloadResult) {
    Write-Host "Failed to download Microsoft Visual C++ Redistributable. Please try again later or install manually."
} else {
    Start-Process -FilePath $vcRedistInstallerFilePath -ArgumentList "/install", "/quiet", "/norestart" -Wait
    Write-Host "Microsoft Visual C++ Redistributable has been installed."
}
# Keep installer behavior reproducible and always target CPython 3.10.0 rather
# than whichever python.exe appears first on PATH (LibreOffice ships one too).
Install-PythonPackages -Package "pip==24.3.1" -Arguments "--upgrade" -PythonExecutable $pythonExecutablePath
Install-PythonPackages -Package "wheel==0.45.1" -PythonExecutable $pythonExecutablePath
Install-PythonPackages -Package "pywin32==308" -PythonExecutable $pythonExecutablePath
Install-PythonPackages -Package "pywinauto==0.6.8" -PythonExecutable $pythonExecutablePath

$pywin32PostInstall = Join-Path (Split-Path $pythonExecutablePath -Parent) "Scripts\pywin32_postinstall.py"
if (Test-Path $pywin32PostInstall) {
    Write-Host "Running pywin32 post-install registration..."
    & $pythonExecutablePath $pywin32PostInstall -install
} else {
    Write-Host "pywin32 post-install script was not found at $pywin32PostInstall"
}

# Install Python packages from requirements.txt using Python's pip module
if (Test-Path $requirementsFile) {
    Write-Host "Installing required Python packages using pip from requirements file..."
    Install-PythonPackages -RequirementsPath $requirementsFile -PythonExecutable $pythonExecutablePath
} else {
    Write-Error "Requirements file not found: $requirementsFile"
    exit
}

$pywin32PostInstall = Join-Path (Split-Path $pythonExecutablePath -Parent) "Scripts\pywin32_postinstall.py"
if (Test-Path $pywin32PostInstall) {
    Write-Host "Running pywin32 post-install registration..."
    & $pythonExecutablePath $pywin32PostInstall -install
} else {
    Write-Host "pywin32 post-install script was not found at $pywin32PostInstall"
}

# Add a firewall rule to allow incoming connections on the specified port for the Python executable
$pythonServerRuleName = "PythonHTTPServer-$pythonServerPort"
if (-not (Get-NetFirewallRule -Name $pythonServerRuleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $pythonServerRuleName -Direction Inbound -Program $pythonExecutablePath -Protocol TCP -LocalPort $pythonServerPort -Action Allow -Profile Any
    Write-Host "Firewall rule added to allow traffic on port $pythonServerPort for Python"
} else {
    Write-Host "Firewall rule already exists. $pythonServerRuleName "
}

# Add a firewall rule to allow incoming connections on the specified port for the Python executable
$caddyProxyRuleName = "Allow-Caddy-Proxy"
if (-not (Get-NetFirewallRule -Name $caddyProxyRuleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $caddyProxyRuleName -Direction Inbound -Program $caddyProxyExecutablePath -Action Allow -Profile Any
    Write-Host "Firewall rule added to allow traffic on port $caddyProxyRuleName"
} else {
    Write-Host "Firewall rule already exists. $caddyProxyRuleName "
}

$onLogonScriptPath = "$scriptFolder\on-logon.ps1"
# Check if the scheduled task exists before unregistering it
if (Get-ScheduledTask -TaskName $onLogonTaskName -ErrorAction SilentlyContinue) {
    Write-Host "Scheduled task $onLogonTaskName already exists."
} else {
    Write-Host "Registering new task $onLogonTaskName..."
    Register-LogonTask -TaskName $onLogonTaskName -ScriptPath $onLogonScriptPath -LocalUser "Docker"
}

# Keep a machine-readable-enough manifest next to the golden image so every
# result can be tied to the actual guest environment that produced it.
$environmentManifestPath = "C:\winarena-environment.txt"
@(
    "windows=$((Get-CimInstance Win32_OperatingSystem).Version)"
    "python=$(& $pythonExecutablePath --version 2>&1)"
    "chrome=$((Get-Item $chromeExePath).VersionInfo.ProductVersion)"
    "libreoffice=$((Get-Item $sofficeExecutablePath).VersionInfo.ProductVersion)"
    "vlc=$((Get-Item $vlcExecutableFilePath).VersionInfo.ProductVersion)"
    ""
    "[pip-freeze]"
) | Set-Content -Path $environmentManifestPath -Encoding ASCII
& $pythonExecutablePath -m pip freeze | Add-Content -Path $environmentManifestPath -Encoding ASCII

Start-Sleep -Seconds 10
Start-ScheduledTask -TaskName $onLogonTaskName
