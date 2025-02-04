import streamlit as st
import nbformat
import openai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import io
import re
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from reportlab.platypus import Image

# Constants
APP_VERSION = "v2.4.2"
LOGO_PATH = "DQ_logo.jpg"

# Get API key from Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]


def analyze_code_patterns(code):
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
    Analyze the following code for patterns and practices (without grading it):

    {code}

    Please provide analysis in the following format:

    **Code Structure Analysis:**
    1. [Describe overall code organization]
    2. [Identify main components/functions]
    3. [Note any design patterns used]

    **Programming Practices:**
    1. [List good programming practices found]
    2. [Identify areas that could use improvement]
    3. [Note any interesting coding patterns]

    **Code Style:**
    1. [Comment on naming conventions]
    2. [Evaluate code formatting]
    3. [Assess documentation/comments]

    **Advanced Features Used:**
    1. [List any advanced language features]
    2. [Note any libraries/frameworks used effectively]
    3. [Identify any optimization techniques]

    **Potential Learning Opportunities:**
    1. [Suggest areas for learning/improvement]
    2. [Recommend additional techniques]
    3. [Propose alternative approaches]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a code analysis expert providing detailed, constructive feedback."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error analyzing code: {e}"


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


def format_code_for_display(code, language='python'):
    lexer = get_lexer_by_name(language)
    formatter = HtmlFormatter(style='monokai')
    result = highlight(code, lexer, formatter)
    css = formatter.get_style_defs('.highlight')
    return css, result


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


def format_feedback(feedback, student_name, student_roll, code_analysis=""):
    current_date = datetime.now().strftime("%Y-%m-%d")

    overall_grade = ""
    if "OVERALL_GRADE:" in feedback:
        overall_grade = feedback.split("OVERALL_GRADE:")[
            1].split("\n")[0].strip()

    formatted_feedback = f"""
    <div style="font-size: 24px; font-weight: bold; margin-bottom: 20px">Lab Submission Evaluation Report</div>
    
    <div style='text-align: right; color: rgba(128, 128, 128, 0.7); margin-top: -40px;'>App Version used to grade: {APP_VERSION}</div>
    
    <hr style="border-top: 2px solid #ccc; margin: 20px 0;">
    
    <div style="font-size: 14px;">
    <strong>Date:</strong> {current_date}<br>
    <strong>Student Name:</strong> {student_name}<br>
    <strong>Roll Number:</strong> {student_roll}
    </div>
    
    <div style="font-size: 18px; font-weight: bold; margin: 20px 0;">
    Overall Grade: {overall_grade}
    </div>
    
    <hr style="border-top: 1px solid #eee; margin: 20px 0;">
    
    <div style="font-size: 20px; font-weight: bold;">Detailed Evaluation</div>
    
    <div style="font-size: 13px;">
    """

    # Process the detailed feedback sections
    detailed_feedback = feedback.split("1. Correctness")[1]
    sections = detailed_feedback.split('\n')
    processed_sections = []

    for line in sections:
        line = line.strip()
        if not line:
            continue

        # Make section titles bold and larger
        if any(line.startswith(f"{i}.") for i in range(1, 5)) or "Summary of Key Recommendations:" in line:
            processed_sections.append(
                f'<div style="font-size: 16px; font-weight: bold; margin-top: 20px;">{line}</div>')
        # Make subsection headers bold
        elif any(header in line for header in ["Score:", "Reasoning:", "Areas for Improvement:", "Key Strengths:"]):
            processed_sections.append(f'<strong>{line}</strong>')
        else:
            processed_sections.append(line)

    formatted_feedback += '\n'.join(processed_sections)

    # Add code analysis section if available
    if code_analysis:
        formatted_feedback += f"""
        <hr style="border-top: 1px solid #eee; margin: 20px 0;">
        <div style="font-size: 20px; font-weight: bold;">Detailed Code Analysis (Ungraded)</div>
        <div style="font-size: 13px;">
        {code_analysis}
        </div>
        """

    # Add watermark to the app interface
    formatted_feedback += """
    <div style='position: fixed; bottom: 10px; right: 10px; opacity: 0.3;'>
        <img src='https://raw.githubusercontent.com/Mountain311/LLM_checker/main/DQ_logo.jpg' width='25'>
        <div style='color: #666; font-size: 12px; text-align: right;'>Powered by Dataquatz</div>
    </div>
    """

    formatted_feedback += "</div>"

    return formatted_feedback


