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
2. Use proper LaTeX notation for all mathematical expressions
3. Ensure consistent formatting across all question types
4. Include detailed explanations with proper notation
5. Maintain notation integrity throughout
6. Always display time limit at the start of quiz

Context:
Creating customized quizzes across academic subjects with emphasis on proper notation rendering.

Content Requirements:
1. Subject-Specific Formatting
   - Mathematics: Use LaTeX notation (e.g., $\\frac{x}{y}$ for fractions, $\\sqrt{x}$ for roots)
   - Chemistry: Proper chemical formulas (e.g., H₂O, CO₂)
   - Physics: Scientific notation and units (e.g., $3.0 \\times 10^8$ m/s)
   - Computer Science: Code blocks with proper syntax highlighting
   - Music: Musical notation when needed
   - Languages: Proper diacritical marks and special characters

2. Question Format Structure
   - Clear question numbering
   - Properly formatted mathematical expressions using LaTeX
   - Well-structured multiple choice options
   - Aligned equations when needed using LaTeX align environment
   - Proper subscripts and superscripts using LaTeX notation

3. Time Calculation Guidelines
   Multiple Choice Questions:
   - Beginner: 1 minute per question
   - Intermediate: 1.5 minutes per question
   - Advanced: 2 minutes per question
   
   Problem Solving/Sets:
   - Beginner: 3 minutes per question
   - Intermediate: 5 minutes per question
   - Advanced: 7 minutes per question
   
   Essay Questions:
   - Beginner: 10 minutes per question
   - Intermediate: 15 minutes per question
   - Advanced: 20 minutes per question

   Additional Time Allowances:
   - Reading time: 5 minutes
   - Planning time: 5 minutes
   - Review time: 10% of total quiz time
   
   Total Time Calculation:
   1. Sum the time for all questions based on type and difficulty
   2. Add reading time (5 minutes)
   3. Add planning time (5 minutes)
   4. Add 10% of subtotal for review
   5. Round up to nearest 5 minutes
   
   Example:
   5 Multiple Choice (Intermediate) = 5 × 1.5 = 7.5 minutes
   2 Problem Solving (Intermediate) = 2 × 5 = 10 minutes
   Subtotal = 17.5 minutes
   + Reading time = 5 minutes
   + Planning time = 5 minutes
   Subtotal = 27.5 minutes
   + Review time (10%) = 2.75 minutes
   Total = 30.25 minutes
   Rounded = 35 minutes

Constraints:
1. Mathematical Notation Rules:
   - ALL mathematical expressions MUST be in LaTeX mode using $ or $$
   - Basic arithmetic: $2 + 2 = 4$
   - Multiplication: Use $\cdot$ or $\times$, never use *
   - Powers/exponents: Use $x^{2}$ or $2^{n}$, never x^2 or 2^n
   - Variables: Italicized in math mode: $x$, $y$, $n$
   - Functions: $f(x)$, $g(x)$, never f(x) or g(x)
   - Derivatives: $f'(x)$ or $\frac{d}{dx}f(x)$
   - Units: Use \text{} in math mode: $9.8 \text{ m/s}^2$

2. Common Mathematical Expressions:
   - Fractions: $\frac{a}{b}$
   - Square roots: $\sqrt{x}$
   - nth roots: $\sqrt[n]{x}$
   - Powers: $x^{n}$, $(x+y)^{2}$
   - Subscripts: $x_{1}$, $a_{n}$
   - Functions: $f(x)$, $\sin(x)$, $\cos(x)$
   - Derivatives: $\frac{d}{dx}$, $f'(x)$, $\frac{d^2y}{dx^2}$
   - Integrals: $\int_{a}^{b} x \, dx$
   - Limits: $\lim_{x \to a} f(x)$
   - Summations: $\sum_{i=1}^{n} x_i$
   - Vectors: $\vec{v}$ or $\mathbf{v}$

Examples:
1. Calculus Question:
   Find $f'(x)$ if $f(x) = x^{2} + 3x + 1$
   
   A) $f'(x) = 2x + 3$
   B) $f'(x) = x^{2} + 3$
   C) $f'(x) = 2x$
   D) $f'(x) = 2$

   Solution: 
   $\frac{d}{dx}[x^{2}] = 2x$
   $\frac{d}{dx}[3x] = 3$
   $\frac{d}{dx}[1] = 0$
   Therefore, $f'(x) = 2x + 3$

2. Physics Question:
   A particle moves according to $s(t) = 3t^{2} - 4t + 2$. Find its velocity at $t = 2$.
   
   Solution:
   $v(t) = \frac{d}{dt}s(t) = 6t - 4$
   At $t = 2$: $v(2) = 6(2) - 4 = 8$ $\text{m/s}$

3. Algebra Question:
   Simplify $(x^{2} + 2x + 1)(x - 1)$
   
   Solution:
   $= x^{3} + 2x^{2} + x - (x^{2} + 2x + 1)$
   $= x^{3} + x^{2} - x - 1$

