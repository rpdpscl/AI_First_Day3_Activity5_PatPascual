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

# Function to detect subject area from text using OpenAI API
def detect_subject_area(text):
    # Create message structure for OpenAI API
    messages = [
        {"role": "system", "content": """
Role:
Subject Matter Expert specializing in academic content analysis.

Instructions:
1. Analyze provided text content carefully
2. Identify key terminology and concepts
3. Determine primary academic subject area
4. Consider interdisciplinary aspects

Context:
Analyzing user-provided text content for subject classification.

Content Requirements:
1. Identify subject-specific vocabulary
2. Recognize common themes and concepts
3. Match content to academic disciplines
4. Provide clear subject classification

Constraints:
1. Focus on mainstream academic subjects
2. Provide specific rather than general classifications
3. Consider academic level of content
4. Maintain consistent subject naming

Example Output:
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

# Function to suggest quiz format based on content using OpenAI API
def suggest_quiz_format(text):
    # First detect the subject area
    subject_area = detect_subject_area(text)
    
    # Create message structure for OpenAI API
    messages = [
        {"role": "system", "content": """
Role:
Educational Assessment Expert specializing in quiz design.

Instructions:
1. Analyze content complexity and scope
2. Consider subject matter nature
3. Evaluate effective testing methods
4. Match content type to quiz format

Context:
Determining optimal quiz formats for different academic content.

Content Requirements:
1. Assess content structure
2. Identify testable elements
3. Determine assessment approach
4. Recommend specific formats

Constraints:
1. Focus on established quiz formats
2. Consider subject-specific requirements
3. Ensure format supports learning objectives
4. Maintain assessment validity

Example Output:
Subject Analysis:
[Subject]: [Brief description]

Recommended Format:
Primary Format: [Quiz type]
Alternative Format: [Alternative type]

Format Justification:
- [Reason 1]
- [Reason 2]
- [Reason 3]

Assessment Structure:
- Question Distribution: [Breakdown]
- Time Allocation: [Time per section]
- Scoring Method: [Approach]

Special Considerations:
- [Subject requirements]
- [Technical requirements]
- [Limitations]
"""},
        {"role": "user", "content": f"""Based on the following analysis and content, suggest the most appropriate quiz format:

Subject Area Analysis:
{subject_area}

Content:
{text[:1000]}... (truncated)"""}
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

# Initialize session state variables for app functionality
if 'accepted_terms' not in st.session_state:
    st.session_state.accepted_terms = False
if 'website_contents' not in st.session_state:
    st.session_state.website_contents = []
if 'show_config' not in st.session_state:
    st.session_state.show_config = False
if 'quiz_generated' not in st.session_state:
    st.session_state.quiz_generated = False
if 'quiz_text' not in st.session_state:
    st.session_state.quiz_text = None
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

# Initialize additional session state variables
if 'detected_subject' not in st.session_state:
    st.session_state.detected_subject = None
if 'format_suggestion' not in st.session_state:
    st.session_state.format_suggestion = None
if 'url_processed' not in st.session_state:
    st.session_state.url_processed = False

# Display warning page for first-time users
if not st.session_state.accepted_terms:
    st.markdown("""
        <style>
        .warning-header {
            color: white;
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
            color: white;
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
    st.write('Enter OpenAI API token:', style={'color': 'white'})
    
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
                background-color: #FBCD5D;
                border: none;
                border-radius: 4px;
                color: white;
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
        ["Home", "Quiz Generator"],
        icons = ['house', 'book'],
        menu_icon = "list", 
        default_index = 0,
        styles = {
            "icon": {"color": "#FBCD5D", "font-size": "20px"},
            "nav-link": {"font-size": "17px", "text-align": "left", "margin": "5px", "--hover-color": "#262730", "color": "white"},
            "nav-link-selected": {"background-color": "#262730"}          
        })

# System prompt for quiz generation with OpenAI API
System_Prompt = """
Role:
QuizGenius - Advanced educational assessment specialist with expertise in technical and mathematical content formatting.

Instructions:
1. Generate clear questions for any subject
2. Use LaTeX notation for ALL mathematical expressions, including basic arithmetic
3. Format ALL mathematical content between $ or $$ tags
4. Include detailed explanations with proper notation
5. Maintain notation integrity throughout
6. Always display time limit at the start of quiz

Content Requirements:
1. Mathematical Expression Rules (STRICT):
   - ALL numbers in equations must be in math mode: $2$, not 2
   - ALL variables must be in math mode: $x$, not x
   - ALL operators must be in math mode: $+$, $-$, $\cdot$, $\div$
   - ALL equations must be in math mode: $2x + 3 = 7$
   - ALL exponents must use curly braces: $x^{2}$, not $x^2$
   - ALL fractions must use \frac: $\frac{1}{2}$, not 1/2
   - ALL function names must use \text or predefined commands: $\text{f}(x)$ or $\sin(x)$

2. Question Format Examples:
   Multiple Choice:
   Question: What is the derivative of $f(x) = x^{2} + 3x + 1$?
   
   A) $\frac{d}{dx}f(x) = 2x + 3$
   B) $\frac{d}{dx}f(x) = x^{2} + 3$
   C) $\frac{d}{dx}f(x) = 2x$
   D) $\frac{d}{dx}f(x) = 2$

   Solution: 
   The correct answer is A.
   Step 1: $\frac{d}{dx}(x^{2}) = 2x$
   Step 2: $\frac{d}{dx}(3x) = 3$
   Step 3: $\frac{d}{dx}(1) = 0$
   Therefore, $\frac{d}{dx}f(x) = 2x + 3$

3. Common Expression Templates:
   - Basic arithmetic: $2 + 2 = 4$
   - Multiplication: $2 \cdot 3$ or $2 \times 3$
   - Division: $\frac{a}{b}$
   - Powers: $x^{2}$, $(x+y)^{2}$
   - Roots: $\sqrt{x}$, $\sqrt[n]{x}$
   - Functions: $\text{f}(x)$, $\sin(x)$
   - Derivatives: $\frac{d}{dx}$, $\text{f}'(x)$
   - Integrals: $\int_{a}^{b} x \, dx$
   - Limits: $\lim_{x \to a} f(x)$
   - Vectors: $\vec{v}$ or $\mathbf{v}$

4. Units and Numbers:
   - Scientific notation: $3.0 \times 10^{8}$
   - Units in text mode: $9.8 \text{ m/s}^{2}$
   - Mixed numbers: $3\frac{1}{2}$ or $\frac{7}{2}$

CRITICAL RULES:
1. EVERY mathematical symbol, number, or expression MUST be in math mode (between $ signs)
2. NEVER use plain text for mathematical expressions
3. ALWAYS use proper LaTeX commands for operators
4. ALWAYS use curly braces for exponents and subscripts
5. ALWAYS format solutions with step-by-step LaTeX notation
6. NEVER mix plain text and math notation in equations

Example Quiz Format:
Time Limit: 30 minutes

1. Question: Solve the equation $2x + 5 = 13$
   
   A) $x = 4$
   B) $x = 6$
   C) $x = 8$
   D) $x = 9$

   Solution:
   Step 1: Subtract $5$ from both sides
   $2x + 5 - 5 = 13 - 5$
   $2x = 8$
   
   Step 2: Divide both sides by $2$
   $\frac{2x}{2} = \frac{8}{2}$
   $x = 4$
   
   Therefore, the answer is A.
"""

# Function to format quiz content for PDF using OpenAI API
def format_quiz_for_pdf(quiz_text):
    messages = [
        {"role": "system", "content": """
Role: PDF Formatting Specialist for Educational Content

Task: Convert quiz content into print-ready format while preserving mathematical notation and structure.

Instructions:
1. Maintain clear section organization:
   - Time limit at the top
   - Questions numbered clearly
   - Multiple choice options indented
   - Solutions clearly marked
   
2. Format Mathematical Expressions:
   - Convert LaTeX to readable print format
   - Example: $\\frac{x}{y}$ → (x)/(y)
   - Example: $x^{2}$ → x^(2)
   - Example: $\\sqrt{x}$ → √(x)
   - Example: $\\cdot$ → ×
   - Example: $3 \\times 10^{8}$ → 3 × 10^(8)
   
3. Formatting Rules:
   - Use clear section breaks
   - Indent multiple choice options
   - Preserve question numbering
   - Mark solutions distinctly
   - Maintain consistent spacing
   - Ensure all special characters are PDF-safe
   
4. Output Structure:
   Time Limit: [time]
   
   Question 1:
   [Question text]
   A) [option]
   B) [option]
   C) [option]
   D) [option]
   
   Solution:
   [Step-by-step solution]
   
   [Repeat for each question]

5. Character Constraints:
   - Use only ASCII characters
   - Replace special symbols with print-safe alternatives
   - Maintain mathematical meaning while ensuring printability
"""},
        {"role": "user", "content": f"Convert this quiz content into print-ready format: \n\n{quiz_text}"}
    ]
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error formatting quiz for PDF: {str(e)}")
        return quiz_text

# Simplified PDF creation function that relies on the OpenAI formatting
def create_formatted_pdf(quiz_text):
    # Get formatted content from OpenAI
    formatted_content = format_quiz_for_pdf(quiz_text)
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Practice Quiz', 0, 1, 'C')
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', size=11)
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Simply write the OpenAI-formatted content
    for line in formatted_content.split('\n'):
        if line.strip():
            pdf.multi_cell(0, 8, txt=line)
            if "Question" in line or "Solution:" in line:
                pdf.ln(3)  # Extra space after question/solution headers
    
    try:
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        print(f"PDF generation error: {str(e)}")
        return None

# Add custom CSS styling for the app
st.markdown("""
    <style>
    /* Global text styles */
    .stMarkdown {
        font-family: 'Helvetica Neue', sans-serif;
        color: white;
    }
    
    /* Headers */
    h1 {
        color: white;
        font-weight: 600;
    }
    
    h2, h3 {
        color: white;
        font-weight: 500;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #FBCD5D;
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
        color: white;
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
        color: white;
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
        st.markdown("<h3 style='text-align: center; color: #FBCD5D; margin-bottom: 10px;'>Key Features</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; font-size: 16px; color: white; min-height: 200px;'>
        <ul style='list-style-type: none; padding-left: 0; margin: 0;'>
        <li style='margin-bottom: 8px;'>• AI-powered subject detection and quiz generation</li>
        <li style='margin-bottom: 8px;'> Multiple question formats and difficulty levels</li>
        <li style='margin-bottom: 8px;'>• Comprehensive answer explanations</li>
        <li style='margin-bottom: 8px;'>• Math-friendly with LaTeX support</li>
        <li style='margin-bottom: 8px;'> Head to Quiz Generator to start creating your quiz!</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h3 style='text-align: center; color: #FBCD5D; margin-bottom: 10px;'>Key Benefits</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; font-size: 16px; color: white; min-height: 200px;'>
        <ul style='list-style-type: none; padding-left: 0; margin: 0;'>
        <li style='margin-bottom: 8px;'>• Streamlined quiz creation for educators</li>
        <li style='margin-bottom: 8px;'>• Personalized learning experience</li>
        <li style='margin-bottom: 8px;'>• Instant feedback and explanations</li>
        <li style='margin-bottom: 8px;'>• Time-efficient exam preparation</li>
        <li style='margin-bottom: 8px;'>• Enhanced conceptual understanding</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

# Options : Quiz Generator
elif options == "Quiz Generator":
    st.title("Quiz Generator")
    
    if not st.session_state.url_processed:
        # Step 1: Get URLs
        st.subheader("Enter up to 5 URLs for content")
        
        # Create input fields for up to 5 URLs
        urls = []
        for i in range(5):
            col1, col2 = st.columns([5,1], gap="small")
            with col1:
                url = st.text_input(f"URL {i+1}:", key=f"url_{i}")
                if url:
                    urls.append(url)
            
        process_urls = st.button('Process URLs', key='process_urls')

        if process_urls and urls:
            try:
                with st.spinner('Processing URL content...'):
                    # Clear previous contents
                    st.session_state.website_contents = []
                    
                    # Process each URL
                    for url in urls:
                        try:
                            response = requests.get(url)
                            soup = BeautifulSoup(response.text, 'html.parser')
                            content = " ".join([p.get_text() for p in soup.find_all('p')])
                            st.session_state.website_contents.append(content)
                        except Exception as e:
                            st.error(f"Error processing URL {url}: {str(e)}")
                    
                    if st.session_state.website_contents:
                        # Combine all contents for subject detection and format suggestion
                        combined_content = " ".join(st.session_state.website_contents)
                        
                        # Steps 2 & 3: Detect subject and suggest format
                        st.session_state.detected_subject = detect_subject_area(combined_content)
                        st.session_state.format_suggestion = suggest_quiz_format(combined_content)
                        
                        st.session_state.url_processed = True
                        st.rerun()
                    else:
                        st.error("No content could be extracted from the provided URLs.")
            except Exception as e:
                st.error(f"Error processing URLs: {str(e)}")

    else:
        if st.session_state.quiz_text:
            # Display generated quiz and buttons
            st.subheader("Generated Quiz:")
            st.markdown(st.session_state.quiz_text)
            
            # Generate PDF data if it doesn't exist
            if st.session_state.pdf_data is None:
                st.session_state.pdf_data = create_formatted_pdf(st.session_state.quiz_text)
            
            st.markdown("---")
            
            # Create two columns for the buttons
            left_col, right_col = st.columns(2)
            
            with left_col:
                if st.session_state.pdf_data is not None:
                    st.download_button(
                        label="📥 Download Quiz (PDF)",
                        data=st.session_state.pdf_data,
                        file_name="quiz.pdf",
                        mime="application/pdf",
                        key="download_pdf"
                    )
            
            with right_col:
                if st.button("🔄 Generate New Quiz", key="new_quiz"):
                    st.session_state.url_processed = False
                    st.session_state.quiz_generated = False
                    st.session_state.quiz_text = None
                    st.session_state.pdf_data = None
                    st.rerun()

        else:
            # Display stored subject detection and suggestions
            st.info(f"Detected subject area: {st.session_state.detected_subject}")
            if st.session_state.format_suggestion:
                st.info(st.session_state.format_suggestion)

            # Step 4: Quiz configuration (no loading here)
            st.subheader("Quiz Configuration")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                difficulty = st.selectbox("Difficulty Level:", ["Beginner", "Intermediate", "Advanced"], key='difficulty')
            with col2:
                question_type = st.selectbox("Question Type:", 
                                           ["Multiple Choice", "Problem Solving", "Essay", "Mixed"],
                                           help="Mixed will create a balanced combination of different question types",
                                           key='question_type')
            with col3:
                num_questions = st.number_input("Number of Questions:", 
                                              min_value=1, 
                                              max_value=100, 
                                              value=5,
                                              help="Choose between 1-100 questions",
                                              key='num_questions')

            specific_topics = st.text_area("Quiz Context and Focus Areas:",
                        help="Help us understand your goals! What's the purpose of this quiz? Any specific topics or concepts you want to focus on?",
                        placeholder="Example: 'Preparing for midterm exam, focus on chapters 3-4' or 'Weekly practice quiz for calculus class, emphasize derivatives'",
                        height=100,
                        key='specific_topics')

            # Step 5: Generate quiz only when button is clicked
            if st.button("Generate Quiz"):
                if not openai.api_key:
                    st.error("Please enter your OpenAI API key first!")
                    st.stop()

                with st.spinner('Generating your quiz...'):
                    user_message = f"""Based on the following content: {' '.join(st.session_state.website_contents)[:4000]}... (truncated)
                    Please generate {num_questions} {question_type} questions at {difficulty} level.
                    {"Focus on these topics: " + specific_topics if specific_topics else ""}
                    Calculate and include appropriate time limit based on question types and difficulty.
                    Please format each question with clear A, B, C, D options for multiple choice, or step-by-step solutions for problem solving."""

                    struct = [{"role": "system", "content": System_Prompt}]
                    struct.append({"role": "user", "content": user_message})
                    
                    try:
                        chat = openai.ChatCompletion.create(
                            model="gpt-4o-mini",
                            messages=struct
                        )
                        st.session_state.quiz_text = chat.choices[0].message.content
                        # Generate PDF data immediately after quiz generation
                        st.session_state.pdf_data = create_formatted_pdf(st.session_state.quiz_text)
                        st.session_state.quiz_generated = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
