import streamlit as st
from pdf_loader import load_btyes_io
import json
from core import pipeline
import os


def inference(query, files, embedding_type):

    # pdfReader = PyPDF2.PdfReader(files[0])
    # text = ''
    # for page in pdfReader.pages:
    #     text += page.extract_text()
    # st.write(text)

    results, _ = pipeline(query, load_btyes_io(files), embedding_type=embedding_type)
    prob_per_documents = {result['name']: result['similarity'] for result in results}
    return prob_per_documents


# Path to save job descriptions
JOB_DESC_FILE = "job_descriptions.json"

# Function to load existing job descriptions from the file
def load_job_descriptions():
    if os.path.exists(JOB_DESC_FILE):
        with open(JOB_DESC_FILE, "r") as f:
            return json.load(f)
    return {}

# Function to save job descriptions to the file
def save_job_descriptions(job_descriptions):
    with open(JOB_DESC_FILE, "w") as f:
        json.dump(job_descriptions, f)   

# Sample job descriptions that will be loaded if none are saved
sample_job_descriptions = {
    "Software Engineer": """We are looking for a software engineer with experience in Python and web development. The ideal candidate should have a strong background in building scalable and robust applications. Knowledge of frameworks such as Flask and Django is a plus. Experience with front-end technologies like HTML, CSS, and JavaScript is desirable. The candidate should also have a good understanding of databases and SQL. Strong problem-solving and communication skills are required for this role.
    """,
    "Data Scientist": """We are seeking a data scientist with expertise in machine learning and statistical analysis. The candidate should have a solid understanding of data manipulation, feature engineering, and model development. Proficiency in Python and popular data science libraries such as NumPy, Pandas, and Scikit-learn is required. Experience with deep learning frameworks like TensorFlow or PyTorch is a plus. Strong analytical and problem-solving skills are essential for this position.
    """
}

job_descriptions = load_job_descriptions() or sample_job_descriptions

# Sidebar for Job Descriptions
st.sidebar.header("Job Descriptions")
selected_job = st.sidebar.selectbox("Select a job description", list(job_descriptions.keys()))
st.sidebar.markdown("```")
st.sidebar.code(job_descriptions[selected_job])

query = st.text_area("Job Description", height=200, value=sample_job_descriptions[selected_job])
uploaded_files = st.file_uploader("Upload Resume", accept_multiple_files=True, type=["txt", "pdf"])
embedding_type = st.selectbox("Embedding Type", ["bert", "minilm", "tfidf"])

if st.button("Submit"):
    if not query:
        st.warning("Please enter a job description.")
    elif not uploaded_files:
        st.warning("Please upload one or more resumes.")
    else:
        with st.spinner("Processing..."):
            results = inference(query, uploaded_files,embedding_type)
        st.subheader("Results")
        for document, similarity in results.items():
            # make similiarty round to 2 decimal place
            if similarity >= 1:
                similarity = round(similarity, 2)
            st.write(f"- {document}:")
            st.progress(similarity, text=f"{similarity:.2%}")