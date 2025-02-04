# Automated Lab Grading App

## Overview
The **Automated Lab Grading App** is a Streamlit-based application that evaluates student-submitted Jupyter Notebooks (.ipynb) against an instructor-provided assignment notebook. The app utilizes OpenAI's GPT-4 model to assess correctness, adherence to instructions, code quality, and explanation clarity, providing structured feedback and generating a PDF report.

## Features
- 📊 **Automated Grading:** Uses OpenAI GPT-4 to evaluate student submissions.
- 📝 **Code Structure Analysis:** Provides insights into code organization and best practices.
- 📄 **PDF Report Generation:** Creates a structured grading report for download.
- 🎨 **Syntax Highlighting:** Uses Pygments for enhanced code readability.
- 🎯 **Instructor and Student Support:** Upload both assignment and student notebooks for comparison.

## Installation
### Prerequisites
- Python 3.10 or later
- OpenAI API key stored in `.streamlit/secrets.toml`
- Required dependencies (listed in `requirements.txt`)

### Setup Instructions
1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd automated_lab_grading
   ```
2. Create and activate a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate  # On Windows
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Store your OpenAI API key in `.streamlit/secrets.toml`:
   ```toml
   [secrets]
   OPENAI_API_KEY = "your-api-key"
   ```
5. Run the Streamlit app:
   ```sh
   streamlit run automated_lab_gradding_app.py
   ```

## Usage
1. **Enter Student Information:** Input student name and roll number.
2. **Upload Files:** Upload the instructor's and student's Jupyter Notebooks.
3. **Evaluate:** Click the "Grade Notebook" button.
4. **Review Results:** View structured feedback and grading analysis.
5. **Download Report:** Save the grading report as a PDF.

## Evaluation Criteria
- ✅ **Correctness:** Accuracy of student solutions.
- 📜 **Adherence to Instructions:** Following assignment requirements.
- 💡 **Code Quality:** Efficiency, readability, and best practices.
- ✍️ **Explanation Quality:** Clarity and thoroughness of explanations.

## Dependencies
The following Python packages are required:
```txt
nbformat==5.7.3
streamlit==1.24.1
openai==1.61.0
reportlab==4.3.0
Pillow==9.4.0
Pygments==2.14.0
```
Install using:
```sh
pip install -r requirements.txt
```

## File Structure
```
📁 automated_lab_grading/
├── 📄 automated_lab_gradding_app.py  # Main application script
├── 📄 requirements.txt  # List of dependencies
├── 📄 README.md  # Project documentation (this file)
├── 🖼️ DQ_logo.jpg  # Application logo (required for PDF generation)
└── 📁 .streamlit/
    └── 📄 secrets.toml  # API key storage
```
