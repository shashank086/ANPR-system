

## 🚀 How to Run the System

### Prerequisites

1. **Python 3.11+** installed.
2. **Tesseract OCR** installed on your machine.
   * Add its path in the `.env` file (Default: `C:\Program Files\Tesseract-OCR\tesseract.exe`).

### Setup & Startup

To start the database services and Flask web server concurrently, run the automated startup script:

```bash
# Run the complete startup script
start_anpr_system.bat
```

This script will automatically:
1. Activate the Python virtual environment (`.venv`) if present.
2. Update all dependencies from `requirements.txt`.
3. Launch the background **MongoDB Atlas Service**.
4. Start the **Flask Web Application** on `http://127.0.0.1:5000`.

### Manual Startup (System Command Prompt)

If you prefer to run the components manually using individual command prompt windows:

#### Step 1: Open a command prompt and navigate to the project directory
```cmd
cd "file path"
```

#### Step 2: Activate the virtual environment
```cmd
.venv\Scripts\activate.bat
```

#### Step 3: Run the MongoDB Atlas service
Open a **new, separate** command prompt window, navigate to the project directory, activate the virtual environment, and run:
```cmd
python backend/services/atlas_service.py
```

#### Step 4: Run the Flask Web application
In your original command prompt window (where the virtual environment is active), run:
```cmd
python backend/api/web_app.py
```

### Direct Service URLs
* 🖥️ **Web Dashboard:** [http://127.0.0.1:5000](http://127.0.0.1:5000)
* 📊 **Performance Metrics API:** [http://127.0.0.1:5000/api/performance](http://127.0.0.1:5000/api/performance)
* 🔗 **MongoDB Atlas Status:** [http://127.0.0.1:5000/api/atlas/status](http://127.0.0.1:5000/api/atlas/status)
