# Required imports for application functionality
import os
import openai
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_extras.mention import mention
import PyPDF2
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import io
from fpdf import FPDF
import docx
import pandas as pd
import pytesseract
from PIL import Image
import sympy
from sympy import simplify, latex

# Configure Streamlit page settings - MUST BE FIRST!
st.set_page_config(page_title="QuizGenius", page_icon="🧠", layout="wide")

# Add MathJax support for mathematical notation
st.markdown("""
    <script type="text/javascript">
        window.MathJax = {
            tex: {
                inlineMath: [['$','$'], ['\\(','\\)']],
                displayMath: [['$$','$$'], ['\\[','\\]']],
                processEscapes: true
            },
            svg: {
                fontCache: 'global'
            }
        };
    </script>
    <script type="text/javascript" id="MathJax-script" async
        src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js">
    </script>
""", unsafe_allow_html=True)

# Helper functions
def detect_subject_area(text):
    messages = [
        {"role": "system", "content": """
Role:
You are a Subject Matter Expert specializing in academic content analysis. Your expertise lies in identifying the primary academic discipline of any given text.

Instructions:
1. Analyze the provided text content carefully
2. Identify key terminology and concepts
3. Determine the primary academic subject area
4. Consider interdisciplinary aspects if present

Context:
Users will provide text content from which you need to:
1. Identify subject-specific vocabulary
2. Recognize common themes and concepts
3. Match content to academic disciplines
4. Provide a clear, single subject classification

Constraints:
- Focus on mainstream academic subjects
- Provide specific rather than general classifications
- Consider the academic level of the content
- Maintain consistency in subject naming

Example Output Format:
Primary Subject: [Main Subject Area]
Sub-discipline: [Specific Branch] (if applicable)
Confidence Level: [High/Medium/Low]
Supporting Evidence:
- [Key term or concept 1]
- [Key term or concept 2]
- [Key term or concept 3]
Interdisciplinary Connections:
- [Related Subject 1]
- [Related Subject 2]
"""},
        {"role": "user", "content": f"Please identify the primary academic subject area for this text: {text[:1000]}... (truncated)"}
    ]
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error detecting subject: {str(e)}"

def suggest_quiz_format(text):
    messages = [
        {"role": "system", "content": """
Role:
You are an Educational Assessment Expert specializing in quiz design. Your expertise lies in determining the most effective assessment format for different types of academic content.

Instructions:
1. Analyze the content's complexity and scope
2. Consider the subject matter's nature
3. Evaluate the most effective testing methods
4. Match content type to quiz format

Context:
Users will provide content from which you need to:
1. Assess the content structure
2. Identify key testable elements
3. Determine optimal assessment approach
4. Recommend specific quiz formats

Constraints:
- Focus on established quiz formats
- Consider subject-specific requirements
- Ensure format supports learning objectives
- Maintain assessment validity

Example Output Format:
Subject Analysis:
[Subject]: [Brief description of content type]

Recommended Format:
Primary Format: [Quiz type]
Alternative Format: [Alternative quiz type]

Format Justification:
- [Reason 1 for format choice]
- [Reason 2 for format choice]
- [Reason 3 for format choice]

Assessment Structure:
- Question Distribution: [Breakdown of question types]
- Time Allocation: [Suggested time per section]
- Scoring Method: [Recommended scoring approach]

Special Considerations:
- [Any subject-specific requirements]
- [Technical requirements]
- [Assessment limitations]
"""},
        {"role": "user", "content": f"Based on this text content, suggest the most appropriate quiz format. Return the response in this exact format only: 'Since the subject matter is [subject], it is recommended to generate [quiz type] type of quiz'. Text: {text[:1000]}... (truncated)"}
    ]
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error suggesting quiz format: {str(e)}"

