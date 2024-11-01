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
    <script type="text/javascript" async
        src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
    </script>
""", unsafe_allow_html=True)

# Function to detect subject area from text
def detect_subject_area(text):
    # Create message structure for OpenAI API
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
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error detecting subject: {str(e)}"

# Function to suggest quiz format based on content
def suggest_quiz_format(text):
    # Create message structure for OpenAI API
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
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error suggesting quiz format: {str(e)}"

# Add session state initialization
if 'accepted_terms' not in st.session_state:
    st.session_state.accepted_terms = False
if 'website_content' not in st.session_state:
    st.session_state.website_content = None
if 'show_config' not in st.session_state:
    st.session_state.show_config = False
if 'quiz_generated' not in st.session_state:
    st.session_state.quiz_generated = False
if 'quiz_text' not in st.session_state:
    st.session_state.quiz_text = None
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

# Warning page
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
    
    st.markdown("<div class='warning-section'>", unsafe_allow_html=True)
    st.markdown("### 1. Quiz Generation Disclaimer")
    st.markdown("""
    - Always review generated quiz content before use
    - AI may occasionally produce inaccurate or hallucinated content
    - Verify questions and answers against trusted sources
    - Generated content should be used for practice purposes only
    - Not recommended for official testing/assessment
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='warning-section'>", unsafe_allow_html=True)
    st.markdown("### 2. File Upload Guidelines")
    st.markdown("""
    - Maximum file size: 10MB per file
    - Supported formats: PDF, DOCX, XLSX, CSV, PNG, JPG, JPEG
    - Do not upload sensitive or confidential materials
    - Ensure you have rights to use uploaded content
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='warning-section'>", unsafe_allow_html=True)
    st.markdown("### 3. Security Warnings")
    st.markdown("""
    - Do not upload materials containing personal/sensitive information
    - Avoid uploading proprietary or classified documents
    - Be cautious with academic materials to prevent data leakage
    - Website URLs should be from trusted sources only
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='warning-section'>", unsafe_allow_html=True)
    st.markdown("### 4. Usage Guidelines")
    st.markdown("""
    - Keep API keys secure and do not share them
    - Use the tool responsibly and ethically
    - Respect intellectual property rights
    - Report any issues or concerns to support
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    agree = st.checkbox("I have read and agree to the above warnings and guidelines")
    if st.button("Continue to QuizGenius", disabled=not agree):
        st.session_state.accepted_terms = True
        st.rerun()
    
    st.stop()

# Set up sidebar with API key input and navigation
with st.sidebar:
    st.image('images/QuizGenius.png')
    
    # Row 1: Label
    st.write('Enter OpenAI API token:')
    
    # Row 2: Input box and button in columns
    col1, col2 = st.columns([5,1], gap="small")
    with col1:
        openai.api_key = st.text_input('', type='password', label_visibility="collapsed")
    with col2:
        check_api = st.button('▶', key='api_button')
        
        # Updated CSS for button styling to match logo color
        st.markdown("""
            <style>
            [data-testid="stButton"][aria-label="api_button"] {
                font-size: 12px;
                background-color: #dec960;  /* Changed to match logo color */
                border: none;
                border-radius: 4px;
                color: white;  /* Changed to white for better contrast */
            }
            </style>
            """, unsafe_allow_html=True)
    
    if check_api:
        if not openai.api_key:
            st.warning('Please enter your OpenAI API token!', icon='⚠️')
        elif not (openai.api_key.startswith('sk-') and len(openai.api_key)==51):
            st.warning('Please enter a valid OpenAI API token!', icon='⚠️')
        else:
            st.success('Proceed to generating your quiz!', icon='👉')
    
    # Navigation menu
    options = option_menu(
        "Dashboard", 
        ["Home", "About Us", "Quiz Generator"],
        icons = ['house', 'info-circle', 'book'],
        menu_icon = "list", 
        default_index = 0,
        styles = {
            "icon": {"color": "#dec960", "font-size": "20px"},
            "nav-link": {"font-size": "17px", "text-align": "left", "margin": "5px", "--hover-color": "#262730"},
            "nav-link-selected": {"background-color": "#262730"}          
        })

# Define system prompt for OpenAI
System_Prompt = """
Role:
You are QuizGenius, an advanced educational assistant specializing in creating customized practice quizzes and mock exams. Your expertise lies in generating high-quality questions across various subjects while adapting to different difficulty levels and learning objectives.

Instructions:
1. Generate questions that are clear, relevant, and aligned with the specified subject matter
2. Provide detailed explanations for each answer to facilitate learning
3. Adjust difficulty levels based on user requirements (beginner, intermediate, advanced)
4. Create questions according to specified format (multiple choice, essay, problem sets, problem solving)
5. Ensure questions test different cognitive levels (recall, application, analysis)

Output Format Requirements:
1. Start with a clear quiz title and subject area
2. Number all questions sequentially
3. Separate sections with clear headers
4. Use consistent formatting for all similar elements
5. Include a student information section at the top

Mathematical Notation:
- Use LaTeX notation for all mathematical expressions
- Format: $equation$ for inline math
- Format: $$equation$$ for display math
- Example: $x^2 + 4x + 4 = 0$ or $$\int_0^1 x^2 dx$$

Question Format Templates:

[MULTIPLE CHOICE]
Question {n}: {clear question text}
A) {option}
B) {option}
C) {option}
D) {option}

