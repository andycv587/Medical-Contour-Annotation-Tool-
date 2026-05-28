param(
    [switch]$All,
    [switch]$Cellpose,
    [switch]$LangSAM,
    [switch]$MedSAM,
    [switch]$MedSAM2,
    [string]$BaseDir = ".model_envs",
    [string]$Python = "python",
    [ValidateSet("cpu", "cu124")]
    [string]$Torch = "cpu"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$CacheDir = Join-Path $ProjectRoot ".model_cache"
$env:HF_HOME = Join-Path $CacheDir "hf"
$env:TORCH_HOME = Join-Path $CacheDir "torch"
$env:XDG_CACHE_HOME = Join-Path $CacheDir "xdg"
$env:PIP_CACHE_DIR = Join-Path $CacheDir "pip"
$env:CELLPOSE_LOCAL_MODELS_PATH = Join-Path $CacheDir "cellpose"
$env:TEMP = Join-Path $CacheDir "tmp"
$env:TMP = Join-Path $CacheDir "tmp"
New-Item -ItemType Directory -Force $env:HF_HOME,$env:TORCH_HOME,$env:XDG_CACHE_HOME,$env:PIP_CACHE_DIR,$env:CELLPOSE_LOCAL_MODELS_PATH,$env:TEMP | Out-Null

function New-BackendEnv {
    param([string]$Name)
    $envDir = Join-Path $BaseDir $Name
    if (!(Test-Path $envDir)) {
        & $Python -m venv $envDir
    }
    $envDir = (Resolve-Path $envDir).Path
    $py = Join-Path $envDir "Scripts\python.exe"
    & $py -m pip install --upgrade pip | Out-Host
    return $py
}

function Install-Torch {
    param(
        [string]$PythonExe,
        [string[]]$Packages = @("torch", "torchvision")
    )
    if ($Torch -eq "cu124") {
        & $PythonExe -m pip install @Packages --index-url https://download.pytorch.org/whl/cu124
    } else {
        & $PythonExe -m pip install @Packages --index-url https://download.pytorch.org/whl/cpu
    }
}

if ($All) {
    $Cellpose = $true
    $LangSAM = $true
    $MedSAM = $true
    $MedSAM2 = $true
}

if (!(Test-Path $BaseDir)) {
    New-Item -ItemType Directory -Force $BaseDir | Out-Null
}

if ($Cellpose) {
    $py = New-BackendEnv "cellpose"
    & $py -m pip install cellpose packaging
    Write-Host "Cellpose env ready: $py"
    $bridge = Join-Path $ProjectRoot "scripts\model_bridges\cellpose_bridge.py"
    Write-Host "Cellpose command for configs/model_registry.local.yaml:"
    Write-Host "`"$py`" `"$bridge`""
}

if ($LangSAM) {
    $py = New-BackendEnv "langsam"
    Install-Torch -PythonExe $py
    & $py -m pip install -U git+https://github.com/luca-medeiros/lang-segment-anything.git
    Write-Host "LangSAM env ready: $py"
    $bridge = Join-Path $ProjectRoot "scripts\model_bridges\langsam_bridge.py"
    Write-Host "LangSAM command for configs/model_registry.local.yaml:"
    Write-Host "`"$py`" `"$bridge`""
}

if ($MedSAM) {
    $repo = Join-Path $BaseDir "MedSAM"
    if (!(Test-Path $repo)) {
        git clone https://github.com/bowang-lab/MedSAM $repo
    }
    $py = New-BackendEnv "medsam_env"
    Install-Torch -PythonExe $py
    & $py -m pip install -e $repo
    Write-Host "MedSAM repo/env ready. Download checkpoint manually and record checkpoint_path/SHA256."
    Write-Host "Repo: $repo"
    $bridge = Join-Path $ProjectRoot "scripts\model_bridges\medsam_bridge.py"
    Write-Host "MedSAM command for configs/model_registry.local.yaml:"
    Write-Host "`"$py`" `"$bridge`""
}

if ($MedSAM2) {
    $repo = Join-Path $BaseDir "MedSAM2"
    if (!(Test-Path $repo)) {
        git clone https://github.com/bowang-lab/MedSAM2 $repo
    }
    $py = New-BackendEnv "medsam2_env"
    Install-Torch -PythonExe $py -Packages @("torch==2.5.1", "torchvision==0.20.1")
    & $py -m pip install -e "$repo[dev]"
    Write-Host "MedSAM2 repo/env ready. Run upstream download.sh or download Hugging Face checkpoints, then record checkpoint_path/SHA256."
    Write-Host "Repo: $repo"
    $bridge = Join-Path $ProjectRoot "scripts\model_bridges\medsam2_bridge.py"
    Write-Host "MedSAM2 bridge contract command for configs/model_registry.local.yaml:"
    Write-Host "`"$py`" `"$bridge`""
    Write-Host "Note: this MedSAM2 bridge still needs a site-specific MEDSAM2_UPSTREAM_CMD adapter before real inference."
}

Write-Host ""
Write-Host "Torch wheel channel: $Torch. Use -Torch cu124 for CUDA 12.4 wheels when your machine is ready for GPU installs."
Write-Host "Next: fill configs\andy_real_run_answers.template.yaml or copy it to a local answers file, then run:"
Write-Host "python scripts\create_local_config_from_answers.py --answers configs\andy_real_run_answers.template.yaml --output-dir configs"
