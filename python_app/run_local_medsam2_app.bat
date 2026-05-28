@echo off
setlocal

set "REPO=%~dp0.."
for %%I in ("%REPO%") do set "REPO=%%~fI"

set "LANGSAM_INFER_CMD="

set "MEDSAM_INFER_CMD=%REPO%\.model_envs\medsam_env\Scripts\python.exe %REPO%\scripts\model_bridges\medsam_bridge.py"
set "MEDSAM_REPO_PATH=%REPO%\.model_envs\MedSAM"
set "MEDSAM_CHECKPOINT=%REPO%\.models\MedSAM\medsam_vit_b.pth"

set "MEDSAM2_INFER_CMD=%REPO%\.model_envs\medsam2_env\Scripts\python.exe %REPO%\scripts\model_bridges\medsam2_bridge.py"
set "MEDSAM2_REPO_PATH=%REPO%\.model_envs\MedSAM2"
set "MEDSAM2_CHECKPOINT=%REPO%\.models\MedSAM2\MedSAM2_latest.pt"

set "HF_HOME=%REPO%\.model_cache\hf"
set "TORCH_HOME=%REPO%\.model_cache\torch"
set "XDG_CACHE_HOME=%REPO%\.model_cache\xdg"
set "TEMP=%REPO%\.model_cache\tmp"
set "TMP=%REPO%\.model_cache\tmp"

if not exist "%TEMP%" mkdir "%TEMP%"

pushd "%REPO%"
python "python_app\main.py"
popd