[PROBLEM SOLVING]
Question {n}: {problem statement}
Given:
- {relevant information}
- {relevant information}
Required:
- {what needs to be solved}
Solution Space:
[Leave appropriate space for working]
Answer: _________________

[ESSAY]
Question {n}: {essay prompt}
Word Limit: {specify limit}
Evaluation Criteria:
- Content & Understanding (30%): {specific requirements}
- Organization & Structure (25%): {specific requirements}
- Evidence & Support (25%): {specific requirements}
- Language & Style (20%): {specific requirements}
Response Space:
_____________________
_____________________

[SHORT ANSWER]
Question {n}: {question text}
Answer Space: _________________
Scoring Guide: {specific requirements}

Answer Key Format:
[SEPARATE PAGE]
Question {n}:
Correct Answer: {detailed answer}
Explanation: {thorough explanation}
Common Mistakes: {list typical errors}
Grading Notes: {scoring guidance}

Constraints:
1. Maintain consistent difficulty throughout
2. Use clear, unambiguous language
3. Provide adequate space for responses
4. Include page numbers for multi-page quizzes
5. Separate answer key clearly from main quiz

Example Quiz Header:
===============================
QUIZ TITLE: {Subject} Assessment
Level: {Beginner/Intermediate/Advanced}
Time Allowed: {XX} minutes
Total Points: {XX}
Student Name: _________________
Date: _________________
===============================

