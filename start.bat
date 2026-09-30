@echo off
chcp 65001 >nul
cd /d %~dp0
echo ==========================================================
echo   XingFu Community - Property Management and Repair System
echo   Port: 8004    Database: property_management
echo ==========================================================
echo.
if not defined PROPERTY_DB_PASSWORD (
    echo PROPERTY_DB_PASSWORD is not set.
    set /p "PROPERTY_DB_PASSWORD=Enter the local MySQL password for this run: "
)
if not defined PROPERTY_DJANGO_SECRET_KEY set "PROPERTY_DJANGO_SECRET_KEY=property-management-local-dev-only"
if not defined PROPERTY_JWT_SECRET set "PROPERTY_JWT_SECRET=property-management-jwt-local-dev-only"
echo.
if not exist backend\static\index.html (
    echo [1/3] Frontend not built, running npm install ^& npm run build ...
    cd frontend
    call npm install
    call npm run build
    cd ..
) else (
    echo [1/3] Frontend build found, skip building.
)
echo.
echo [2/3] Import db/init.sql into MySQL first if you have not done that:
echo        mysql -uroot -p ^< db/init.sql
echo.
echo [3/3] Starting Django server at http://localhost:8004/
echo        Press Ctrl+C to stop.
echo.
cd backend
python manage.py runserver 0.0.0.0:8004 --noreload
cd ..
