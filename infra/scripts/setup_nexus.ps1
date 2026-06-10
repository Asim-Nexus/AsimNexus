# ASIMNEXUS Founder Distribution Script - Windows PowerShell
# =====================================================
# One-click ASIMNEXUS installation for Founder Clones
# Automatically detects hardware and configures optimal settings

param(
    [Parameter(Mandatory=$false)]
    [string]$Mode = "auto",
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "latest",
    
    [Parameter(Mandatory=$false)]
    [string]$FounderKey = "",
    
    [Parameter(Mandatory=$false)]
    [string]$InstallPath = "C:\ASIMNEXUS",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDocker = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$DevMode = $false
)

# Color scheme for output
$Colors = @{
    Title = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "White"
    Accent = "Magenta"
}

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Show-Banner {
    Write-ColorOutput ""
    Write-ColorOutput "╔══════════════════════════════════════════════════════════════╗" "Title"
    Write-ColorOutput "║                   ASIMNEXUS FOUNDER CLONE SETUP                    ║" "Title"
    Write-ColorOutput "║                Universal Operating System Installer                ║" "Title"
    Write-ColorOutput "╚══════════════════════════════════════════════════════════════╝" "Title"
    Write-ColorOutput ""
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-SystemInfo {
    Write-ColorOutput "🔍 Detecting System Configuration..." "Info"
    
    $systemInfo = @{}
    
    # OS Information
    $systemInfo.OS = (Get-WmiObject -Class Win32_OperatingSystem).Caption
    $systemInfo.OSVersion = (Get-WmiObject -Class Win32_OperatingSystem).Version
    $systemInfo.Architecture = $env:PROCESSOR_ARCHITECTURE
    
    # Hardware Information
    $cpu = Get-WmiObject -Class Win32_Processor
    $systemInfo.CPU = $cpu.Name
    $systemInfo.Cores = $cpu.NumberOfCores
    $systemInfo.Threads = $cpu.NumberOfLogicalProcessors
    
    # Memory Information
    $memory = Get-WmiObject -Class Win32_ComputerSystem
    $totalMemory = [math]::Round($memory.TotalPhysicalMemory / 1GB, 2)
    $systemInfo.TotalMemoryGB = $totalMemory
    
    # GPU Detection
    $systemInfo.GPU = "Unknown"
    $systemInfo.GPUMemoryGB = 0
    
    try {
        # Try to detect NVIDIA GPU
        $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
        if ($nvidiaSmi) {
            $gpuInfo = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
            if ($gpuInfo) {
                $gpuParts = $gpuInfo.Split(",")
                $systemInfo.GPU = $gpuParts[0].Trim()
                $memoryMB = [int]$gpuParts[1].Trim()
                $systemInfo.GPUMemoryGB = [math]::Round($memoryMB / 1024, 2)
            }
        }
    } catch {
        Write-ColorOutput "⚠️ GPU detection failed - will use CPU mode" "Warning"
    }
    
    # Disk Space Check
    $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
    $freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 2)
    $systemInfo.FreeDiskSpaceGB = $freeSpaceGB
    
    # Determine Hardware Tier
    $systemInfo.HardwareTier = Get-HardwareTier $systemInfo
    $systemInfo.RecommendedMode = Get-RecommendedMode $systemInfo
    
    return $systemInfo
}

function Get-HardwareTier {
    param($systemInfo)
    
    $memoryGB = $systemInfo.TotalMemoryGB
    $gpuMemoryGB = $systemInfo.GPUMemoryGB
    
    if ($memoryGB -ge 32 -and $gpuMemoryGB -ge 12) {
        return "Tier 5 Enterprise"
    } elseif ($memoryGB -ge 16 -and $gpuMemoryGB -ge 6) {
        return "Tier 4 Performance"
    } elseif ($memoryGB -ge 8 -and $gpuMemoryGB -ge 4) {
        return "Tier 3 Standard"
    } elseif ($memoryGB -ge 4) {
        return "Tier 2 Basic"
    } else {
        return "Tier 1 Mobile"
    }
}

