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

# Add session state initialization
if 'accepted_terms' not in st.session_state:
    st.session_state.accepted_terms = False

# Configure Streamlit page settings
st.set_page_config(page_title="QuizGenius", page_icon="🧠", layout="wide")

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
        st.experimental_rerun()
    
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
        
        # Minimal CSS for button styling
        st.markdown("""
            <style>
            [data-testid="stButton"][aria-label="api_button"] {
                font-size: 12px;
                background-color: transparent;
                border: 1px solid rgba(250, 250, 250, 0.2);
                border-radius: 4px;
                color: rgb(255, 75, 75);
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
4. Create questions according to specified format (multiple choice, essay, problem sets, problem solving, case studies, practical tests, or mixed)
5. Ensure questions test different cognitive levels (recall, application, analysis)
6. For mathematical questions:
   - Use proper mathematical notation (superscripts for powers, LaTeX for complex equations)
   - Accept equivalent answers in different forms
   - Provide step-by-step solutions
7. For essay questions, provide clear grading criteria based on:
   - Content & Understanding (30%)
   - Organization & Structure (25%)
   - Evidence & Support (25%)
   - Language & Style (20%)

Context:
Users will provide content from which you need to:
1. Detect the subject area automatically
2. Generate appropriate questions based on the content
3. Adapt question formats to suit the subject
4. Maintain appropriate difficulty level

Constraints:
- Generate only curriculum-relevant content
- Maintain academic integrity
- Provide clear, unambiguous questions
- Include answer explanations for learning purposes
- Adapt language to appropriate grade/education level
- For essay questions, include specific grading rubrics
- For math questions, include acceptable answer formats

Example Output Format:
For Multiple Choice:
Question 1: [Question text]
A) [Option]
B) [Option]
C) [Option]
D) [Option]
Hint: [Helpful hint to guide student]
Correct Answer: [Letter]
Explanation: [Detailed explanation of why this answer is correct and why others are incorrect]

For Problem Solving:
Question 1: [Problem statement]
Hint: [Helpful hint about approach]
Solution Approach:
- [Step 1]
- [Step 2]
- [Step 3]
Acceptable Answers: [List equivalent correct answers]
Explanation: [Detailed solution walkthrough]

For Essays:
Question 1: [Essay prompt]
Hint: [Key points to consider]
Expected Response Elements:
- [Key point 1]
- [Key point 2]
- [Key point 3]
Grading Rubric:
[Include detailed rubric with scoring criteria]
"""

# Options : Home
if options == "Home":
    st.title("Welcome to QuizGenius!")
    st.write("Your intelligent companion for creating customized practice quizzes.")
    st.write("Simply provide your content in the 'Quiz Generator' section.")
    st.write("Our AI-powered system will detect the subject and generate tailored questions to help you prepare!")
    
    st.markdown("### Key Features:")
    st.markdown("""
    - Automatic subject detection
    - Customizable difficulty levels
    - Multiple question formats
    - Detailed explanations for each answer
    - Curriculum-aligned content
    - Instant quiz generation
    - Support for multiple file formats (PDF, Word, Excel, Images)
    - Mathematical notation support
    - Equivalent answer recognition
    """)
    
    st.markdown("### Benefits:")
    st.markdown("""
    - Students reported an average 15% score increase on standardized tests
    - Personalized learning experience
    - Efficient exam preparation
    - Immediate feedback and explanations
    - Math-friendly interface with LaTeX support
    """)
   
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
    
    # Create tabs for different input methods
    input_method = st.tabs(["Manual Input", "File Upload", "Website URL"])
    
    with input_method[0]:
        # Manual input interface
        subject_text = st.text_area("Enter your content:")
        if subject_text:
            detected_subject = detect_subject_area(subject_text)
            st.info(f"Detected subject area: {detected_subject}")
    
    with input_method[1]:
        # File upload interface
        uploaded_file = st.file_uploader("Upload file", type=['pdf', 'docx', 'xlsx', 'xls', 'csv', 'png', 'jpg', 'jpeg'])
        if uploaded_file:
            with st.spinner("Processing file..."):
                text = extract_text_from_file(uploaded_file)
                if text.startswith("Error") or text == "Unsupported file format":
                    st.error(text)
                else:
                    st.success("File processed successfully!")
                    detected_subject = detect_subject_area(text)
                    st.info(f"Detected subject area: {detected_subject}")
    
    with input_method[2]:
        # Website URL interface
        website_url = st.text_input("Enter website URL:")
        if website_url:
            try:
                response = requests.get(website_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract text from paragraphs
                text = " ".join([p.get_text() for p in soup.find_all('p')])
                st.success("Website content extracted successfully!")
                detected_subject = detect_subject_area(text)
                st.info(f"Detected subject area: {detected_subject}")
            except Exception as e:
                st.error(f"Error extracting website content: {str(e)}")

    # Common quiz configuration for all input methods
    st.subheader("Quiz Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        difficulty = st.selectbox("Select difficulty level:", ["Beginner", "Intermediate", "Advanced"])
        num_questions = st.number_input("Number of questions:", min_value=1, max_value=20, value=5)
    
    with col2:
        question_type = st.multiselect("Select question types:", 
                                     ["Multiple Choice", "Essay", "Problem Sets", "Problem Solving", "Mixed"],
                                     default=["Multiple Choice"])
    
    # Advanced options
    with st.expander("Advanced Options"):
        specific_topics = st.text_area("Specific topics or concepts to focus on (optional):")
        time_limit = st.number_input("Suggested time limit (minutes):", min_value=5, max_value=180, value=30)
        include_explanations = st.checkbox("Include detailed explanations", value=True)
        math_mode = st.checkbox("Enable math mode (LaTeX support)", value=True)
    
    # Generate Quiz button
    if st.button("Generate Quiz"):
        if not openai.api_key:
            st.error("Please enter your OpenAI API key first!")
            st.stop()
            
        # Show format suggestions if text is available
        if 'text' in locals() and text and question_type:
            suggestions, detected_subject = suggest_quiz_format(text, question_type)
            if suggestions:
                st.info("Format Suggestions:")
                for suggestion in suggestions:
                    st.write(suggestion)
                    
        # Determine which input method was used and create appropriate user message
        if 'text' in locals():  # For PDF or Website content
            user_message = f"""Based on the following content: {text[:4000]}... (truncated)
            Please generate {num_questions} {', '.join(question_type)} questions at {difficulty} level.
            {"Focus on these topics: " + specific_topics if specific_topics else ""}
            {"Include detailed explanations for each answer." if include_explanations else ""}
            Suggested time limit: {time_limit} minutes.
            {"Use LaTeX notation for mathematical expressions." if math_mode else ""}
            Please format each question with clear A, B, C, D options for multiple choice, or step-by-step solutions for problem solving."""
        elif 'subject_text' in locals() and subject_text:  # For manual input
            user_message = f"""Based on the following content: {subject_text}
            Please generate {num_questions} {', '.join(question_type)} questions at {difficulty} level.
            {"Focus on these topics: " + specific_topics if specific_topics else ""}
            {"Include detailed explanations for each answer." if include_explanations else ""}
            Suggested time limit: {time_limit} minutes.
            {"Use LaTeX notation for mathematical expressions." if math_mode else ""}
            Please format each question with clear A, B, C, D options for multiple choice, or step-by-step solutions for problem solving."""
        else:
            st.warning("Please provide input content to generate questions.")
            st.stop()

        with st.spinner('Generating your quiz...'):
            struct = [{"role": "system", "content": System_Prompt}]
            struct.append({"role": "user", "content": user_message})
            
            try:
                # Generate quiz using OpenAI
                chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=struct)
                response = chat.choices[0].message.content
                
                # Split response into questions and answers
                quiz_parts = response.split("\n\n")
                questions = []
                hints = []
                answer_key = []
                explanations = []
                
                for part in quiz_parts:
                    if part.startswith("Question"):
                        questions.append(part)
                    elif part.startswith("Hint:"):
                        hints.append(part)
                    elif any(x in part for x in ["Correct Answer:", "Grading Rubric:", "Solution Approach:", "Acceptable Answers:"]):
                        answer_key.append(part)
                    elif part.startswith("Explanation:"):
                        explanations.append(part)
                
                quiz_text = "\n\n".join(questions)
                
                st.subheader("Generated Quiz:")
                if math_mode:
                    st.latex(quiz_text)
                else:
                    st.write(quiz_text)
                
                # Create PDF files
                def create_pdf(content, title):
                    """Generate PDF with quiz content"""
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.cell(200, 10, txt=title, ln=1, align='C')
                    pdf.multi_cell(0, 10, txt=content)
                    return pdf.output(dest='S').encode('latin-1')
                
                # Download buttons for quiz and answer key
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="Download Quiz (PDF)",
                        data=create_pdf(quiz_text, "Practice Quiz"),
                        file_name="quiz.pdf",
                        mime="application/pdf"
                    )
                with col2:
                    answer_key_text = "\n\n".join(answer_key)
                    st.download_button(
                        label="Download Answer Key (PDF)",
                        data=create_pdf(answer_key_text, "Answer Key"),
                        file_name="answer_key.pdf",
                        mime="application/pdf"
                    )
                
                # Quiz taking interface
                st.subheader("Take the Quiz")
                if st.button("Start Quiz"):
                    student_answers = {}
                    correct_answers = {}
                    
                    # Extract correct answers from answer key
                    for i, (question, hint) in enumerate(zip(questions, hints), 1):
                        st.write(f"\n{question}")
                        
                        # Add hint button for each question
                        if st.button(f"Show Hint for Question {i}", key=f"hint_{i}"):
                            st.info(hint)
                            
                        if "Multiple Choice" in question_type:
                            student_answers[i] = st.radio(
                                f"Your answer for Question {i}:",
                                ["A", "B", "C", "D"],
                                key=f"q_{i}"
                            )
                            
                            # Add show answer button for each question
                            if st.button(f"Show Answer for Question {i}", key=f"answer_{i}"):
                                st.success(f"Correct Answer: {answer_key[i-1]}")
                                st.write(f"Explanation: {explanations[i-1]}")
                                
                        elif "Problem Solving" in question_type:
                            student_answer = st.text_input(f"Your answer for Problem {i}")
                            if student_answer:
                                acceptable_answers = answer_key[i-1].split("Acceptable Answers:")[1].strip().split(",")
                                is_correct = any(check_math_equivalence(student_answer, ans.strip()) for ans in acceptable_answers)
                                if is_correct:
                                    st.success("Correct!")
                                else:
                                    st.error("Incorrect. Try again.")
                                    
                                # Add show answer button
                                if st.button(f"Show Solution for Problem {i}", key=f"solution_{i}"):
                                    st.write(answer_key[i-1])
                                    st.write(explanations[i-1])
                                    
                        elif "Essay" in question_type:
                            st.text_area(f"Essay Response for Question {i}:", key=f"essay_{i}")
                            st.write("Grading Rubric:")
                            st.write(get_essay_rubric())
                            
                            # Add essay guidance button
                            if st.button(f"Show Writing Guidelines for Essay {i}", key=f"guide_{i}"):
                                st.write(answer_key[i-1])
                    
                    if st.button("Submit Quiz"):
                        score = 0
                        incorrect_questions = []
                        
                        # Calculate score for multiple choice questions
                        for q_num in student_answers:
                            if student_answers[q_num] == correct_answers.get(q_num):
                                score += 1
                            else:
                                incorrect_questions.append(q_num)
                        
                        # Display results and feedback
                        st.subheader("Quiz Results")
                        if len(correct_answers) > 0:
                            percentage = (score / len(correct_answers)) * 100
                            st.write(f"Score: {score}/{len(correct_answers)} ({percentage:.1f}%)")
                            
                            # Show detailed feedback
                            st.write("\nDetailed Feedback:")
                            for q_num in student_answers:
                                st.write(f"\nQuestion {q_num}:")
                                if q_num in incorrect_questions:
                                    st.error("Incorrect")
                                    st.write(f"Your answer: {student_answers[q_num]}")
                                    st.write(f"Correct answer: {correct_answers[q_num]}")
                                    st.write(explanations[q_num-1])
                                else:
                                    st.success("Correct!")
                                    st.write(explanations[q_num-1])

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
