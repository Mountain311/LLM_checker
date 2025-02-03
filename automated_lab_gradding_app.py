import streamlit as st
import nbformat
import openai
import os
from dotenv import load_dotenv  # Import dotenv to read .env file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from datetime import datetime

# Load environment variables from .env file
load_dotenv()


def read_notebook(notebook_file):
    try:
        notebook_content = notebook_file.read()  # Read the content of the file
        notebook = nbformat.reads(notebook_content.decode(
            'utf-8'), as_version=4)  # Parse the content
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


def generate_pdf_report(student_name, assignment_name, feedback, output_file):
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter
    margin = 50
    y_position = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y_position, "Automated Grading Report")
    y_position -= 20

    c.setFont("Helvetica", 10)
    c.drawString(margin, y_position,
                 f"Submission Date: {datetime.today().strftime('%Y-%m-%d')}")
    y_position -= 30

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y_position, f"Student Name: {student_name}")
    y_position -= 20
    c.drawString(margin, y_position, f"Assignment: {assignment_name}")
    y_position -= 30

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y_position, "Evaluation Summary:")
    y_position -= 20

    def draw_wrapped_text(canvas_obj, text, x, y, max_width, bold=False, line_spacing=14):
        font = "Helvetica-Bold" if bold else "Helvetica"
        wrapped_lines = simpleSplit(text, font, 12, max_width)
        canvas_obj.setFont(font, 12)
        for line in wrapped_lines:
            if y < 50:
                canvas_obj.showPage()
                canvas_obj.setFont(font, 12)
                y = height - 50
            canvas_obj.drawString(x, y, line)
            y -= line_spacing
        return y

    sections = feedback.split("\n")
    for section in sections:
        section = section.strip()
        if section.startswith("**") and "**" in section[2:]:
            section_header, section_content = section.split("**", 2)[1:]
            y_position = draw_wrapped_text(c, section_header.strip(
            ) + ":", margin, y_position, width - 2 * margin, bold=True)
            y_position = draw_wrapped_text(c, section_content.strip(
            ), margin + 10, y_position, width - 2 * margin, bold=False)
        else:
            y_position = draw_wrapped_text(
                c, section, margin, y_position, width - 2 * margin, bold=False)

    c.save()
    return output_file


def main():
    st.title("Automated Notebook Grading App")

    api_key = os.getenv("OPENAI_API_KEY")  # Read from environment variable
    if not api_key:
        st.error(
            "API key not found. Please ensure the OPENAI_API_KEY is set in the .env file or system environment.")
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
            pdf_path = f"{student_name}_grading_report.pdf"
            pdf_path = generate_pdf_report(
                student_name, "Assignment", feedback, pdf_path)
            st.success("Grading completed!")
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    "Download Grading Report", pdf_file, file_name=pdf_path, mime="application/pdf")


if __name__ == "__main__":
    main()