def convert_math_to_unicode(text):
    messages = [
        {"role": "system", "content": """
Role: You are LaTeXPDFGenius, an advanced mathematical notation converter specializing in transforming LaTeX expressions into publication-ready Unicode text for PDF documents.

Key Requirements:
1. Convert ALL mathematical expressions to their Unicode equivalents
2. Preserve equation structure and visual hierarchy
3. Maintain consistent spacing and formatting
4. Ensure readability in PDF output

Mathematical Conversion Guidelines:
1. Basic Operations:
   - Addition (+) → +
   - Subtraction (-) → −
   - Multiplication (\\times) → ×
   - Division (\\div) → ÷
   - Plus-minus (\\pm) → ±
   - Minus-plus (\\mp) → ∓

2. Numbers and Exponents:
   - Superscripts (x^n) → xⁿ (⁰¹²³⁴⁵⁶⁷⁸⁹)
   - Subscripts (x_n) → xₙ (₀₁₂₃₄₅₆₇₈₉)
   - Fractions (\\frac{a}{b}) → Unicode fractions where possible (½, ⅓, ¼, etc.)

3. Greek Letters:
   - \\alpha → α
   - \\beta → β
   - \\gamma → γ
   - \\theta → θ
   - \\pi → π
   [Continue for all Greek letters]

4. Calculus and Series:
   - Integral (\\int) → ∫
   - Double Integral (\\iint) → ∬
   - Triple Integral (\\iiint) → ∭
   - Contour Integral (\\oint) → ∮
   - Sum (\\sum) → ∑
   - Product (\\prod) → ∏
   - Partial (\\partial) → ∂

5. Relations and Logic:
   - Less than or equal (\\leq) → ≤
   - Greater than or equal (\\geq) → ≥
   - Not equal (\\neq) → ≠
   - Approximately (\\approx) → ≈
   - Proportional to (\\propto) → ∝
   - Similar to (\\sim) → ∼
   - Identical to (\\equiv) → ≡

6. Set Theory:
   - Element of (\\in) → ∈
   - Not element of (\\notin) → ∉
   - Subset (\\subset) → ⊂
   - Superset (\\supset) → ⊃
   - Union (\\cup) → ∪
   - Intersection (\\cap) → ∩

7. Arrows and Vectors:
   - Right arrow (\\rightarrow) → →
   - Left arrow (\\leftarrow) → ←
   - Double arrow (\\leftrightarrow) → ↔
   - Implies (\\Rightarrow) → ⇒
   - If and only if (\\Leftrightarrow) → ⇔
   - Vector notation (\\vec{v}) → v⃗

8. Special Symbols:
   - Infinity (\\infty) → ∞
   - Square root (\\sqrt{x}) → √x
   - Cube root (\\sqrt[3]{x}) → ∛x
   - Fourth root (\\sqrt[4]{x}) → ∜x
   - Degree (\\degree) → °
   - Prime (') → ′
   - Double prime ('') → ″

Format Requirements:
1. Text Structure:
   - Remove LaTeX delimiters ($, $$, \\[, \\])
   - Preserve line breaks and paragraph structure
   - Maintain question numbering and formatting
   - Keep option labels (A), B), C), D)) intact

2. Spacing Guidelines:
   - Add appropriate spacing around operators
   - Maintain alignment in equations
   - Preserve indentation in multi-line expressions
   - Keep consistent spacing between elements

3. Special Handling:
   - Complex fractions: Use horizontal division when Unicode fractions unavailable
   - Matrices: Convert to readable format with proper alignment
   - Multi-line equations: Preserve structure and alignment
   - Nested expressions: Maintain proper hierarchy

Example Conversions:
Input: $x^2 + \\frac{1}{2}\\alpha\\beta = \\sqrt{y}$
Output: x² + ½αβ = √y

Input: $$\\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$
Output: ∫₀^∞ e⁻ˣ² dx = √π/2

Remember:
- Convert ALL mathematical notation
- Maintain readability and clarity
- Preserve structural hierarchy
- Ensure consistent formatting
- Handle complex expressions appropriately

Output Format:
Return ONLY the converted text without explanations or comments.
Preserve all original line breaks and spacing.
Maintain the exact structure of the input text."""},
        {"role": "user", "content": f"Convert this LaTeX math to Unicode symbols: {text}"}
    ]
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return text

# Initialize session state
for key in ['accepted_terms', 'website_content', 'show_config', 'quiz_generated', 'quiz_text', 'pdf_data']:
    if key not in st.session_state:
        st.session_state[key] = False if key != 'pdf_data' else None

