# 🔭 Galileo Decile Tracking Dashboard

A professional Streamlit dashboard for tracking stock decile performance across global regions, powered exclusively by your Google Drive data.

## ✨ Features

### 📊 Dashboard
- Real-time stock data from your Google Drive
- Decile distribution visualizations
- Region breakdown charts
- CSV export functionality

### 🔍 Stock Search
- Search by **ticker symbol** (e.g., "F", "AAPL", "7203")
- Search by **company name** (e.g., "Ford", "Apple", "Toyota")
- Results grouped by region

### 📅 Time Period Filters
- 3 Months / 6 Months / 9 Months / 12 Months
- Custom date range selection

### 🏭 Sector Analysis
- View stocks by sector within each region
- **Region-separated sector views** (Japan Tech ≠ US Tech)
- Sector performance heatmaps
- Cross-region comparisons

### 📁 Synced Files
- View all synced files from Google Drive
- Automatic region detection from filenames
- Date extraction from filenames
- File sync status tracking

---

## 📁 Your File Naming Convention

The dashboard automatically recognizes your file naming pattern:

| Filename | Detected Region | Detected Date |
|----------|-----------------|---------------|
| `S&P500 March 11 2025.xlsx` | US | March 11, 2025 |
| `S&P500 Jan 28 2025.xlsx` | US | January 28, 2025 |
| `Japan Jan 08 2026.xlsx` | Japan | January 8, 2026 |
| `GLOBAL Ex US Mar 11 2025.xlsx` | Global Ex US | March 11, 2025 |
| `Europe Jan 28 2025.xlsx` | Europe | January 28, 2025 |
| `APAC Ex JPY Dec 10 2025.xlsx` | APAC Ex Japan | December 10, 2025 |

---

## 🌍 Supported Regions

- **US** - S&P500, Nasdaq, Russell
- **Europe** - European stocks
- **UK** - FTSE stocks
- **APAC Ex Japan** - Asia Pacific excluding Japan
- **Japan** - Japanese stocks
- **China** - Chinese stocks
- **Global** - Global indices
- **Global Ex US** - International excluding US

---

## 📊 Expected Data Format

Your Excel/CSV files should contain these columns:

| Column | Required | Alternatives |
|--------|----------|--------------|
| Ticker | ✅ | Symbol, Stock, Code |
| Company Name | ✅ | Company, Name |
| Current Decile | ✅ | Decile |
| Previous Decile | ✅ | Prior Decile |
| Sector | Optional | Industry |
| Score | Optional | Total Score |
| Market Cap | Optional | Mkt Cap |

---

## 🚀 Deployment to Streamlit Cloud

### Step 1: Prepare Your Repository

Upload these files to GitHub:
```
your-repo/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

### Step 2: Set Up Google Cloud

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the **Google Drive API**

2. **Create Service Account**
   - Go to IAM & Admin > Service Accounts
   - Create a new service account
   - Grant it "Viewer" role
   - Create and download JSON key

3. **Share Your Drive Folder**
   - Open Google Drive
   - Right-click your data folder
   - Share with the service account email

### Step 3: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Connect your GitHub repository
3. In **Advanced Settings > Secrets**, add:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service@project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

4. Deploy!

---

## 🔧 Local Development

```bash
# Clone repository
git clone https://github.com/your-username/galileo-dashboard.git
cd galileo-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create secrets file
mkdir -p .streamlit
# Add your credentials to .streamlit/secrets.toml

# Run
streamlit run app.py
```

---

## 📊 Decile Filters

| Filter | Description |
|--------|-------------|
| All Decile Movements | Show all stocks |
| Entering Top 2 Deciles | Stocks moving into decile 1 or 2 from 3+ |
| Entering Bottom 2 Deciles | Stocks moving into decile 9 or 10 from 8- |
| Moving +3 Deciles | Stocks improving by 3+ decile positions |
| Moving +5 Deciles | Stocks improving by 5+ decile positions |

---

**Built for Oxtan Capital Limited** | Galileo Quantitative Investment System
