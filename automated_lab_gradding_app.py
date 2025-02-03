import streamlit as st
import nbformat
import openai
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from datetime import datetime

# Get API key from Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]


def read_notebook(notebook_file):
    try:
        notebook_content = notebook_file.read()
        notebook = nbformat.reads(
            notebook_content.decode('utf-8'), as_version=4)
        return notebook['cells'] if 'cells' in notebook else []
    except Exception as e:
        st.error(f"Error reading notebook: {e}")
        return []


def extract_code_cells(cells):
    return [cell['source'] for cell in cells if cell['cell_type'] == 'code']


def extract_markdown_cells(cells):
    return [cell['source'] for cell in cells if cell['cell_type'] == 'markdown']


def evaluate_submission(api_key, assignment_cells, student_cells):
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
    **Assignment Instructions (Unsolved Notebook):**
    {assignment_cells}

    **Student Submission (Solved Notebook):**
    {student_cells}

    **Evaluation Criteria:**
    **Correctness:** Does the student's code produce the expected output?
    **Adherence to Instructions:** Does the student follow the provided guidelines?
    **Code Quality:** Is the code well-structured, readable, and efficient?
    **Explanation Quality:** If required, is the markdown explanation clear and correct?

    **Task:**
    Provide a detailed assessment of the student's work. Highlight mistakes, suggest improvements, and assign an overall grade out of 10.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a programming instructor grading a student submission."},
                      {"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error with OpenAI API: {e}"


def main():
    st.title("Automated Notebook Grading App")

    if not api_key:
        st.error("API key not found. Please set OPENAI_API_KEY in secrets.toml.")
        return

    student_name = st.text_input("Enter Student's Full Name")
    assignment_notebook = st.file_uploader(
        "Upload Instructor's Notebook", type=["ipynb"])
    student_notebook = st.file_uploader(
        "Upload Student's Notebook", type=["ipynb"])

    if st.button("Grade Notebook") and student_name and assignment_notebook and student_notebook:
        assignment_cells = read_notebook(assignment_notebook)
        student_cells = read_notebook(student_notebook)

        assignment_code = extract_code_cells(assignment_cells)
        student_code = extract_code_cells(student_cells)
        assignment_text = extract_markdown_cells(assignment_cells)
        student_text = extract_markdown_cells(student_cells)

        assignment_content = "\n\n".join(assignment_code + assignment_text)
        student_content = "\n\n".join(student_code + student_text)

        feedback = evaluate_submission(
            api_key, assignment_content, student_content)

        if "Error" in feedback:
            st.error(feedback)
        else:
            st.success("Grading completed!")
            st.write(feedback)  # Display feedback in the app


if __name__ == "__main__":
    main()
