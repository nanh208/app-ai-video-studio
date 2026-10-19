@echo off
chcp 65001 >nul
echo ========================================================
echo   🚀 TỰ ĐỘNG ĐẨY MÃ NGUỒN LÊN GITHUB BẰNG TOKEN (PAT)
echo ========================================================
echo.

set /p GITHUB_USER="1. Nhập GitHub Username của bạn (ví dụ: buiminhkhang27032023-afk): "
if "%GITHUB_USER%"=="" (
    echo [Lỗi] Chưa nhập Username!
    pause
    exit /b 1
)

set /p REPO_NAME="2. Nhập tên Repository trên GitHub (ví dụ: ai-video-studio): "
if "%REPO_NAME%"=="" (
    echo [Lỗi] Chưa nhập tên Repository!
    pause
    exit /b 1
)

set /p GITHUB_TOKEN="3. Dán GitHub Personal Access Token (ghp_...): "
if "%GITHUB_TOKEN%"=="" (
    echo [Lỗi] Chưa nhập Token!
    pause
    exit /b 1
)

echo.
echo [1/3] Đang kiểm tra nhánh Git...
git branch -M main

echo [2/3] Đang cấu hình Remote Origin...
git remote remove origin 2>nul
git remote add origin https://%GITHUB_TOKEN%@github.com/%GITHUB_USER%/%REPO_NAME%.git

echo [3/3] Đang đẩy toàn bộ mã nguồn lên GitHub...
git push -u origin main --force

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   🏆 ĐẨY MÃ NGUỒN LÊN GITHUB THÀNH CÔNG!
    echo   👉 Repository: https://github.com/%GITHUB_USER%/%REPO_NAME%
    echo ========================================================
    REM Xóa token khỏi remote URL để bảo mật tuyệt đối
    git remote set-url origin https://github.com/%GITHUB_USER%/%REPO_NAME%.git
) else (
    echo.
    echo [Thất bại] Kiểm tra lại Token hoặc chắc chắn rằng Repository đã được tạo trên GitHub!
)

echo.
pause
