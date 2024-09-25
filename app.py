import streamlit as st
from pdf_loader import load_btyes_io
import json
from core import pipeline
import os

# Path to save job descriptions
JOB_DESC_FILE = "job_descriptions.json"

def inference(query, files, embedding_type):
    # pdfReader = PyPDF2.PdfReader(files[0])
    # text = ''
    # for page in pdfReader.pages:
    #     text += page.extract_text()
    # st.write(text)
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

# Load job descriptions from the file or fallback to an empty dictionary
job_descriptions = load_job_descriptions()

# Sidebar for Job Descriptions
st.sidebar.header("Job Descriptions")
selected_job = st.sidebar.selectbox("Select a job description", list(job_descriptions.keys()), key="selected_job")
if selected_job:
    st.sidebar.code(job_descriptions[selected_job])

# Main Page
st.title("👨🏼‍🎓 Resume Ranker")

col1, col2,  = st.columns(2)

with col1:
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
            with col2:
                with st.spinner("Processing..."):
                    # Assuming 'inference' function does the processing of resumes
                    results = inference(query, uploaded_files, embedding_type)
                st.subheader("Results")
                for document, similarity in results.items():
                    similarity = round(similarity, 2) if similarity >= 1 else similarity
                    st.write(f"- {document}:")
                    st.progress(similarity, text=f"{similarity:.2%}")

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
        st.rerun()  
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