# Add CSS styling
st.markdown("""
    <style>
    .stMarkdown { font-family: 'Helvetica Neue', sans-serif; }
    h1 { color: #1f1f1f; font-weight: 600; }
    h2, h3 { color: #2c3e50; font-weight: 500; }
    .stButton>button {
        background-color: #dec960;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .css-1d391kg { padding: 2rem 1rem; }
    .stExpander {
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #e9ecef;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px;
        color: #2c3e50;
        font-size: 16px;
    }
    .stAlert {
        padding: 1rem;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# Set up sidebar
with st.sidebar:
    st.image('images/QuizGenius.png')
    
    col1, col2 = st.columns([5,1], gap="small")
    with col1:
        openai.api_key = st.text_input('Enter OpenAI API token:', type='password', label_visibility="collapsed")
    with col2:
        check_api = st.button('▶', key='api_button')
    
    if check_api:
        if not openai.api_key:
            st.warning('Please enter your OpenAI API token!', icon='⚠️')
        elif not (openai.api_key.startswith('sk-') and len(openai.api_key)==51):
            st.warning('Please enter a valid OpenAI API token!', icon='⚠️')
        else:
            st.success('Proceed to generating your quiz!', icon='👉')
    
    options = option_menu(
        "Dashboard",
        ["Home", "Quiz Generator"],
        icons=['house', 'book'],
        menu_icon="list",
        default_index=0,
        styles={
            "icon": {"color": "#dec960", "font-size": "20px"},
            "nav-link": {"font-size": "17px", "text-align": "left", "margin": "5px", "--hover-color": "#262730"},
            "nav-link-selected": {"background-color": "#262730"}
        }
    )

# Display warning page if terms not accepted
if not st.session_state.accepted_terms:
    st.markdown("""
        <style>
        .warning-header {
            color: #ff4b4b;
            text-align: center;
            padding: 20px;
            margin-bottom: 20px;
        }
        .warning-section {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 4px solid #ff4b4b;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='warning-header'>⚠️ Important Warnings and Guidelines</h1>", unsafe_allow_html=True)
    
    warnings = {
        "Quiz Generation Disclaimer": [
            "Always review generated quiz content before use",
            "AI may occasionally produce inaccurate or hallucinated content", 
            "Verify questions and answers against trusted sources",
            "Generated content should be used for practice purposes only",
            "Not recommended for official testing/assessment"
        ],
        "File Upload Guidelines": [
            "Maximum file size: 10MB per file",
            "Supported formats: PDF, DOCX, XLSX, CSV, PNG, JPG, JPEG",
            "Do not upload sensitive or confidential materials",
            "Ensure you have rights to use uploaded content"
        ],
        "Security Warnings": [
            "Do not upload materials containing personal/sensitive information",
            "Avoid uploading proprietary or classified documents", 
            "Be cautious with academic materials to prevent data leakage",
            "Website URLs should be from trusted sources only"
        ],
        "Usage Guidelines": [
            "Keep API keys secure and do not share them",
            "Use the tool responsibly and ethically",
            "Respect intellectual property rights", 
            "Report any issues or concerns to support"
        ]
    }
    
    for title, items in warnings.items():
        st.markdown(f"<div class='warning-section'>", unsafe_allow_html=True)
        st.markdown(f"### {title}")
        st.markdown("\n".join([f"- {item}" for item in items]))
        st.markdown("</div>", unsafe_allow_html=True)
    
    agree = st.checkbox("I have read and agree to the above warnings and guidelines")
    if st.button("Continue to QuizGenius", disabled=not agree):
        st.session_state.accepted_terms = True
        st.rerun()
    
    st.stop()

# Main content based on selected option
if options == "Home":
    st.markdown("<h1 style='text-align: center; margin-bottom: 15px; color: white;'>Welcome to QuizGenius!</h1>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; padding: 10px; margin-bottom: 20px; font-size: 18px; color: white;'>QuizGenius is your intelligent companion for creating customized practice quizzes. Our AI-powered system automatically detects subjects and generates tailored questions to enhance your learning experience and test preparation.</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    features = {
        "Key Features": [
            "AI-powered subject detection and quiz generation",
            "Multiple question formats and difficulty levels",
            "Comprehensive answer explanations",
            "Math-friendly with LaTeX support",
            "Head to Quiz Generator to start creating your quiz!"
        ],
        "Key Benefits": [
            "Streamlined quiz creation for educators",
            "Personalized learning experience",
            "Instant feedback and explanations",
            "Time-efficient exam preparation",
            "Enhanced conceptual understanding"
        ]
    }
    
    for col, (title, items) in zip([col1, col2], features.items()):
        with col:
            st.markdown(f"<h3 style='text-align: center; color: #dec960; margin-bottom: 10px;'>{title}</h3>", unsafe_allow_html=True)
            st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; font-size: 16px; color: #1f1f1f; min-height: 200px;'>
                <ul style='list-style-type: none; padding-left: 0; margin: 0;'>
                {"".join([f"<li style='margin-bottom: 8px;'>• {item}</li>" for item in items])}
                </ul>
                </div>
            """, unsafe_allow_html=True)

elif options == "Quiz Generator":
    st.title("Quiz Generator")
    
    if not st.session_state.show_config:
        col1, col2 = st.columns([5,1], gap="small")
        with col1:
            website_url = st.text_input("Enter website URL:")
        with col2:
            check_url = st.button('▶', key='url_button')

        if check_url and website_url:
            try:
                response = requests.get(website_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                st.session_state.website_content = " ".join([p.get_text() for p in soup.find_all('p')])
                st.session_state.show_config = True
                st.rerun()
            except Exception as e:
                st.error(f"Error extracting website content: {str(e)}")
    
    if st.session_state.show_config:
        if st.session_state.quiz_text:
            st.subheader("Generated Quiz:")
            processed_text = st.session_state.quiz_text.replace('x^2', 'x²').replace('x^3', 'x³')
            st.markdown(processed_text)
            
            col1, col2, col3 = st.columns([1.5, 1.5, 3])
            with col1:
                if st.session_state.pdf_data is not None:
                    st.download_button(
                        label="Download Quiz (PDF)",
                        data=st.session_state.pdf_data,
                        file_name="quiz.pdf",
                        mime="application/pdf"
                    )
            with col2:
                if st.button("Generate New Quiz"):
                    for key in ['show_config', 'quiz_generated', 'website_content', 'quiz_text', 'pdf_data']:
                        st.session_state[key] = False if key != 'pdf_data' else None
                    st.rerun()
        else:
            detected_subject = detect_subject_area(st.session_state.website_content)
            st.info(f"Detected subject area: {detected_subject}")
            suggestion = suggest_quiz_format(st.session_state.website_content)
            if suggestion:
                st.info(suggestion)

            st.subheader("Quiz Configuration")
            col1, col2 = st.columns(2)
            
            with col1:
                difficulty = st.selectbox("Select difficulty level:", ["Beginner", "Intermediate", "Advanced"])
                num_questions = st.number_input("Number of questions:", min_value=1, max_value=20, value=5)
                specific_topics = st.text_area("Specific topics or concepts to focus on (optional):")
                time_limit = st.number_input("Suggested time limit (minutes):", min_value=5, max_value=180, value=30)
            
            with col2:
                question_type = st.multiselect("Select question types:", 
                                             ["Multiple Choice", "Essay", "Problem Sets", "Problem Solving", "Mixed"],
                                             default=["Multiple Choice"])
            
            if st.button("Generate Quiz"):
                if not openai.api_key:
                    st.error("Please enter your OpenAI API key first!")
                    st.stop()

                with st.spinner('Generating your quiz...'):
                    try:
                        chat = openai.ChatCompletion.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": System_Prompt},
                                {"role": "user", "content": f"""Based on the following content: {st.session_state.website_content[:4000]}... (truncated)
                                Please generate {num_questions} {', '.join(question_type)} questions at {difficulty} level.
                                {"Focus on these topics: " + specific_topics if specific_topics else ""}
                                Suggested time limit: {time_limit} minutes.
                                Please format each question with clear A, B, C, D options for multiple choice, or step-by-step solutions for problem solving."""}
                            ]
                        )
                        
                        st.session_state.quiz_text = chat.choices[0].message.content
                        st.session_state.quiz_generated = True
                        
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        pdf.cell(200, 10, txt="Practice Quiz", ln=1, align='C')
                        
                        for line in st.session_state.quiz_text.split('\n'):
                            line = line.replace('^', '**')
                            pdf.multi_cell(0, 10, txt=line)
                        
                        st.session_state.pdf_data = pdf.output(dest='S').encode('latin-1')
                        st.rerun()
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