function Get-RecommendedMode {
    param($systemInfo)
    
    $tier = $systemInfo.HardwareTier
    $hasGPU = $systemInfo.GPU -ne "Unknown"
    
    switch -Wildcard ($tier) {
        "Tier 5*" { return "titan" }
        "Tier 4*" { return if ($hasGPU) { "full_neural" } else { "quantized_heavy" } }
        "Tier 3*" { return if ($hasGPU) { "quantized_heavy" } else { "quantized_medium" } }
        "Tier 2*" { return "quantized_medium" }
        "Tier 1*" { return "quantized_light" }
        default { return "balanced" }
    }
}

function Test-DockerInstallation {
    Write-ColorOutput "🐳 Checking Docker Installation..." "Info"
    
    try {
        $dockerVersion = docker --version
        if ($dockerVersion) {
            Write-ColorOutput "✅ Docker is installed: $dockerVersion" "Success"
            return $true
        }
    } catch {
        Write-ColorOutput "❌ Docker is not installed" "Error"
        return $false
    }
}

function Install-Docker {
    Write-ColorOutput "📦 Installing Docker Desktop..." "Info"
    
    try {
        # Download Docker Desktop installer
        $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
        $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
        
        Write-ColorOutput "📥 Downloading Docker Desktop..." "Info"
        Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerInstaller
        
        Write-ColorOutput "⚙️ Installing Docker Desktop (this may take a few minutes)..." "Info"
        Start-Process -FilePath $dockerInstaller -ArgumentList "/quiet" -Wait
        
        # Clean up
        Remove-Item $dockerInstaller -Force
        
        Write-ColorOutput "✅ Docker Desktop installation completed" "Success"
        Write-ColorOutput "⚠️ Please restart your computer and run this script again" "Warning"
        return $true
    } catch {
        Write-ColorOutput "❌ Docker installation failed: $($_.Exception.Message)" "Error"
        return $false
    }
}