Remember:
- Generate questions that are print-ready
- Include clear spacing between sections
- Format mathematical notation consistently
- Provide clear instructions for each section
- Include total points for each question
"""

# Add this near the top, after st.set_page_config
st.markdown("""
    <style>
    /* Global text styles */
    .stMarkdown {
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Headers */
    h1 {
        color: #1f1f1f;
        font-weight: 600;
    }
    
    h2, h3 {
        color: #2c3e50;
        font-weight: 500;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #dec960;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    /* Sidebar */
    .css-1d391kg {
        padding: 2rem 1rem;
    }
    
    /* Cards/Boxes */
    .stExpander {
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #e9ecef;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px;
        color: #2c3e50;
        font-size: 16px;
    }
    
    /* Info boxes */
    .stAlert {
        padding: 1rem;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# Options : Home
if options == "Home":
    st.markdown("<h1 style='text-align: center; margin-bottom: 15px; color: white;'>Welcome to QuizGenius!</h1>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align: center; padding: 10px; margin-bottom: 20px; font-size: 18px; color: white;'>QuizGenius is your intelligent companion for creating customized practice quizzes. Our AI-powered system automatically detects subjects and generates tailored questions to enhance your learning experience and test preparation.</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 style='text-align: center; color: #dec960; margin-bottom: 10px;'>Key Features</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; font-size: 16px; color: #1f1f1f; min-height: 200px;'>
        <ul style='list-style-type: none; padding-left: 0; margin: 0;'>
        <li style='margin-bottom: 8px;'>• AI-powered subject detection and quiz generation</li>
        <li style='margin-bottom: 8px;'> Multiple question formats and difficulty levels</li>
        <li style='margin-bottom: 8px;'>• Comprehensive answer explanations</li>
        <li style='margin-bottom: 8px;'>• Math-friendly with LaTeX support</li>
        <li style='margin-bottom: 8px;'>• Head to Quiz Generator to start creating your quiz!</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h3 style='text-align: center; color: #dec960; margin-bottom: 10px;'>Key Benefits</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; font-size: 16px; color: #1f1f1f; min-height: 200px;'>
        <ul style='list-style-type: none; padding-left: 0; margin: 0;'>
        <li style='margin-bottom: 8px;'>• Streamlined quiz creation for educators</li>
        <li style='margin-bottom: 8px;'>• Personalized learning experience</li>
        <li style='margin-bottom: 8px;'>• Instant feedback and explanations</li>
        <li style='margin-bottom: 8px;'>• Time-efficient exam preparation</li>
        <li style='margin-bottom: 8px;'>• Enhanced conceptual understanding</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

# Options : About Us
elif options == "About Us":
    st.title("About Us")
    st.write("# QuizGenius by AI Republic")
    st.image('images/Pat.png')
    st.write("## Empowering students and educators with intelligent quiz generation")
    st.text("Connect with us via LinkedIn: https://www.linkedin.com/in/rpdpscl/")
    st.text("For more information, visit our website: www.airepublic.com")
    st.write("\n")

# Options : Quiz Generator
elif options == "Quiz Generator":
    st.title("Quiz Generator")
    
    if not st.session_state.show_config:
        # Website URL interface with button
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
            # Only show quiz results and related buttons
            st.subheader("Generated Quiz:")
            
            # Process mathematical notation in quiz text
            processed_text = st.session_state.quiz_text.replace('^', '**')  # Convert ^ to ** for exponents
            processed_text = processed_text.replace('**', '^')  # Convert back for display
            st.markdown(processed_text)
            
            # Place buttons side by side in a single row
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
                    st.session_state.show_config = False
                    st.session_state.quiz_generated = False
                    st.session_state.website_content = None
                    st.session_state.quiz_text = None
                    st.session_state.pdf_data = None
                    st.rerun()
        else:
            # Show configuration options only if quiz hasn't been generated
            # Detect subject and suggest format
            detected_subject = detect_subject_area(st.session_state.website_content)
            st.info(f"Detected subject area: {detected_subject}")
            suggestion = suggest_quiz_format(st.session_state.website_content)
            if suggestion:
                st.info(suggestion)

            # Quiz configuration
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
            
            # Generate Quiz button
            if st.button("Generate Quiz"):
                if not openai.api_key:
                    st.error("Please enter your OpenAI API key first!")
                    st.stop()

                with st.spinner('Generating your quiz...'):
                    # Generate quiz
                    user_message = f"""Based on the following content: {st.session_state.website_content[:4000]}... (truncated)
                    Please generate {num_questions} {', '.join(question_type)} questions at {difficulty} level.
                    {"Focus on these topics: " + specific_topics if specific_topics else ""}
                    Suggested time limit: {time_limit} minutes.
                    Please format each question with clear A, B, C, D options for multiple choice, or step-by-step solutions for problem solving."""

                    struct = [{"role": "system", "content": System_Prompt}]
                    struct.append({"role": "user", "content": user_message})
                    
                    try:
                        # Generate quiz using OpenAI
                        chat = openai.ChatCompletion.create(
                            model="gpt-4o-mini",
                            messages=struct
                        )
                        st.session_state.quiz_text = chat.choices[0].message.content
                        st.session_state.quiz_generated = True
                        
                        # Create PDF file for quiz with math support
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)  # Add Unicode font support
                        pdf.set_font("DejaVu", size=12)
                        pdf.cell(200, 10, txt="Practice Quiz", ln=1, align='C')
                        
                        # Split quiz text into lines and add to PDF
                        lines = st.session_state.quiz_text.split('\n')
                        for line in lines:
                            # Process mathematical notation
                            line = line.replace('^', '**')  # Convert ^ to ** for exponents
                            pdf.multi_cell(0, 10, txt=line)
                        
                        # Store PDF data in session state
                        st.session_state.pdf_data = pdf.output(dest='S').encode('latin-1')
                        
                        # Rerun to show the quiz and download button
                        st.rerun()

                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
