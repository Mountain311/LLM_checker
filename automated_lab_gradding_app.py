import streamlit as st
import nbformat
import openai
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import pandas as pd
import io

# Constants
APP_VERSION = "v2"

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


def create_pdf_report(feedback, student_name, student_roll):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Lab Submission Evaluation Report")

    c.setFont("Helvetica", 10)
    c.drawString(width - 150, height - 30, f"App Version: {APP_VERSION}")

    # Student Info
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Student Name: {student_name}")
    c.drawString(50, height - 100, f"Roll Number: {student_roll}")
    c.drawString(50, height - 120,
                 f"Date: {datetime.now().strftime('%Y-%m-%d')}")

    # Extract overall grade
    overall_grade = ""
    if "OVERALL_GRADE:" in feedback:
        overall_grade = feedback.split("OVERALL_GRADE:")[
            1].split("\n")[0].strip()
        c.drawString(50, height - 140, f"Overall Grade: {overall_grade}/10")

    # Detailed feedback
    y_position = height - 180
    c.setFont("Helvetica", 10)

    # Split feedback into lines and wrap text
    for line in feedback.split('\n'):
        if line.strip():
            wrapped_text = simpleSplit(line, 'Helvetica', 10, width - 100)
            for wrapped_line in wrapped_text:
                if y_position < 50:  # Start new page if near bottom
                    c.showPage()
                    y_position = height - 50
                    c.setFont("Helvetica", 10)
                c.drawString(50, y_position, wrapped_line)
                y_position -= 15

    c.save()
    buffer.seek(0)
    return buffer


def evaluate_submission(api_key, assignment_cells, student_cells):
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
    **Assignment Instructions (Unsolved Notebook):**
    {assignment_cells}

    **Student Submission (Solved Notebook):**
    {student_cells}

    Please evaluate the submission based on the following criteria and provide a structured response in this exact format:

    OVERALL_GRADE: [Grade out of 10]

    1. Correctness (0-5):
    Score: [number]
    Reasoning: [detailed explanation]
    Areas for Improvement: [specific points if any]
    Key Strengths: [list main strengths]

    2. Adherence to Instructions (0-5):
    Score: [number]
    Reasoning: [detailed explanation]
    Areas for Improvement: [specific points if any]
    Key Strengths: [list main strengths]

    3. Code Quality (0-5):
    Score: [number]
    Reasoning: [detailed explanation]
    Areas for Improvement: [specific points if any]
    Key Strengths: [list main strengths]

    4. Explanation Quality (0-5):
    Score: [number]
    Reasoning: [detailed explanation]
    Areas for Improvement: [specific points if any]
    Key Strengths: [list main strengths]

    Summary of Key Recommendations:
    [List top 3 most important improvements needed]

    Additional Comments: [any overall feedback or suggestions]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a programming instructor grading a student submission. Provide detailed, structured feedback following the exact format specified."},
                      {"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error with OpenAI API: {e}"


def format_feedback(feedback, student_name, student_roll):
    current_date = datetime.now().strftime("%Y-%m-%d")

    overall_grade = ""
    if "OVERALL_GRADE:" in feedback:
        overall_grade = feedback.split("OVERALL_GRADE:")[
            1].split("\n")[0].strip()

    formatted_feedback = f"""
    # Lab Submission Evaluation Report
    
    <div style='text-align: right; color: rgba(128, 128, 128, 0.7);'>App Version used to grade: {APP_VERSION}</div>
    
    **Date:** {current_date}  
    **Student Name:** {student_name}  
    **Roll Number:** {student_roll}  
    **Overall Grade:** {overall_grade}/10
    
    ---
    
    ## Detailed Evaluation
    
    {feedback.split("1. Correctness")[1]}
    """

    return formatted_feedback


def extract_scores(feedback):
    scores = {}
    categories = ['Correctness', 'Adherence to Instructions',
                  'Code Quality', 'Explanation Quality']

    for category in categories:
        try:
            section = feedback.split(f"{category} (0-5):")[1].split("\n")[1]
            score = float(section.split("Score:")[1].strip())
            scores[category] = score
        except:
            scores[category] = 0

    try:
        overall = float(feedback.split("OVERALL_GRADE:")
                        [1].split("\n")[0].strip())
        scores['Overall'] = overall
    except:
        scores['Overall'] = 0

    return scores


def create_excel_report(feedback, student_name, student_roll):
    scores = extract_scores(feedback)

    # Create DataFrame
    df = pd.DataFrame({
        'Category': list(scores.keys()),
        'Score': list(scores.values()),
        'Maximum Score': [5, 5, 5, 5, 10]  # Overall is out of 10
    })

    # Add student info
    info_df = pd.DataFrame({
        'Field': ['Student Name', 'Roll Number', 'Date'],
        'Value': [student_name, student_roll, datetime.now().strftime('%Y-%m-%d')]
    })

    # Create Excel writer object
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write student info
        info_df.to_excel(writer, sheet_name='Evaluation',
                         startrow=0, index=False)

        # Write scores
        df.to_excel(writer, sheet_name='Evaluation', startrow=5, index=False)

        # Write detailed feedback
        pd.DataFrame({'Detailed Feedback': [feedback]}).to_excel(
            writer, sheet_name='Detailed Feedback', index=False)

        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Evaluation']

        # Add some formatting
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })

        # Apply formatting
        worksheet.set_column('A:C', 20)
        worksheet.set_row(5, None, header_format)

    buffer.seek(0)
    return buffer


def main():
    st.title("Automated Notebook Grading App")

    # Display app version in top right
    st.markdown(
        f"<div style='position: absolute; top: 20px; right: 20px; color: rgba(128, 128, 128, 0.7);'>App Version: {APP_VERSION}</div>",
        unsafe_allow_html=True
    )

    if not api_key:
        st.error("API key not found. Please set OPENAI_API_KEY in secrets.toml.")
        return

    # Create two columns for student info
    col1, col2 = st.columns(2)
    with col1:
        student_name = st.text_input("Enter Student's Full Name")
    with col2:
        student_roll = st.text_input("Enter Student's Roll Number")

    assignment_notebook = st.file_uploader(
        "Upload Instructor's Notebook", type=["ipynb"])
    student_notebook = st.file_uploader(
        "Upload Student's Notebook", type=["ipynb"])

    if st.button("Grade Notebook") and student_name and student_roll and assignment_notebook and student_notebook:
        with st.spinner("Evaluating submission..."):
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
                formatted_feedback = format_feedback(
                    feedback, student_name, student_roll)
                st.markdown(formatted_feedback)

                # Create download buttons for reports
                col1, col2 = st.columns(2)

                # PDF Download
                pdf_buffer = create_pdf_report(
                    feedback, student_name, student_roll)
                with col1:
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_buffer,
                        file_name=f"grade_report_{student_roll}.pdf",
                        mime="application/pdf"
                    )

                # Excel Download
                excel_buffer = create_excel_report(
                    feedback, student_name, student_roll)
                with col2:
                    st.download_button(
                        label="Download Excel Report",
                        data=excel_buffer,
                        file_name=f"grade_report_{student_roll}.xlsx",
                        mime="application/vnd.ms-excel"
                    )


if __name__ == "__main__":
    main()
