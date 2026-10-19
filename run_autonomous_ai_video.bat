@echo off
chcp 65001 > nul
echo =====================================================================
echo    ROBOT QUET TIN TUC AI THE GIOI VA DUNG VIDEO TU DONG 100%
echo =====================================================================
echo.

cd /d "d:\aivideo"
call "d:\aivideo\OpenMontage\.venv\Scripts\activate.bat"

echo [*] Dang quet RSS tin AI the gioi moi nhat...
echo [*] Kiem tra danh sach da xu ly de tranh trung lap...
echo [*] Tu dong viet kich ban, tong hop giong doc va render video 1080x1920...
echo.

python "d:\aivideo\auto_crawl_ai_video.py"

echo.
echo =====================================================================
echo    HOAN THANH! Video da duoc luu tai thu muc: d:\aivideo\output
echo =====================================================================
pause
