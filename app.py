import streamlit as st
from pdf_loader import load_btyes_io
import json
from core import pipeline
import os
import pandas as pd
import gspread
from google.oauth2 import service_account

# Path to save job descriptions
JOB_DESC_FILE = "job_descriptions.json"

def inference(query, files, embedding_type):
    results, _ = pipeline(query, load_btyes_io(files), embedding_type=embedding_type)
    prob_per_documents = {result['name']: result['similarity'] for result in results}
    return prob_per_documents

# Function to load existing job descriptions from the file
def load_job_descriptions():
    if os.path.exists(JOB_DESC_FILE):
        with open(JOB_DESC_FILE, "r") as f:
            return json.load(f)
    return {}

# Function to save job descriptions to the file
def save_job_descriptions(job_descriptions):
    with open(JOB_DESC_FILE, "w") as f:
        json.dump(job_descriptions, f, indent=4)

# Function to save feedback to Google Sheets
def save_to_google_sheets(df, job_description_name, job_description_content):
    # Set up the scope and credentials for Google Sheets
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    
    # Open the Google Sheet (replace 'Resume Feedback' with your sheet name)
    sheet = client.open("Resume Feedback").sheet1  # Adjust as needed
    
    # Prepare data to append
    for _, row in df.iterrows():
        data_to_append = [
            job_description_name,
            row['Resume'],
            int(row['Pass to Next Round'])
        ]
        try:
            sheet.append_row(data_to_append)
        except Exception as e:
            st.error(f"Error saving to Google Sheets: {e}")

# Load job descriptions from the file or fallback to an empty dictionary
job_descriptions = load_job_descriptions()

# Sidebar for Job Descriptions
st.sidebar.header("Job Descriptions")
selected_job = st.sidebar.selectbox("Select a job description", list(job_descriptions.keys()), key="selected_job")
if selected_job:
    st.sidebar.code(job_descriptions[selected_job])

# Main Page
st.title("👨🏼‍🎓 Resume Ranker")

    # Text area for Job Description
if selected_job:
        query = st.text_area("Job Description", height=200, value=job_descriptions[selected_job], key="query")
else:
        query = st.text_area("Job Description", height=200, key="query")

    # File uploader for resumes
uploaded_files = st.file_uploader("Upload Resume", accept_multiple_files=True, type=["txt", "pdf"])

    # Embedding type selection
embedding_type = st.selectbox("Embedding Type", ["bert", "minilm", "tfidf"])

    # Button to submit the query
if st.button("Submit"):
        if not query:
            st.warning("Please enter a job description.")
        elif not uploaded_files:
            st.warning("Please upload one or more resumes.")
        else:
                with st.spinner("Processing..."):
                    # Assuming 'inference' function does the processing of resumes
                    results = inference(query, uploaded_files, embedding_type)
                st.subheader("Results")
                # Create a DataFrame from results
                data = [{'Resume': doc, 'Similarity': sim} for doc, sim in results.items()]
                df_results = pd.DataFrame(data)
                df_results['Pass to Next Round'] = False
                edited_df = st.data_editor(df_results, use_container_width=True)
                if st.button('Save Feedback'):
                    if selected_job:
                        job_description_name = selected_job
                    else:
                        job_description_name = 'Custom Job Description'
                    save_to_google_sheets(edited_df, job_description_name, query)
                    st.success('Feedback saved to Google Sheets!')

# Sidebar - Add New Job Description
st.sidebar.subheader("Manage Job Descriptions")

# Add new job description input fields
new_job_name = st.sidebar.text_input("New Job Description Name", key="new_job_name")
new_job_description = st.sidebar.text_area("New Job Description Content", height=150, key="new_job_description")

if st.sidebar.button("Save New Job Description"):
    if new_job_name and new_job_description:
        job_descriptions[new_job_name] = new_job_description
        save_job_descriptions(job_descriptions)
        st.sidebar.success(f"New job description '{new_job_name}' saved successfully!")
        st.experimental_rerun()  
    else:
        st.sidebar.error("Please enter both a name and content for the new job description.")

# Update an existing job description
if selected_job and st.sidebar.button("Update Selected Job Description"):
    if query:
        job_descriptions[selected_job] = query
        save_job_descriptions(job_descriptions)
        st.sidebar.success(f"Job description '{selected_job}' updated successfully!")
    else:
        st.sidebar.error("Job description content cannot be empty.")
