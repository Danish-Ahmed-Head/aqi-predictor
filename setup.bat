@echo off
echo ==================================
echo AQI Predictor - Windows Setup
echo ==================================
echo.

REM Check Python version
echo Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.9 or 3.10 from python.org
    pause
    exit /b 1
)
echo.

REM Create directories
echo Creating project directories...
if not exist data mkdir data
if not exist models mkdir models
if not exist reports mkdir reports
if not exist notebooks mkdir notebooks
if not exist src mkdir src
if not exist app mkdir app
if not exist .github\workflows mkdir .github\workflows
echo Done.
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment!
    pause
    exit /b 1
)
echo Done.
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo Done.
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo Done.
echo.

REM Install dependencies
echo Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo Done.
echo.

REM Create .env file
if not exist .env (
    echo Creating .env file...
    copy .env.template .env
    echo Done.
    echo.
    echo WARNING: Please edit .env file and add your API keys!
) else (
    echo .env file already exists.
)
echo.

REM Create Streamlit secrets directory
if not exist .streamlit mkdir .streamlit
if not exist .streamlit\secrets.toml (
    echo Creating Streamlit secrets file...
    (
        echo [default]
        echo HOPSWORKS_API_KEY = "your_key_here"
    ) > .streamlit\secrets.toml
    echo Done.
    echo.
    echo WARNING: Please edit .streamlit\secrets.toml and add your API key!
) else (
    echo Streamlit secrets file already exists.
)
echo.

echo ==================================
echo Setup Complete!
echo ==================================
echo.
echo NEXT STEPS:
echo 1. Edit .env file and add your API keys
echo    - AQICN_TOKEN (from https://aqicn.org/data-platform/token/)
echo    - HOPSWORKS_API_KEY (from https://app.hopsworks.ai/)
echo.
echo 2. Activate virtual environment:
echo    venv\Scripts\activate
echo.
echo 3. Collect initial data (backfill 7 days):
echo    python src\feature_pipeline.py --backfill 7
echo.
echo 4. Train the model:
echo    python src\training_pipeline.py
echo.
echo 5. Run the dashboard:
echo    streamlit run app\streamlit_app.py
echo.
echo For more information, see README.md
echo.
pause