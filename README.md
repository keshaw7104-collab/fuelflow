# FuelFlow: Payment Analysis and Business Intelligence

FuelFlow is a portfolio-ready petrol-pump payment analysis project built with the requested data-analytics stack:

**Python | Pandas | NumPy | SQL | Excel | Power BI | PostgreSQL | Render**

## What each technology does

| Technology | Role in this project |
|---|---|
| Python + FastAPI | Receives, validates, imports, and exposes payment data through an API. |
| Pandas + NumPy | Cleans payment records and calculates KPIs, trends, payment-channel summaries, and exceptions. |
| PostgreSQL + SQL | Stores payments and provides reusable reporting views. |
| Excel | Supplies the controlled payment-import template. |
| Power BI | Creates the final management dashboard and real-time operational page. |
| Render | Hosts the Python API and PostgreSQL database. |

## Project structure

```text
app/                 Python FastAPI application
sql/schema.sql       PostgreSQL tables, views, and business rules
scripts/             Database migration and NumPy/Pandas demo-data generator
excel/               Validated Excel payment-import template
powerbi/              Connection guide, DAX measures, and report design
render.yaml          Render deployment blueprint
```

## Software you need

1. **Python 3.11 or newer** — install from [python.org](https://www.python.org/downloads/). Select **Add Python to PATH** during setup.
2. **VS Code** — code editor. Install the Python extension when VS Code suggests it.
3. **PostgreSQL + pgAdmin** — local database for development. Keep the username `postgres`, port `5432`, and save the password you create.
4. **Microsoft Excel** — to fill the payment-import template.
5. **Power BI Desktop** — to create the dashboard `.pbix` file. It is a Windows desktop application.
6. **Git + GitHub account** — version control and source repository.
7. **Render account** — cloud deployment.

## Run locally in VS Code

### 1. Create the local database

Open **pgAdmin 4**, right-click **Databases**, select **Create → Database**, and create:

```text
Database name: fuelflow
Owner: postgres
```

### 2. Open this project folder in VS Code

Open the folder that contains this README. In VS Code, open **Terminal → New Terminal**, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, run this once in the same terminal and repeat the activation command:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 3. Configure your local database connection

Open `.env` and replace `YOUR_PASSWORD` with the PostgreSQL password you chose:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/fuelflow
PORT=8000
SEED_DEMO_DATA=true
```

Do not upload `.env` or your database password to GitHub.

### 4. Create data and start the API

Run these commands:

```powershell
python scripts/migrate.py
python scripts/seed_demo.py
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. This is FastAPI's interactive page where you can test every API action without writing code.

## Excel workflow

1. Open [FuelFlow_Payment_Import_Template.xlsx](excel/FuelFlow_Payment_Import_Template.xlsx).
2. Read the **Instructions** worksheet.
3. Enter payment rows only in the **Payment Import** worksheet; do not change its headers.
4. In FastAPI docs, use `POST /api/import/excel` to upload the completed workbook.
5. Use `GET /api/payments/export.csv` to download the selected payment history for Excel.

## Power BI workflow

Follow [FuelFlow_PowerBI_Guide.md](powerbi/FuelFlow_PowerBI_Guide.md) exactly. It contains the PostgreSQL views, table relationships, DAX measures, visual layouts, and DirectQuery setup for real-time reporting.

For a live operational page, choose **DirectQuery** when connecting to PostgreSQL. Power BI's automatic page refresh is available only for DirectQuery sources; published-report cadence depends on the Power BI workspace/capacity configuration. [Microsoft guidance](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-automatic-page-refresh)

## Deploy to GitHub and Render

1. Create a new empty GitHub repository named `fuelflow-python-bi-dashboard`.
2. In the VS Code terminal, run:

   ```powershell
   git init
   git add .
   git commit -m "Initial FuelFlow Python BI project"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/fuelflow-python-bi-dashboard.git
   git push -u origin main
   ```

3. In Render, select **New → Blueprint**, connect the GitHub repository, and approve `render.yaml`.
4. Render creates the Python web service and PostgreSQL database. It runs the SQL migration before each deployment.
5. Set `SEED_DEMO_DATA=false` after demonstrating the sample dashboard, before importing real station payments.

The Render service uses a private PostgreSQL connection automatically. For Power BI, use the external PostgreSQL connection details displayed in Render's database dashboard and keep those credentials only in Power BI.

## Portfolio talking points

- Designed a payment-data pipeline from Excel and API input through PostgreSQL to Power BI.
- Used Python, Pandas, and NumPy for automated KPI, payment-channel, trend, and exception analysis.
- Created SQL views for reusable daily, payment-app, pump/shift, and settlement reporting.
- Built a Power BI model with custom DAX measures, DirectQuery, and real-time refresh design.
- Deployed the API and database configuration through Render Blueprint infrastructure-as-code.