def create_pdf_report(feedback, student_name, student_roll, code_analysis=""):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Add logo and footer to all pages
    def add_footer(canvas):
        canvas.saveState()
        # Add logo
        logo = Image(LOGO_PATH, width=20, height=20)
        logo.drawOn(canvas, width - 40, 40)
        # Add footer text
        canvas.setFillColorRGB(0.5, 0.5, 0.5, 0.4)
        canvas.setFont("Helvetica", 10)
        canvas.drawRightString(width - 40, 30, "Powered by Dataquatz")
        canvas.restoreState()

    # Header with larger, bold font
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "Lab Submission Evaluation Report")

    # App version in translucent gray
    c.setFillColorRGB(0.5, 0.5, 0.5, 0.6)
    c.setFont("Helvetica", 10)
    c.drawString(width - 150, height - 30, f"App Version: {APP_VERSION}")
    c.setFillColorRGB(0, 0, 0, 1)

    # Separator line
    c.setLineWidth(2)
    c.line(50, height - 70, width - 50, height - 70)

    # Student Info with medium font
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 90, f"Student Name: {student_name}")
    c.drawString(50, height - 110, f"Roll Number: {student_roll}")
    c.drawString(50, height - 130,
                 f"Date: {datetime.now().strftime('%Y-%m-%d')}")

    # Extract and display overall grade
    overall_grade = ""
    if "OVERALL_GRADE:" in feedback:
        overall_grade = feedback.split("OVERALL_GRADE:")[
            1].split("\n")[0].strip()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 160, f"Overall Grade: {overall_grade}/10")

    # Another separator line before detailed feedback
    c.setLineWidth(1)
    c.line(50, height - 180, width - 50, height - 180)

    # Detailed feedback
    y_position = height - 200
    text_width = width - 100

    # Process feedback sections
    all_content = feedback + "\n\n" + code_analysis if code_analysis else feedback
    sections = all_content.split('\n')

    # Add footer to first page
    add_footer(c)

    for line in sections:
        line = line.strip()
        if not line:
            continue

        # Handle section titles
        if any(line.startswith(f"{i}.") for i in range(1, 5)) or "Summary of Key Recommendations:" in line or "Code Analysis" in line:
            c.setFont("Helvetica-Bold", 12)
            if y_position < 100:
                c.showPage()
                add_footer(c)
                y_position = height - 50
            y_position -= 20
        else:
            c.setFont("Helvetica", 10)

        wrapped_text = simpleSplit(line, c._fontname, c._fontsize, text_width)

        for wrapped_line in wrapped_text:
            if y_position < 50:
                c.showPage()
                add_footer(c)
                y_position = height - 50
                c.setFont("Helvetica", 10)

            c.drawString(50, y_position, wrapped_line)
            y_position -= 15

    c.save()
    buffer.seek(0)
    return buffer


def main():
    st.markdown(
        f"""
        <div style='position: fixed; top: 20px; right: 20px; text-align: right; opacity: 0.75;'>
            <div style='color: #666; font-size: 14px; margin-bottom: 5px;'>App Version: {APP_VERSION}</div>
            <div style='color: #666; font-size: 14px;'>Powered by Dataquatz</div>
            <img src='https://raw.githubusercontent.com/Mountain311/LLM_checker/main/DQ_logo.jpg' width='50'>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.title("Automated Notebook Grading App")

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
            code_analysis = analyze_code_patterns("\n".join(student_code))

            formatted_feedback = format_feedback(
                feedback, student_name, student_roll, code_analysis)

            # PDF report generation
            pdf_report = create_pdf_report(
                feedback, student_name, student_roll, code_analysis)

            # Download button
            st.download_button(
                label="Download PDF Report",
                data=pdf_report,
                file_name=f"{student_roll}_report.pdf",
                mime="application/pdf"
            )

    # Add documentation section in sidebar
    st.sidebar.markdown(f"""
    ### Version: {APP_VERSION}
    
    ### How to Use This App
    1. Enter student name and roll number
    2. Upload the instructor's notebook (assignment template)
    3. Upload the student's completed notebook
    4. Click 'Grade Notebook' to generate evaluation
    5. View report and download PDF

    ### Evaluation Criteria
    - Correctness of solutions
    - Adherence to instructions
    - Code quality and best practices
    - Quality of explanations
    - Additional code pattern analysis

    ### Requirements
    - OpenAI API key (in secrets.toml)
    - Python 3.10
    - Required libraries: streamlit, openai, nbformat, reportlab, pygments
    - DQ_logo.jpg in working directory
    """)


if __name__ == "__main__":
    main()
