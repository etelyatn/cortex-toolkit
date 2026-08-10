: << 'CMDBLOCK'
@echo off
REM Cross-platform wrapper for Cortex Toolkit hook scripts.
REM On Windows: cmd.exe finds Git Bash even when bash.exe is not on PATH.
REM On Unix: the shell skips this block and runs the script at the bottom.

if "%~1"=="" (
    echo run-hook.cmd: missing script name >&2
    exit /b 1
)

set "HOOK_DIR=%~dp0"

if exist "C:\Program Files\Git\bin\bash.exe" (
    "C:\Program Files\Git\bin\bash.exe" -lc "script=$(cygpath -u \"$1\"); shift; \"$script\" \"$@\"" _ "%HOOK_DIR%%~1" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)
if exist "C:\Program Files (x86)\Git\bin\bash.exe" (
    "C:\Program Files (x86)\Git\bin\bash.exe" -lc "script=$(cygpath -u \"$1\"); shift; \"$script\" \"$@\"" _ "%HOOK_DIR%%~1" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

where bash >nul 2>nul
if %ERRORLEVEL% equ 0 (
    bash -lc "script=$(cygpath -u \"$1\" 2>/dev/null || printf '%s' \"$1\"); shift; \"$script\" \"$@\"" _ "%HOOK_DIR%%~1" %2 %3 %4 %5 %6 %7 %8 %9
    exit /b %ERRORLEVEL%
)

echo Cortex Toolkit hook requires Git Bash or another bash.exe on PATH. >&2
exit /b 2
CMDBLOCK

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$1"
shift
exec bash "${SCRIPT_DIR}/${SCRIPT_NAME}" "$@"
