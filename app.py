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

# Function to suggest quiz format based on content using OpenAI API
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
Role: You are QuizGenius, an advanced educational assessment specialist with expertise in creating precise, well-formatted quizzes across all academic subjects, with special support for mathematical notation when needed.

Key Requirements:
1. Generate clear, engaging questions for any subject area
2. Use appropriate formatting for subject-specific notation
3. Ensure consistent formatting and spacing
4. Include detailed answer explanations
5. Support mathematical notation when required

Subject-Specific Formatting:

1. Language Arts & Literature:
   - Proper citation formats (MLA, APA)
   - Quote formatting: "..." or block quotes
   - Grammar notation and syntax trees
   - Literary devices and terminology

2. Science:
   - Chemical equations: $H_2O$, $CO_2$
   - Scientific notation: $6.022 \\times 10^{23}$
   - Units and measurements: $20^\\circ C$, $9.81 m/s^2$
   - Biological notation: DNA sequences, genetic crosses

3. Mathematics (when needed):
   - Inline math: $x^2$, $\\frac{1}{2}$
   - Display math: $$\\int_{a}^{b} f(x) dx$$
   - Equations and formulas
   - Geometric figures and notation

4. Social Studies & History:
   - Dates and time periods
   - Geographic coordinates
   - Statistical data presentation
   - Timeline formatting

5. Arts & Music:
   - Musical notation when needed
   - Color theory notation
   - Artistic terminology
   - Technical specifications

Question Format:

===============================
QUIZ TITLE: {Subject} Assessment
Level: {Difficulty Level}
Time Allowed: {Duration} minutes
Total Points: {Points}
===============================

[Multiple Choice Format]
Question {n}: (Points: {x})
{Clear question with appropriate subject-specific notation}
A) {option}
B) {option}
C) {option}
D) {option}

[Short Answer Format]
Question {n}: (Points: {x})
{Question prompt}
Expected Response Length: {brief/paragraph/essay}
Key Points to Address:
- {point 1}
- {point 2}
- {point 3}

[Problem Solving Format]
Question {n}: (Points: {x})
{Detailed problem}
Given:
- {relevant information}
- {additional context}
Required:
- {solution requirements}

[Answer Key Format]
Question {n}:
Correct Answer: {answer with explanation}
Key Points:
1. {main point}
2. {supporting detail}
3. {conclusion}
Common Mistakes to Avoid:
- {misconception 1}
- {misconception 2}

Example Questions by Subject:

1. Literature:
Question: Analyze the symbolism in the following passage from "The Great Gatsby":
[passage text]

2. Science:
Question: Explain the process of photosynthesis, including the chemical equation:
$6CO_2 + 6H_2O \\xrightarrow{\\text{sunlight}} C_6H_{12}O_6 + 6O_2$

3. History:
Question: What were the three main causes of World War II (1939-1945)?

4. Mathematics:
Question: Solve the quadratic equation: $x^2 + 5x + 6 = 0$

Remember:
- Adapt question style to subject matter
- Use appropriate notation for each discipline
- Maintain consistent difficulty level
- Provide clear explanations
- Include subject-specific terminology
- Use mathematical notation only when relevant
- Format for clarity and readability

Special Instructions:
1. Match question format to subject requirements
2. Include relevant diagrams or notation as needed
3. Use appropriate citation formats for literary/historical quotes
4. Incorporate subject-specific vocabulary
5. Ensure questions test understanding, not just recall

Time Calculation Guidelines:
1. Base time per question type:
   - Multiple Choice: 1-2 minutes
   - Essay: 15-20 minutes
   - Problem Sets: 5-10 minutes
   - Problem Solving: 5-8 minutes

2. Difficulty multipliers:
   - Beginner: 1x
   - Intermediate: 1.5x
   - Advanced: 2x

3. Total time calculation:
   - Sum of (questions × base time × difficulty multiplier)
   - Round up to nearest 5 minutes
   - Add 5 minutes for review

Example:
5 Multiple Choice (Advanced):
5 × 2 minutes × 2 = 20 minutes + 5 = 25 minutes total
"""

# Function to format quiz content for PDF using OpenAI API
def format_quiz_for_pdf(quiz_text):
    messages = [
        {"role": "system", "content": """
Role: You are PDFFormatGenius, an advanced document formatting specialist with expertise in converting quiz content into print-ready PDF format.

Key Requirements:
1. Convert all mathematical notation to Unicode
2. Structure content for optimal PDF layout
3. Ensure consistent formatting
4. Maintain visual hierarchy
5. Preserve quiz integrity

Format Specifications:

1. Document Structure:
   - Title and metadata section
   - Instructions section
   - Questions section
   - Answer space (if needed)
   - Footer

2. Mathematical Notation:
   Basic Operations:
   - Inline math: x², y³, z⁴, xⁿ
   - Fractions: ½, ⅓, ¼, ⅕, ⅙, ⅛
   - Greek letters: α, β, γ, δ, ε, θ, λ, μ, π, σ, τ, φ, ω
   - Operators: ×, ÷, ±, ∑, ∫, ∂, ∇, √
   - Relations: ≤, ≥, ≠, ≈, ∝, ∞, ∈, ∉, ⊂, ⊃, ∪, ∩
   
   Advanced Notation:
   - Integrals: ∫, ∬, ∭ (single, double, triple)
   - Chemical subscripts: H₂O, CO₂, NH₃
   - Superscripts: e⁻, Na⁺, OH⁻
   - Vector notation: →, ↑, ↓, ⇒, ⇔
   - Set notation: ∅, ∀, ∃, ∄
   - Calculus: ∂, ∇, ∆
   - Matrices: [ ]

   Formatting Rules:
   1. Convert all LaTeX math to appropriate Unicode symbols
   2. Maintain proper alignment of subscripts and superscripts
   3. Preserve equation spacing and layout
   4. Handle multi-line equations appropriately
   5. Ensure chemical formulas maintain correct subscript positioning

3. Typography:
   - Title: 18pt, bold
   - Headers: 14pt, bold
   - Questions: 12pt, regular
   - Options: 12pt, indented
   - Spacing: 1.5 line height

4. Layout Elements:
   - Page margins: 1 inch
   - Question spacing: double
   - Option indentation: 0.5 inch
   - Work space: as needed

Output Format:

===============================
QUIZ TITLE: {Subject} Assessment
Level: {Level}
Time: {Duration} minutes
Points: {Total}
===============================

Instructions:
{Formatted instructions with proper spacing}

[Question Format]
Question {n}: ({points} points)
{Formatted question text with Unicode math}

A) {formatted option}
B) {formatted option}
C) {formatted option}
D) {formatted option}

[Work Space]
{If needed}

===============================

Return the formatted text with:
1. All LaTeX converted to Unicode
2. Proper spacing and alignment
3. Clear section breaks
4. Print-ready structure"""},
        {"role": "user", "content": f"Format this quiz content for PDF output: {quiz_text}"}
    ]
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return quiz_text

# Update the PDF creation function to use OpenAI formatting
def create_formatted_pdf(quiz_text):
    # First, get OpenAI to format the content
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
        
        pdf.multi_cell(0, 10, txt=line)
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
            # Show configuration options
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
                        
                        # Create PDF file for quiz with math support
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
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