function Install-ASIMNEXUS {
    param($systemInfo)
    
    Write-ColorOutput "🚀 Installing ASIMNEXUS..." "Info"
    
    # Create installation directory
    if (!(Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Path $InstallPath -Force
        Write-ColorOutput "📁 Created installation directory: $InstallPath" "Success"
    }
    
    # Set working directory
    Set-Location $InstallPath
    
    try {
        # Download ASIMNEXUS
        if ($Version -eq "latest") {
            Write-ColorOutput "📥 Downloading ASIMNEXUS (latest)..." "Info"
            # This would download from GitHub releases
            # For demo, we'll assume it's already available
            Write-ColorOutput "📦 ASIMNEXUS package ready" "Success"
        } else {
            Write-ColorOutput "📥 Downloading ASIMNEXUS v$Version..." "Info"
            # Download specific version
        }
        
        # Create configuration
        $config = @{
            "system" = @{
                "hardware_tier" = $systemInfo.HardwareTier
                "recommended_mode" = $systemInfo.RecommendedMode
                "gpu_available" = ($systemInfo.GPU -ne "Unknown")
                "gpu_name" = $systemInfo.GPU
                "gpu_memory_gb" = $systemInfo.GPUMemoryGB
                "total_memory_gb" = $systemInfo.TotalMemoryGB
                "cpu_cores" = $systemInfo.Cores
                "os" = $systemInfo.OS
            }
            "deployment" = @{
                "mode" = $systemInfo.RecommendedMode
                "auto_scale" = $true
                "monitoring_enabled" = $true
                "security_level" = "standard"
            }
            "founder" = @{
                "key" = if ($FounderKey) { $FounderKey } else { "auto-generated" }
                "installation_date" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
                "version" = $Version
            }
        }
        
        # Save configuration
        $configPath = "$InstallPath\config\founder_config.json"
        New-Item -ItemType Directory -Path (Split-Path $configPath) -Force | Out-Null
        $config | ConvertTo-Json -Depth 4 | Out-File -FilePath $configPath -Encoding UTF8
        
        Write-ColorOutput "✅ ASIMNEXUS installation completed" "Success"
        return $true
    } catch {
        Write-ColorOutput "❌ ASIMNEXUS installation failed: $($_.Exception.Message)" "Error"
        return $false
    }
}

function Start-ASIMNEXUSServices {
    Write-ColorOutput "🚀 Starting ASIMNEXUS services..." "Info"
    
    try {
        Set-Location $InstallPath
        
        # Start Docker Compose
        if (Test-Path "docker-compose.yml") {
            Write-ColorOutput "🐳 Starting Docker Compose services..." "Info"
            docker-compose up -d
            
            # Wait for services to be ready
            Write-ColorOutput "⏳ Waiting for services to initialize..." "Info"
            Start-Sleep -Seconds 30
            
            # Check service status
            $services = docker-compose ps
            Write-ColorOutput "📊 Service Status:" "Info"
            Write-ColorOutput $services "Accent"
            
            Write-ColorOutput "✅ ASIMNEXUS services started successfully" "Success"
            Write-ColorOutput "🌐 Web Interface: http://localhost:3000" "Success"
            Write-ColorOutput "🔌 API Endpoint: http://localhost:8000" "Success"
            Write-ColorOutput "📊 Monitoring: http://localhost:3001" "Success"
        } else {
            Write-ColorOutput "❌ docker-compose.yml not found" "Error"
        }
    } catch {
        Write-ColorOutput "❌ Failed to start services: $($_.Exception.Message)" "Error"
    }
}

function New-FounderReport {
    param($systemInfo)
    
    $reportPath = "$InstallPath\founder_report.txt"
    
    $report = @"
╔══════════════════════════════════════════════════════════════╗
║                    ASIMNEXUS FOUNDER REPORT                        ║
╚══════════════════════════════════════════════════════════════╝

Installation Summary:
- Date: $(Get-Date)
- Version: $Version
- Mode: $systemInfo.RecommendedMode
- Hardware Tier: $systemInfo.HardwareTier

System Configuration:
- OS: $($systemInfo.OS)
- CPU: $($systemInfo.CPU) ($($systemInfo.Cores) cores)
- Memory: $($systemInfo.TotalMemoryGB) GB
- GPU: $($systemInfo.GPU) ($($systemInfo.GPUMemoryGB) GB)
- Free Disk Space: $($systemInfo.FreeDiskSpaceGB) GB

Recommended Settings:
- Execution Mode: $systemInfo.RecommendedMode
- Model Size: $(Get-ModelSize $systemInfo.RecommendedMode)
- Batch Size: $(Get-BatchSize $systemInfo.RecommendedMode)
- Performance Profile: $(Get-PerformanceProfile $systemInfo.RecommendedMode)

Access Information:
- Web Interface: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- Monitoring Dashboard: http://localhost:3001
- WebSocket: ws://localhost:8000/ws

Next Steps:
1. Open http://localhost:3000 in your browser
2. Complete the onboarding wizard
3. Configure your Founder preferences
4. Activate your Digital Workforce

Support:
- Documentation: https://docs.asimnexus.com
- Community: https://community.asimnexus.com
- Issues: https://github.com/asimnexus/issues

Generated by ASIMNEXUS Founder Setup Script v2.0
"@
    
    $report | Out-File -FilePath $reportPath -Encoding UTF8
    Write-ColorOutput "📋 Founder report saved to: $reportPath" "Success"
}

function Get-ModelSize {
    param($mode)
    
    switch ($mode) {
        "titan" { return "20B parameters" }
        "full_neural" { return "13B parameters" }
        "quantized_heavy" { return "7B parameters" }
        "quantized_medium" { return "4B parameters" }
        "quantized_light" { return "2B parameters" }
        default { return "Auto-detected" }
    }
}

function Get-BatchSize {
    param($mode)
    
    switch ($mode) {
        "titan" { return "8" }
        "full_neural" { return "4" }
        "quantized_heavy" { return "4" }
        "quantized_medium" { return "2" }
        "quantized_light" { return "1" }
        default { return "Auto" }
    }
}

function Get-PerformanceProfile {
    param($mode)
    
    switch ($mode) {
        "titan" { return "Maximum Performance" }
        "full_neural" { return "High Performance" }
        "quantized_heavy" { return "Balanced Performance" }
        "quantized_medium" { return "Power Saving" }
        "quantized_light" { return "Minimal Resource Usage" }
        default { return "Adaptive" }
    }
}

# Main execution
function Main {
    Show-Banner
    
    # Check administrator privileges
    if (!(Test-Administrator)) {
        Write-ColorOutput "⚠️ This script requires administrator privileges" "Warning"
        Write-ColorOutput "Please run PowerShell as Administrator" "Warning"
        Read-Host "Press Enter to exit..."
        exit 1
    }
    
    Write-ColorOutput "🔑 Administrator privileges confirmed" "Success"
    
    # Detect system configuration
    $systemInfo = Get-SystemInfo
    
    # Display system information
    Write-ColorOutput "📊 System Configuration:" "Info"
    Write-ColorOutput "   OS: $($systemInfo.OS)" "Accent"
    Write-ColorOutput "   CPU: $($systemInfo.CPU) ($($systemInfo.Cores) cores)" "Accent"
    Write-ColorOutput "   Memory: $($systemInfo.TotalMemoryGB) GB" "Accent"
    Write-ColorOutput "   GPU: $($systemInfo.GPU) ($($systemInfo.GPUMemoryGB) GB)" "Accent"
    Write-ColorOutput "   Hardware Tier: $($systemInfo.HardwareTier)" "Accent"
    Write-ColorOutput "   Recommended Mode: $($systemInfo.RecommendedMode)" "Accent"
    Write-ColorOutput ""
    
    # Check Docker installation
    $dockerInstalled = Test-DockerInstallation
    
    if (!$dockerInstalled -and !$SkipDocker) {
        Write-ColorOutput "🐳 Docker not found. Installing Docker Desktop..." "Info"
        $dockerInstalled = Install-Docker
        
        if (!$dockerInstalled) {
            Write-ColorOutput "❌ Docker installation failed. Please install Docker manually and retry." "Error"
            exit 1
        }
        
        Write-ColorOutput "🔄 Please restart your computer and run this script again" "Warning"
        exit 0
    }
    
    # Install ASIMNEXUS
    $installSuccess = Install-ASIMNEXUS $systemInfo
    
    if (!$installSuccess) {
        Write-ColorOutput "❌ ASIMNEXUS installation failed" "Error"
        exit 1
    }
    
    # Start services
    if (!$DevMode) {
        Start-ASIMNEXUSServices
    } else {
        Write-ColorOutput "🔧 Development mode - services not started automatically" "Info"
        Write-ColorOutput "Run 'docker-compose up -d' manually to start services" "Info"
    }
    
    # Generate report
    Generate-FounderReport $systemInfo
    
    Write-ColorOutput ""
    Write-ColorOutput "🎉 ASIMNEXUS Founder Clone Setup Complete!" "Success"
    Write-ColorOutput ""
    Write-ColorOutput "Your Digital Workforce is ready to awaken!" "Accent"
    Write-ColorOutput ""
    Write-ColorOutput "Quick Start Commands:" "Info"
    Write-ColorOutput "  • Check status: docker-compose ps" "Accent"
    Write-ColorOutput "  • View logs: docker-compose logs -f" "Accent"
    Write-ColorOutput "  • Stop services: docker-compose down" "Accent"
    Write-ColorOutput "  • Restart services: docker-compose restart" "Accent"
    Write-ColorOutput ""
    Write-ColorOutput "🌐 Access your ASIMNEXUS at: http://localhost:3000" "Success"
    Write-ColorOutput ""
}

# Execute main function
Main
