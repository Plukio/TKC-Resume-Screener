import streamlit as st
from pdf_loader import load_btyes_io
import json
from core import pipeline
import os
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import datetime

# Function to perform inference
def inference(query, files, embedding_type):
    results, _ = pipeline(query, load_btyes_io(files), embedding_type=embedding_type)
    prob_per_documents = {result['name']: result['similarity'] for result in results}
    return prob_per_documents

# Function to save feedback to Google Sheets, including the query and timestamp
def save_to_google_sheets(df, query_text):
    try:
        # Set up the scope and credentials for Google Sheets
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # Open the Google Sheet (replace with your own Google Sheet URL)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/11by73OTHm0PX2Ai8uO_cT87vHlWjKbbEjV7IupGehvg/edit?gid=0#gid=0").sheet1
        
        # Get the current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepare data to append: Resume, Rank, Query Text, Timestamp
        for _, row in df.iterrows():
            data_to_append = [
                row['Resume'],         # Resume Name
                row['Rank'],           # Rank
                query_text,            # Job Description (query text)
                timestamp              # Timestamp
            ]
            sheet.append_row(data_to_append)
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")

def fetch_column_c_from_sheet():
    try:
        # Set up the scope and credentials for Google Sheets
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        # Open the Google Sheet
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/11by73OTHm0PX2Ai8uO_cT87vHlWjKbbEjV7IupGehvg/edit?gid=0#gid=0").sheet1
        
        # Get all records from the sheet
        all_records = sheet.get_all_values()
        
        # Extract the "C" column (3rd column)
        column_c_data = [row[2] for row in all_records if len(row) > 2]  # Column C is index 2
        return column_c_data
    except Exception as e:
        st.error(f"Error fetching column C from Google Sheets: {e}")
        return []
        
    
st.title("👨🏼‍🎓 Resume Ranker")

# Fetch recent job descriptions
recent_job_descriptions = fetch_recent_job_descriptions()

# Option to select recent JD or add new one
jd_choice = st.radio("Would you like to use a recent Job Description or add a new one?", ("Use Recent JD", "Add New JD"))

if jd_choice == "Use Recent JD" and recent_job_descriptions:
    query = st.selectbox("Choose a recent Job Description", recent_job_descriptions)
elif jd_choice == "Add New JD":
    query = st.text_area("Enter the Job Description", height=200, key="query")
else:
    st.warning("No recent job descriptions available. Please enter a new one.")
    query = st.text_area("Enter the Job Description", height=200, key="query")

# File uploader for resumes
uploaded_files = st.file_uploader("Upload Resume", accept_multiple_files=True, type=["txt", "pdf"])

# Embedding type selection
embedding_type = st.selectbox("Embedding Type", ["bert", "minilm", "tfidf"])

# Button to submit the query
if st.button("Submit"):
    if not query:
        st.warning("Please enter or select a job description.")
    elif not uploaded_files:
        st.warning("Please upload one or more resumes.")
    else:
        with st.spinner("Processing..."):
            # Process resumes based on the job description
            results = inference(query, uploaded_files, embedding_type)
            st.subheader("Results")
            
            # Create a DataFrame from results
            data = [{'Resume': doc, 'Similarity': sim} for doc, sim in results.items()]
            df_results = pd.DataFrame(data)
            st.session_state["df_results"] = df_results

# Handle session state for results
if "df_results" not in st.session_state:
    st.warning('Please submit resumes to rank them', icon="⚠️")
else:
    df_results = st.session_state["df_results"]
    st.dataframe(df_results)
    
    # Allow user to rank resumes using multiselect
    resume_options = list(df_results['Resume'])
    st.write("Please rank the resumes by selecting them in order of priority:")

    ranked_resumes = st.multiselect(
        "Select resumes in order of preference",
        resume_options,
        default=resume_options
    )

    # Assign ranks based on user input
    for i, resume in enumerate(ranked_resumes):
        df_results.loc[df_results['Resume'] == resume, 'Rank'] = i + 1
    
    # Save rankings to CSV
    df_results.to_csv('results.csv', index=False)

# Load the CSV and allow saving feedback
if os.path.exists('results.csv'):
    df_results = pd.read_csv('results.csv')

    # Button to save feedback
    if st.button('Save Feedback'):
        save_to_google_sheets(df_results, query)
        st.success('Feedback saved to Google Sheets!')