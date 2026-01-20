"""
Galileo Decile Tracking Dashboard
================================
A Streamlit dashboard for tracking stock decile performance across regions.
Syncs with Google Drive for data management.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
import os
import json
from io import StringIO, BytesIO
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Galileo Decile Tracker",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM STYLING
# =============================================================================
st.markdown("""
<style>
    /* Main theme */
    :root {
        --primary-color: #1a365d;
        --secondary-color: #2c5282;
        --accent-color: #4299e1;
        --success-color: #48bb78;
        --warning-color: #ed8936;
        --background-dark: #0f1419;
        --background-card: #1a202c;
        --text-primary: #e2e8f0;
        --text-secondary: #a0aec0;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1a365d 0%, #2c5282 50%, #2d3748 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .main-header h1 {
        color: #ffffff;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-header p {
        color: #a0aec0;
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(145deg, #1a202c, #2d3748);
        border: 1px solid #4a5568;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4299e1;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Status indicators */
    .status-synced {
        color: #48bb78;
        font-weight: 600;
    }
    
    .status-pending {
        color: #ed8936;
        font-weight: 600;
    }
    
    /* Data table styling */
    .dataframe {
        font-size: 0.85rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #4299e1, #3182ce);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #3182ce, #2c5282);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4);
    }
    
    /* Search box styling */
    .search-container {
        background: #2d3748;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    /* Sector card */
    .sector-card {
        background: linear-gradient(145deg, #2d3748, #1a202c);
        border: 1px solid #4a5568;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Info box */
    .setup-box {
        background: linear-gradient(145deg, #2d3748, #1a202c);
        border: 2px solid #4299e1;
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# REGION MAPPING CONFIGURATION - MATCHED TO YOUR FILE NAMES
# =============================================================================
REGION_MAPPINGS = {
    "US": ["s&p500", "s&p 500", "sp500", "us", "usa", "nasdaq", "russell", "dow", "american"],
    "Europe": ["europe", "european", "eu", "stoxx", "euro stoxx", "ftse developed europe", "msci europe"],
    "UK": ["uk", "united kingdom", "ftse", "ftse100", "ftse 100", "ftse250", "british", "london"],
    "APAC Ex Japan": ["apac ex jpy", "apac ex japan", "apac", "asia pacific", "asia", "asian", "pacific", "emerging asia", "asean"],
    "Japan": ["japan", "japanese", "nikkei", "topix", "tokyo"],
    "China": ["china", "chinese", "shanghai", "shenzhen", "hang seng", "hsi", "csi", "a-shares", "h-shares"],
    "Global": ["global", "world", "msci world", "acwi", "all country", "worldwide"],
    "Global Ex US": ["global ex us", "global ex-us", "world ex us", "international", "eafe", "ex-us", "non-us"]
}

REGION_OPTIONS = ["All Regions", "US", "Europe", "UK", "APAC Ex Japan", "Japan", "China", "Global", "Global Ex US"]

DECILE_OPTIONS = [
    "All Decile Movements",
    "Entering Top 2 Deciles",
    "Entering Bottom 2 Deciles",
    "Moving +3 Deciles",
    "Moving +5 Deciles"
]

# Month name mappings for date parsing
MONTH_MAPPINGS = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12
}

# Sector categories
SECTORS = [
    "All Sectors",
    "Technology",
    "Healthcare",
    "Financials",
    "Consumer Discretionary",
    "Consumer Staples",
    "Industrials",
    "Energy",
    "Materials",
    "Utilities",
    "Real Estate",
    "Communication Services"
]

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
if 'synced_files' not in st.session_state:
    st.session_state.synced_files = []

if 'stock_data' not in st.session_state:
    st.session_state.stock_data = pd.DataFrame()

if 'last_sync' not in st.session_state:
    st.session_state.last_sync = None

if 'drive_connected' not in st.session_state:
    st.session_state.drive_connected = False

# =============================================================================
# GOOGLE DRIVE INTEGRATION
# =============================================================================
def get_google_drive_service():
    """Initialize Google Drive API service using Streamlit secrets."""
    try:
        if 'gcp_service_account' in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            service = build('drive', 'v3', credentials=credentials)
            return service
        else:
            return None
    except Exception as e:
        st.error(f"Error connecting to Google Drive: {str(e)}")
        return None

def extract_date_from_filename(filename):
    """
    Extract date from filename using your naming convention.
    Handles formats like: "S&P500 March 11 2025.xlsx", "Japan Jan 08 2026.xlsx"
    """
    filename_lower = filename.lower()
    
    # Pattern 1: Month Name Day Year (e.g., "March 11 2025", "Jan 28 2025")
    pattern1 = r'([a-zA-Z]+)\s+(\d{1,2})\s+(\d{4})'
    match = re.search(pattern1, filename, re.IGNORECASE)
    if match:
        month_str = match.group(1).lower()
        day = int(match.group(2))
        year = int(match.group(3))
        
        if month_str in MONTH_MAPPINGS:
            month = MONTH_MAPPINGS[month_str]
            try:
                return datetime(year, month, day)
            except ValueError:
                pass
    
    # Pattern 2: YYYY-MM-DD
    pattern2 = r'(\d{4})-(\d{2})-(\d{2})'
    match = re.search(pattern2, filename)
    if match:
        try:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass
    
    # Pattern 3: YYYYMMDD
    pattern3 = r'(\d{4})(\d{2})(\d{2})'
    match = re.search(pattern3, filename)
    if match:
        try:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass
    
    return None

def extract_region_from_filename(filename):
    """
    Extract region from filename based on your naming convention.
    Handles: "S&P500", "Japan", "GLOBAL Ex US", "Europe", "APAC Ex JPY"
    """
    filename_lower = filename.lower()
    
    # Check for specific patterns first (more specific matches)
    if 'global ex us' in filename_lower or 'global ex-us' in filename_lower:
        return "Global Ex US"
    if 'apac ex jpy' in filename_lower or 'apac ex japan' in filename_lower:
        return "APAC Ex Japan"
    if 's&p500' in filename_lower or 's&p 500' in filename_lower or 'sp500' in filename_lower:
        return "US"
    
    # Check general region mappings
    for region, keywords in REGION_MAPPINGS.items():
        for keyword in keywords:
            # Use word boundary matching to avoid partial matches
            if re.search(r'\b' + re.escape(keyword) + r'\b', filename_lower):
                return region
    
    return "Unclassified"

def parse_file_metadata(filename):
    """Parse filename to extract date and region metadata."""
    return {
        'filename': filename,
        'date': extract_date_from_filename(filename),
        'region': extract_region_from_filename(filename)
    }

def list_drive_files(service, folder_id=None):
    """List files from Google Drive."""
    try:
        query = "(mimeType='text/csv' or mimeType='application/vnd.ms-excel' or mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')"
        
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="nextPageToken, files(id, name, modifiedTime, size, mimeType)"
        ).execute()
        
        files = results.get('files', [])
        return files
    except Exception as e:
        st.error(f"Error listing files: {str(e)}")
        return []

def download_file_content(service, file_id, mime_type):
    """Download file content from Google Drive."""
    try:
        if 'google-apps' in mime_type:
            # Export Google Sheets as CSV
            request = service.files().export_media(fileId=file_id, mimeType='text/csv')
        else:
            request = service.files().get_media(fileId=file_id)
        
        file_content = BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        file_content.seek(0)
        return file_content
    except Exception as e:
        st.error(f"Error downloading file: {str(e)}")
        return None

def read_excel_file(file_content, filename):
    """Read Excel or CSV file content into a DataFrame."""
    try:
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(file_content)
        else:
            df = pd.read_excel(file_content)
        return df
    except Exception as e:
        st.warning(f"Could not read file {filename}: {str(e)}")
        return None

def standardize_column_names(df):
    """Standardize column names to match expected format."""
    # Create a mapping of possible column names to standard names
    column_mappings = {
        # Ticker variations
        'ticker': 'Ticker',
        'symbol': 'Ticker',
        'stock': 'Ticker',
        'stock code': 'Ticker',
        'code': 'Ticker',
        
        # Company name variations
        'company': 'Company Name',
        'company name': 'Company Name',
        'name': 'Company Name',
        'company_name': 'Company Name',
        
        # Sector variations
        'sector': 'Sector',
        'industry': 'Sector',
        'gics sector': 'Sector',
        
        # Decile variations
        'current decile': 'Current Decile',
        'current_decile': 'Current Decile',
        'decile': 'Current Decile',
        'curr decile': 'Current Decile',
        
        'previous decile': 'Previous Decile',
        'previous_decile': 'Previous Decile',
        'prev decile': 'Previous Decile',
        'prior decile': 'Previous Decile',
        
        'decile change': 'Decile Change',
        'decile_change': 'Decile Change',
        'change': 'Decile Change',
        
        # Score variations
        'score': 'Score',
        'total score': 'Score',
        'composite score': 'Score',
        
        # Market cap variations
        'market cap': 'Market Cap (Bn)',
        'market_cap': 'Market Cap (Bn)',
        'marketcap': 'Market Cap (Bn)',
        'mkt cap': 'Market Cap (Bn)',
    }
    
    # Rename columns based on mapping
    new_columns = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in column_mappings:
            new_columns[col] = column_mappings[col_lower]
    
    if new_columns:
        df = df.rename(columns=new_columns)
    
    return df

def process_file_data(df, region, file_date):
    """Process a dataframe and add region/date metadata."""
    if df is None or df.empty:
        return None
    
    # Standardize column names
    df = standardize_column_names(df)
    
    # Add region and file date
    df['Region'] = region
    df['File Date'] = file_date if file_date else datetime.now()
    
    # Calculate decile change if not present
    if 'Decile Change' not in df.columns and 'Current Decile' in df.columns and 'Previous Decile' in df.columns:
        df['Decile Change'] = df['Current Decile'] - df['Previous Decile']
    
    return df

# =============================================================================
# FILTERING FUNCTIONS
# =============================================================================
def filter_by_decile_criteria(df, criteria):
    """Filter dataframe based on decile movement criteria."""
    if df.empty:
        return df
    if criteria == "All Decile Movements":
        return df
    elif criteria == "Entering Top 2 Deciles":
        return df[(df['Current Decile'] <= 2) & (df['Previous Decile'] > 2)]
    elif criteria == "Entering Bottom 2 Deciles":
        return df[(df['Current Decile'] >= 9) & (df['Previous Decile'] < 9)]
    elif criteria == "Moving +3 Deciles":
        return df[df['Decile Change'] >= 3]
    elif criteria == "Moving +5 Deciles":
        return df[df['Decile Change'] >= 5]
    return df

def filter_by_date_range(df, start_date, end_date):
    """Filter dataframe by date range."""
    if df.empty or 'File Date' not in df.columns:
        return df
    
    df_filtered = df.copy()
    df_filtered['File Date'] = pd.to_datetime(df_filtered['File Date'])
    
    mask = (df_filtered['File Date'] >= pd.to_datetime(start_date)) & \
           (df_filtered['File Date'] <= pd.to_datetime(end_date))
    
    return df_filtered[mask]

def filter_by_search(df, search_term):
    """Filter dataframe by ticker or company name search."""
    if df.empty or not search_term:
        return df
    
    search_lower = search_term.lower().strip()
    
    mask = pd.Series([False] * len(df))
    
    if 'Ticker' in df.columns:
        mask = mask | df['Ticker'].astype(str).str.lower().str.contains(search_lower, na=False)
    
    if 'Company Name' in df.columns:
        mask = mask | df['Company Name'].astype(str).str.lower().str.contains(search_lower, na=False)
    
    return df[mask]

def filter_by_sector(df, sector):
    """Filter dataframe by sector."""
    if df.empty or sector == "All Sectors" or 'Sector' not in df.columns:
        return df
    return df[df['Sector'] == sector]

def filter_by_region(df, region):
    """Filter dataframe by region."""
    if df.empty or region == "All Regions" or 'Region' not in df.columns:
        return df
    return df[df['Region'] == region]

def get_date_range_from_period(period):
    """Get start and end dates based on period selection."""
    end_date = datetime.now()
    
    if period == "3 Months":
        start_date = end_date - relativedelta(months=3)
    elif period == "6 Months":
        start_date = end_date - relativedelta(months=6)
    elif period == "9 Months":
        start_date = end_date - relativedelta(months=9)
    elif period == "12 Months":
        start_date = end_date - relativedelta(months=12)
    else:  # Custom
        start_date = end_date - relativedelta(months=12)
    
    return start_date, end_date

# =============================================================================
# MAIN APPLICATION
# =============================================================================
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔭 Galileo Decile Tracker</h1>
        <p>Quantitative Stock Analysis Dashboard • Google Drive Integrated</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check Google Drive connection
    service = get_google_drive_service()
    
    if service:
        st.session_state.drive_connected = True
    else:
        st.session_state.drive_connected = False
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Dashboard Controls")
        st.markdown("---")
        
        # Google Drive Connection Status
        st.markdown("#### 📁 Google Drive")
        
        if st.session_state.drive_connected:
            st.success("✅ Connected")
        else:
            st.error("❌ Not Connected")
            st.caption("Configure credentials in Streamlit secrets")
        
        # Folder ID input
        folder_id = st.text_input(
            "Drive Folder ID",
            help="Enter the Google Drive folder ID containing your decile files"
        )
        
        # Sync button
        sync_disabled = not st.session_state.drive_connected
        
        if st.button("🔄 Sync Files from Drive", use_container_width=True, disabled=sync_disabled):
            if service:
                with st.spinner("Syncing files from Google Drive..."):
                    files = list_drive_files(service, folder_id if folder_id else None)
                    
                    if not files:
                        st.warning("No Excel or CSV files found in the specified location")
                    else:
                        # Process files and download data
                        processed_files = []
                        all_stock_data = []
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, f in enumerate(files):
                            status_text.text(f"Processing: {f['name']}")
                            
                            metadata = parse_file_metadata(f['name'])
                            
                            # Download and read file content
                            file_content = download_file_content(service, f['id'], f.get('mimeType', ''))
                            
                            if file_content:
                                df = read_excel_file(file_content, f['name'])
                                
                                if df is not None and not df.empty:
                                    # Process the data
                                    processed_df = process_file_data(df, metadata['region'], metadata['date'])
                                    
                                    if processed_df is not None:
                                        all_stock_data.append(processed_df)
                            
                            processed_files.append({
                                'id': f['id'],
                                'filename': f['name'],
                                'date': metadata['date'],
                                'region': metadata['region'],
                                'modified': f.get('modifiedTime', ''),
                                'synced_at': datetime.now()
                            })
                            
                            progress_bar.progress((i + 1) / len(files))
                        
                        status_text.empty()
                        progress_bar.empty()
                        
                        st.session_state.synced_files = processed_files
                        st.session_state.last_sync = datetime.now()
                        
                        if all_stock_data:
                            st.session_state.stock_data = pd.concat(all_stock_data, ignore_index=True)
                            st.success(f"✅ Synced {len(processed_files)} files with {len(st.session_state.stock_data)} stock records")
                        else:
                            st.warning("Files synced but no stock data could be extracted. Check file format.")
        
        if not st.session_state.drive_connected:
            st.info("👆 Connect Google Drive to sync files")
        
        st.markdown("---")
        
        # Only show filters if data is loaded
        if not st.session_state.stock_data.empty:
            # =====================================================================
            # TIME PERIOD FILTER
            # =====================================================================
            st.markdown("#### 📅 Time Period")
            
            time_period = st.radio(
                "Select Period",
                ["3 Months", "6 Months", "9 Months", "12 Months", "Custom"],
                horizontal=False,
                key="time_period"
            )
            
            if time_period == "Custom":
                col1, col2 = st.columns(2)
                with col1:
                    custom_start = st.date_input(
                        "From",
                        datetime.now() - timedelta(days=365),
                        key="custom_start"
                    )
                with col2:
                    custom_end = st.date_input(
                        "To",
                        datetime.now(),
                        key="custom_end"
                    )
                start_date, end_date = custom_start, custom_end
            else:
                start_date, end_date = get_date_range_from_period(time_period)
                st.caption(f"📆 {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            st.markdown("---")
            
            # =====================================================================
            # REGION FILTER
            # =====================================================================
            st.markdown("#### 🌍 Region Filter")
            selected_region = st.selectbox(
                "Select Region",
                REGION_OPTIONS,
                help="Filter data by geographic region"
            )
            
            st.markdown("---")
            
            # =====================================================================
            # DECILE FILTER
            # =====================================================================
            st.markdown("#### 📊 Decile Movement Filter")
            selected_decile = st.selectbox(
                "Select Criteria",
                DECILE_OPTIONS,
                help="Filter stocks by decile movement patterns"
            )
            
            st.markdown("---")
            
            # Last sync info
            if st.session_state.last_sync:
                st.caption(f"Last sync: {st.session_state.last_sync.strftime('%Y-%m-%d %H:%M')}")
        else:
            # Default values when no data
            start_date = datetime.now() - relativedelta(months=12)
            end_date = datetime.now()
            selected_region = "All Regions"
            selected_decile = "All Decile Movements"
    
    # =========================================================================
    # MAIN CONTENT AREA
    # =========================================================================
    
    # Check if data is loaded
    if st.session_state.stock_data.empty:
        # Show setup instructions
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div class="setup-box">
                <h2>📁 Connect Your Google Drive</h2>
                <p>This dashboard requires a connection to your Google Drive to load your decile tracking data.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if not st.session_state.drive_connected:
                st.markdown("### ⚠️ Google Drive Not Connected")
                st.markdown("""
                To connect your Google Drive, you need to configure your credentials in Streamlit secrets.
                
                **For Streamlit Cloud deployment:**
                1. Go to your app settings
                2. Click on "Secrets"
                3. Add your Google Cloud service account credentials
                
                **For local development:**
                1. Create `.streamlit/secrets.toml`
                2. Add your credentials
                """)
                
                with st.expander("📋 Setup Instructions", expanded=True):
                    st.markdown("""
                    **Step 1: Create a Google Cloud Project**
                    1. Go to [Google Cloud Console](https://console.cloud.google.com/)
                    2. Create a new project
                    3. Enable the Google Drive API
                    
                    **Step 2: Create Service Account**
                    1. Go to IAM & Admin > Service Accounts
                    2. Create a new service account
                    3. Grant it "Viewer" role
                    4. Create and download JSON key
                    
                    **Step 3: Share Your Drive Folder**
                    Share your Google Drive folder containing the decile files with the service account email.
                    
                    **Step 4: Add Secrets**
                    Add this to your Streamlit secrets:
                    
                    ```toml
                    [gcp_service_account]
                    type = "service_account"
                    project_id = "your-project-id"
                    private_key_id = "your-key-id"
                    private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
                    client_email = "your-service@project.iam.gserviceaccount.com"
                    client_id = "your-client-id"
                    auth_uri = "https://accounts.google.com/o/oauth2/auth"
                    token_uri = "https://oauth2.googleapis.com/token"
                    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
                    client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
                    ```
                    """)
            else:
                st.markdown("### ✅ Google Drive Connected")
                st.markdown("""
                Your Google Drive is connected. Click **"🔄 Sync Files from Drive"** in the sidebar to load your data.
                
                **Supported file formats:**
                - Excel files (.xlsx, .xls)
                - CSV files (.csv)
                
                **Your file naming convention is supported:**
                - `S&P500 March 11 2025.xlsx` → US region
                - `Japan Jan 08 2026.xlsx` → Japan region
                - `GLOBAL Ex US Mar 11 2025.xlsx` → Global Ex US region
                - `Europe Jan 28 2025.xlsx` → Europe region
                - `APAC Ex JPY Dec 10 2025.xlsx` → APAC Ex Japan region
                """)
        
        return  # Exit early if no data
    
    # =========================================================================
    # DATA IS LOADED - SHOW DASHBOARD
    # =========================================================================
    
    stock_data = st.session_state.stock_data.copy()
    
    # Apply filters
    filtered_data = stock_data.copy()
    filtered_data = filter_by_region(filtered_data, selected_region)
    filtered_data = filter_by_decile_criteria(filtered_data, selected_decile)
    filtered_data = filter_by_date_range(filtered_data, start_date, end_date)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", 
        "🔍 Stock Search", 
        "🏭 Sector Analysis",
        "📁 Synced Files", 
        "⚙️ Settings"
    ])
    
    # =========================================================================
    # TAB 1: DASHBOARD
    # =========================================================================
    with tab1:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Stocks",
                value=len(filtered_data),
                delta=None
            )
        
        with col2:
            regions_count = filtered_data['Region'].nunique() if not filtered_data.empty else 0
            st.metric(
                label="Regions",
                value=regions_count,
                delta=None
            )
        
        with col3:
            st.metric(
                label="Selected Region",
                value=selected_region if selected_region != "All Regions" else "All",
                delta=None
            )
        
        with col4:
            sectors_count = filtered_data['Sector'].nunique() if not filtered_data.empty and 'Sector' in filtered_data.columns else 0
            st.metric(
                label="Sectors",
                value=sectors_count,
                delta=None
            )
        
        st.markdown("---")
        
        # Main data display
        st.markdown("### 📊 Stock Decile Data")
        
        # Display summary and export
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**Showing {len(filtered_data)} stocks** | Region: {selected_region} | Filter: {selected_decile}")
        
        with col2:
            if not filtered_data.empty:
                export_csv = filtered_data.to_csv(index=False)
                st.download_button(
                    label="📥 Export CSV",
                    data=export_csv,
                    file_name=f"galileo_decile_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        # Display data table
        if not filtered_data.empty:
            # Determine which columns to display based on what's available
            available_cols = filtered_data.columns.tolist()
            display_cols = [col for col in ['Ticker', 'Company Name', 'Region', 'Sector', 'Current Decile', 
                           'Previous Decile', 'Decile Change', 'Score', 'Market Cap (Bn)'] if col in available_cols]
            
            column_config = {}
            if 'Current Decile' in display_cols:
                column_config["Current Decile"] = st.column_config.ProgressColumn(
                    "Current Decile",
                    format="%d",
                    min_value=1,
                    max_value=10,
                )
            if 'Score' in display_cols:
                column_config["Score"] = st.column_config.NumberColumn(
                    "Score",
                    format="%.2f"
                )
            if 'Market Cap (Bn)' in display_cols:
                column_config["Market Cap (Bn)"] = st.column_config.NumberColumn(
                    "Market Cap (Bn)",
                    format="$%.2f"
                )
            if 'Decile Change' in display_cols:
                column_config["Decile Change"] = st.column_config.NumberColumn(
                    "Decile Δ",
                    format="%+d"
                )
            
            st.dataframe(
                filtered_data[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config=column_config
            )
        else:
            st.info("No data matches the current filters. Try adjusting your selection.")
        
        # Visualization
        st.markdown("---")
        st.markdown("### 📈 Visualizations")
        
        if not filtered_data.empty and 'Current Decile' in filtered_data.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # Decile distribution chart
                decile_counts = filtered_data['Current Decile'].value_counts().sort_index()
                fig_dist = px.bar(
                    x=decile_counts.index,
                    y=decile_counts.values,
                    labels={'x': 'Decile', 'y': 'Count'},
                    title='Distribution by Current Decile',
                    color=decile_counts.values,
                    color_continuous_scale='Blues'
                )
                fig_dist.update_layout(
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#e2e8f0'
                )
                st.plotly_chart(fig_dist, use_container_width=True)
            
            with col2:
                # Region breakdown
                if 'Region' in filtered_data.columns:
                    region_counts = filtered_data['Region'].value_counts()
                    fig_region = px.pie(
                        values=region_counts.values,
                        names=region_counts.index,
                        title='Distribution by Region',
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_region.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#e2e8f0'
                    )
                    st.plotly_chart(fig_region, use_container_width=True)
    
    # =========================================================================
    # TAB 2: STOCK SEARCH
    # =========================================================================
    with tab2:
        st.markdown("### 🔍 Search Stocks by Ticker or Company Name")
        st.markdown("Search for stocks using ticker symbols (e.g., 'F', 'AAPL') or company names (e.g., 'Ford', 'Apple')")
        
        # Search input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_term = st.text_input(
                "🔎 Enter Ticker or Company Name",
                placeholder="e.g., F, Ford, AAPL, Apple, Toyota...",
                key="stock_search"
            )
        
        with col2:
            search_region = st.selectbox(
                "Region",
                REGION_OPTIONS,
                key="search_region"
            )
        
        # Apply search
        search_results = stock_data.copy()
        
        if search_region != "All Regions":
            search_results = filter_by_region(search_results, search_region)
        
        if search_term:
            search_results = filter_by_search(search_results, search_term)
            
            st.markdown(f"---")
            st.markdown(f"### 📋 Search Results: **{len(search_results)}** stocks found")
            
            if not search_results.empty:
                # Display results grouped by region
                for region in search_results['Region'].unique():
                    region_results = search_results[search_results['Region'] == region]
                    
                    with st.expander(f"🌍 {region} ({len(region_results)} stocks)", expanded=True):
                        available_cols = region_results.columns.tolist()
                        display_cols = [col for col in ['Ticker', 'Company Name', 'Sector', 'Current Decile', 
                                       'Previous Decile', 'Decile Change', 'Score'] if col in available_cols]
                        
                        column_config = {}
                        if 'Current Decile' in display_cols:
                            column_config["Current Decile"] = st.column_config.ProgressColumn(
                                "Current Decile",
                                format="%d",
                                min_value=1,
                                max_value=10,
                            )
                        if 'Decile Change' in display_cols:
                            column_config["Decile Change"] = st.column_config.NumberColumn(
                                "Decile Δ",
                                format="%+d"
                            )
                        
                        st.dataframe(
                            region_results[display_cols],
                            use_container_width=True,
                            hide_index=True,
                            column_config=column_config
                        )
            else:
                st.warning(f"No stocks found matching '{search_term}' in {search_region}")
        else:
            st.info("👆 Enter a ticker symbol or company name to search")
            
            # Show available tickers
            if 'Ticker' in stock_data.columns:
                st.markdown("#### 📋 Available Tickers in Your Data")
                
                for region in stock_data['Region'].unique():
                    region_data = stock_data[stock_data['Region'] == region]
                    tickers = region_data['Ticker'].unique()[:20]  # Show first 20
                    
                    with st.expander(f"🌍 {region} ({len(region_data['Ticker'].unique())} tickers)"):
                        st.write(", ".join([str(t) for t in tickers]))
                        if len(region_data['Ticker'].unique()) > 20:
                            st.caption(f"...and {len(region_data['Ticker'].unique()) - 20} more")
    
    # =========================================================================
    # TAB 3: SECTOR ANALYSIS
    # =========================================================================
    with tab3:
        st.markdown("### 🏭 Sector Analysis")
        st.markdown("Analyze stocks by sector within each region. Sectors are kept separate by region.")
        
        if 'Sector' not in stock_data.columns:
            st.warning("Sector data not available in your files. Please ensure your data includes a 'Sector' column.")
        else:
            # Sector and region selection
            col1, col2, col3 = st.columns(3)
            
            with col1:
                sector_region = st.selectbox(
                    "🌍 Select Region",
                    REGION_OPTIONS,
                    key="sector_region"
                )
            
            with col2:
                # Get available sectors from the data
                available_sectors = ["All Sectors"] + sorted(stock_data['Sector'].dropna().unique().tolist())
                selected_sector = st.selectbox(
                    "🏭 Select Sector",
                    available_sectors,
                    key="sector_select"
                )
            
            with col3:
                sector_search = st.text_input(
                    "🔎 Search within Sector",
                    placeholder="Search ticker or name...",
                    key="sector_search"
                )
            
            st.markdown("---")
            
            # Filter data by region first
            sector_data = stock_data.copy()
            
            if sector_region != "All Regions":
                sector_data = filter_by_region(sector_data, sector_region)
            
            # Then filter by sector
            sector_filtered = filter_by_sector(sector_data, selected_sector)
            
            # Then apply search within sector
            if sector_search:
                sector_filtered = filter_by_search(sector_filtered, sector_search)
            
            # Display sector summary
            if sector_region == "All Regions":
                st.markdown("### 📊 Sector Distribution by Region")
                
                # Create a pivot table showing sectors by region
                if not sector_data.empty:
                    pivot = sector_data.groupby(['Region', 'Sector']).size().unstack(fill_value=0)
                    
                    fig_heatmap = px.imshow(
                        pivot,
                        labels=dict(x="Sector", y="Region", color="Count"),
                        title="Stock Count by Sector and Region",
                        color_continuous_scale="Blues",
                        aspect="auto"
                    )
                    fig_heatmap.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#e2e8f0'
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                    
                    st.markdown("---")
            
            # Display stocks by sector with region separation
            st.markdown(f"### 📋 {selected_sector} Stocks")
            
            if not sector_filtered.empty:
                # Group by region to keep them separate
                for region in sector_filtered['Region'].unique():
                    region_sector_data = sector_filtered[sector_filtered['Region'] == region]
                    
                    with st.expander(f"🌍 **{region}** - {selected_sector} ({len(region_sector_data)} stocks)", expanded=True):
                        # Summary metrics for this region-sector combination
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            if 'Current Decile' in region_sector_data.columns:
                                avg_decile = region_sector_data['Current Decile'].mean()
                                st.metric("Avg Decile", f"{avg_decile:.1f}")
                        
                        with col2:
                            if 'Current Decile' in region_sector_data.columns:
                                top_2 = len(region_sector_data[region_sector_data['Current Decile'] <= 2])
                                st.metric("Top 2 Deciles", top_2)
                        
                        with col3:
                            if 'Decile Change' in region_sector_data.columns:
                                improving = len(region_sector_data[region_sector_data['Decile Change'] > 0])
                                st.metric("Improving", improving)
                        
                        with col4:
                            if 'Score' in region_sector_data.columns:
                                avg_score = region_sector_data['Score'].mean()
                                st.metric("Avg Score", f"{avg_score:.1f}")
                        
                        # Display the data
                        available_cols = region_sector_data.columns.tolist()
                        display_cols = [col for col in ['Ticker', 'Company Name', 'Current Decile', 
                                       'Previous Decile', 'Decile Change', 'Score', 'Market Cap (Bn)'] if col in available_cols]
                        
                        column_config = {}
                        if 'Current Decile' in display_cols:
                            column_config["Current Decile"] = st.column_config.ProgressColumn(
                                "Current Decile",
                                format="%d",
                                min_value=1,
                                max_value=10,
                            )
                        if 'Decile Change' in display_cols:
                            column_config["Decile Change"] = st.column_config.NumberColumn(
                                "Decile Δ",
                                format="%+d"
                            )
                        if 'Market Cap (Bn)' in display_cols:
                            column_config["Market Cap (Bn)"] = st.column_config.NumberColumn(
                                "Market Cap",
                                format="$%.1fB"
                            )
                        
                        sort_col = 'Current Decile' if 'Current Decile' in display_cols else display_cols[0]
                        
                        st.dataframe(
                            region_sector_data[display_cols].sort_values(sort_col),
                            use_container_width=True,
                            hide_index=True,
                            column_config=column_config
                        )
            else:
                st.info(f"No stocks found in {selected_sector} for {sector_region}")
            
            # Sector comparison chart
            if not sector_data.empty and 'Current Decile' in sector_data.columns:
                st.markdown("---")
                st.markdown("### 📈 Sector Performance Comparison")
                
                # Calculate average decile by sector for each region
                sector_avg = sector_data.groupby(['Region', 'Sector'])['Current Decile'].mean().reset_index()
                
                fig_sector = px.bar(
                    sector_avg,
                    x='Sector',
                    y='Current Decile',
                    color='Region',
                    barmode='group',
                    title='Average Current Decile by Sector and Region',
                    labels={'Current Decile': 'Avg Decile'}
                )
                fig_sector.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#e2e8f0',
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_sector, use_container_width=True)
    
    # =========================================================================
    # TAB 4: SYNCED FILES
    # =========================================================================
    with tab4:
        st.markdown("### 📁 Synced Files Database")
        
        if st.session_state.synced_files:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Files", len(st.session_state.synced_files))
            with col2:
                classified = len([f for f in st.session_state.synced_files if f['region'] != 'Unclassified'])
                st.metric("Classified", classified)
            with col3:
                unclassified = len([f for f in st.session_state.synced_files if f['region'] == 'Unclassified'])
                st.metric("Unclassified", unclassified)
            
            st.markdown("---")
            
            # File list with filters
            file_region_filter = st.selectbox(
                "Filter by Region",
                ["All"] + REGION_OPTIONS[1:] + ["Unclassified"],
                key="file_region_filter"
            )
            
            # Display files
            files_df = pd.DataFrame(st.session_state.synced_files)
            
            if file_region_filter != "All":
                files_df = files_df[files_df['region'] == file_region_filter]
            
            # Format dates for display
            files_df['date_str'] = files_df['date'].apply(
                lambda x: x.strftime('%Y-%m-%d') if x else 'No date detected'
            )
            files_df['synced_at_str'] = files_df['synced_at'].apply(
                lambda x: x.strftime('%Y-%m-%d %H:%M') if x else ''
            )
            
            # Display as styled table
            display_df = files_df[['filename', 'region', 'date_str', 'synced_at_str']].copy()
            display_df.columns = ['Filename', 'Region', 'File Date', 'Synced At']
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Filename": st.column_config.TextColumn("📄 Filename", width="large"),
                    "Region": st.column_config.TextColumn("🌍 Region", width="medium"),
                    "File Date": st.column_config.TextColumn("📅 File Date", width="medium"),
                    "Synced At": st.column_config.TextColumn("⏰ Synced", width="medium")
                }
            )
            
            # Region breakdown chart
            st.markdown("---")
            st.markdown("#### 📊 Files by Region")
            region_file_counts = files_df['region'].value_counts()
            fig_files = px.bar(
                x=region_file_counts.index,
                y=region_file_counts.values,
                labels={'x': 'Region', 'y': 'Number of Files'},
                color=region_file_counts.values,
                color_continuous_scale='Viridis'
            )
            fig_files.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#e2e8f0'
            )
            st.plotly_chart(fig_files, use_container_width=True)
            
        else:
            st.info("No files synced yet. Click 'Sync Files from Drive' in the sidebar to load your data.")
    
    # =========================================================================
    # TAB 5: SETTINGS
    # =========================================================================
    with tab5:
        st.markdown("### ⚙️ Configuration")
        
        st.markdown("#### 🔑 Google Drive Connection")
        
        if st.session_state.drive_connected:
            st.success("✅ Google Drive is connected")
        else:
            st.error("❌ Google Drive is not connected")
        
        with st.expander("📋 Setup Instructions", expanded=not st.session_state.drive_connected):
            st.markdown("""
            **Step 1: Create a Google Cloud Project**
            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. Create a new project
            3. Enable the Google Drive API
            
            **Step 2: Create Service Account**
            1. Go to IAM & Admin > Service Accounts
            2. Create a new service account
            3. Grant it "Viewer" role
            4. Create and download JSON key
            
            **Step 3: Share Your Drive Folder**
            Share your Google Drive folder with the service account email address.
            
            **Step 4: Add Secrets to Streamlit**
            Add the service account JSON to your Streamlit secrets.
            """)
        
        st.markdown("---")
        
        st.markdown("#### 📁 Supported File Patterns")
        
        st.markdown("""
        **Your file naming convention:**
        | Example Filename | Detected Region | Detected Date |
        |-----------------|-----------------|---------------|
        | `S&P500 March 11 2025.xlsx` | US | March 11, 2025 |
        | `Japan Jan 08 2026.xlsx` | Japan | January 8, 2026 |
        | `GLOBAL Ex US Mar 11 2025.xlsx` | Global Ex US | March 11, 2025 |
        | `Europe Jan 28 2025.xlsx` | Europe | January 28, 2025 |
        | `APAC Ex JPY Dec 10 2025.xlsx` | APAC Ex Japan | December 10, 2025 |
        """)
        
        st.markdown("---")
        
        st.markdown("#### 📊 Expected Data Columns")
        
        st.markdown("""
        Your Excel/CSV files should contain these columns (column names are flexible):
        
        | Required | Column | Alternatives |
        |----------|--------|--------------|
        | ✅ | Ticker | Symbol, Stock, Code |
        | ✅ | Company Name | Company, Name |
        | ✅ | Current Decile | Decile |
        | ✅ | Previous Decile | Prior Decile |
        | ⬜ | Sector | Industry |
        | ⬜ | Score | Total Score |
        | ⬜ | Market Cap | Mkt Cap |
        """)
        
        st.markdown("---")
        
        st.markdown("#### 📊 Decile Criteria Definitions")
        
        criteria_df = pd.DataFrame([
            {"Criteria": "Entering Top 2 Deciles", "Definition": "Stocks moving into decile 1 or 2 from decile 3+"},
            {"Criteria": "Entering Bottom 2 Deciles", "Definition": "Stocks moving into decile 9 or 10 from decile 8-"},
            {"Criteria": "Moving +3 Deciles", "Definition": "Stocks improving by 3 or more decile positions"},
            {"Criteria": "Moving +5 Deciles", "Definition": "Stocks improving by 5 or more decile positions"}
        ])
        
        st.dataframe(criteria_df, hide_index=True, use_container_width=True)
        
        st.markdown("---")
        
        # Clear data button
        st.markdown("#### 🗑️ Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear All Synced Data", type="secondary"):
                st.session_state.synced_files = []
                st.session_state.stock_data = pd.DataFrame()
                st.session_state.last_sync = None
                st.success("All synced data cleared")
                st.rerun()
        
        with col2:
            if st.session_state.last_sync:
                st.info(f"Last sync: {st.session_state.last_sync.strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()