IMPORTANT FORMATTING RULES:
1. Never use plain text for mathematical expressions
2. Always wrap math in $ or $$ tags
3. Always use proper LaTeX notation for exponents: x^{2} not x^2
4. Always use \cdot or \times for multiplication
5. Always use \text{} for units in math mode
6. Always use proper function notation in math mode
7. Always show step-by-step solutions with proper notation
"""

# Function to format quiz content for PDF using OpenAI API
def format_quiz_for_pdf(quiz_text):
    messages = [
        {"role": "system", "content": """
Role:
QuizGenius PDF Formatter specializing in print-ready quiz formats.

Instructions:
1. Convert LaTeX math to ASCII/Unicode
2. Format equations for readability
3. Ensure consistent spacing
4. Use supported characters only
5. Handle multi-line equations

Context:
Creating PDF-compatible quiz content.

Content Requirements:
1. Question Formatting
   - Clear numbering and spacing
   - ASCII-safe mathematical expressions
   - Proper alignment and indentation

2. Character Conversion Rules
   - Use ASCII fractions
   - Simple operators
   - Basic notation

Constraints:
1. ASCII/Unicode characters only
2. Basic symbol support
3. Consistent formatting
4. Print-ready output

Examples:
[existing conversion examples...]

Output Structure:
[existing structure format...]
"""},
        {"role": "user", "content": f"Format this quiz content for PDF output..."}
    ]
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Use GPT-4o-mini for better handling
            messages=messages,
            temperature=0.1  # Lower temperature for more consistent formatting
        )
        return response.choices[0].message.content
    except Exception as e:
        return quiz_text

# Update the PDF creation function to handle the formatted content
def create_formatted_pdf(quiz_text):
    # Get OpenAI to format and convert notation to ASCII-safe format
    formatted_content = format_quiz_for_pdf(quiz_text)
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Practice Quiz', 0, 1, 'C')
            self.ln(10)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', size=12)
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Process the OpenAI-formatted content
    lines = formatted_content.split('\n')
    for line in lines:
        if '=======' in line:
            pdf.ln(5)
            continue
        
        try:
            pdf.multi_cell(0, 10, txt=line)
        except Exception as e:
            # If encoding fails, try to remove problematic characters
            cleaned_line = ''.join(c for c in line if ord(c) < 128)
            pdf.multi_cell(0, 10, txt=cleaned_line)
            
        if not line.strip():
            pdf.ln(5)
    
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
        <li style='margin-bottom: 8px;'>• Head to Quiz Generator to start creating your quiz!</li>
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
            # Display the generated quiz
            st.subheader("Generated Quiz:")
            st.markdown(st.session_state.quiz_text)
            
            # Add a separator
            st.markdown("---")
            
            # Create two columns for the buttons
            left_col, right_col = st.columns(2)
            
            # Generate PDF data
            pdf_data = create_formatted_pdf(st.session_state.quiz_text)
            
            # Left column: Download PDF button
            with left_col:
                if pdf_data is not None:
                    st.download_button(
                        label="📥 Download Quiz (PDF)",
                        data=pdf_data,
                        file_name="quiz.pdf",
                        mime="application/pdf",
                        key="download_pdf"
                    )
            
            # Right column: Generate New Quiz button
            with right_col:
                if st.button("🔄 Generate New Quiz", key="new_quiz"):
                    # Reset all relevant session state variables
                    st.session_state.show_config = False
                    st.session_state.quiz_generated = False
                    st.session_state.website_content = None
                    st.session_state.quiz_text = None
                    st.rerun()

        else:
            # Show subject detection and suggestions first
            detected_subject = detect_subject_area(st.session_state.website_content)
            st.info(f"Detected subject area: {detected_subject}")
            suggestion = suggest_quiz_format(st.session_state.website_content)
            if suggestion:
                st.info(suggestion)

            # Quiz configuration
            st.subheader("Quiz Configuration")

            # Store form inputs in variables (no processing yet)
            col1, col2, col3 = st.columns(3)
            with col1:
                difficulty = st.selectbox("Difficulty Level:", ["Beginner", "Intermediate", "Advanced"])
            with col2:
                question_type = st.selectbox("Question Type:", 
                                           ["Multiple Choice", "Problem Solving", "Essay", "Mixed"],
                                           help="Mixed will create a balanced combination of different question types")
            with col3:
                num_questions = st.number_input("Number of Questions:", 
                                              min_value=1, 
                                              max_value=100, 
                                              value=5,
                                              help="Choose between 1-100 questions")

            specific_topics = st.text_area("Quiz Context and Focus Areas:",
                        help="Help us understand your goals! What's the purpose of this quiz? Any specific topics or concepts you want to focus on?",
                        placeholder="Example: 'Preparing for midterm exam, focus on chapters 3-4' or 'Weekly practice quiz for calculus class, emphasize derivatives'",
                        height=100)

            # Only generate quiz when button is clicked
            if st.button("Generate Quiz"):
                if not openai.api_key:
                    st.error("Please enter your OpenAI API key first!")
                    st.stop()

                with st.spinner('Generating your quiz...'):
                    # Generate quiz
                    user_message = f"""Based on the following content: {st.session_state.website_content[:4000]}... (truncated)
                    Please generate {num_questions} {', '.join(question_type)} questions at {difficulty} level.
                    {"Focus on these topics: " + specific_topics if specific_topics else ""}
                    Calculate and include appropriate time limit based on question types and difficulty.
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
                        st.rerun()

                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
