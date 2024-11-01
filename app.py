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

# Configure Streamlit page settings
st.set_page_config(page_title="QuizGenius", page_icon="🧠", layout="wide")

# Add MathJax support
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

# Core functions
def detect_subject_area(text):
    messages = [
        {"role": "system", "content": """[System prompt content]"""},
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
        {"role": "system", "content": """[System prompt content]"""},
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
        {"role": "system", "content": """[System prompt content]"""},
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

# Warning page
if not st.session_state.accepted_terms:
    st.markdown("""[Warning page content]""", unsafe_allow_html=True)
    agree = st.checkbox("I have read and agree to the above warnings and guidelines")
    if st.button("Continue to QuizGenius", disabled=not agree):
        st.session_state.accepted_terms = True
        st.rerun()
    st.stop()

# Sidebar setup
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

# Apply styling
st.markdown("""[CSS styling content]""", unsafe_allow_html=True)

# Home page
if options == "Home":
    st.markdown("""[Home page content]""", unsafe_allow_html=True)

# Quiz Generator page
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
            
            def create_formatted_pdf(quiz_text):
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
                pdf.set_font("Arial", size=12)
                pdf.set_auto_page_break(auto=True, margin=15)
                
                unicode_text = convert_math_to_unicode(quiz_text)
                lines = unicode_text.split('\n')
                
                for line in lines:
                    try:
                        cleaned_line = ''.join(char for char in line if ord(char) < 256)
                        if line.startswith('Question'):
                            pdf.set_font('Arial', 'B', 12)
                            pdf.multi_cell(0, 10, cleaned_line)
                            pdf.set_font('Arial', '', 12)
                        elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                            pdf.cell(10)
                            pdf.multi_cell(0, 10, cleaned_line)
                        else:
                            pdf.multi_cell(0, 10, cleaned_line)
                        if not line.strip():
                            pdf.ln(5)
                    except:
                        continue
                
                try:
                    return pdf.output(dest='S').encode('latin-1')
                except:
                    pdf = PDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.cell(200, 10, "Error: Could not generate PDF with special characters", 0, 1, 'C')
                    return pdf.output(dest='S').encode('latin-1')
            
            st.session_state.pdf_data = create_formatted_pdf(st.session_state.quiz_text)
            
            col1, col2, col3 = st.columns([1.5, 1.5, 3])
            with col1:
                if st.session_state.pdf_data:
                    st.download_button("Download Quiz (PDF)", st.session_state.pdf_data, "quiz.pdf", "application/pdf")
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
                num_questions = st.number_input("Number of questions:", 1, 20, 5)
                specific_topics = st.text_area("Specific topics or concepts to focus on (optional):")
                time_limit = st.number_input("Suggested time limit (minutes):", 5, 180, 30)
            
            with col2:
                question_type = st.multiselect("Select question types:", 
                    ["Multiple Choice", "Essay", "Problem Sets", "Problem Solving", "Mixed"],
                    default=["Multiple Choice"])
            
            if st.button("Generate Quiz"):
                if not openai.api_key:
                    st.error("Please enter your OpenAI API key first!")
                    st.stop()

                with st.spinner('Generating your quiz...'):
                    user_message = f"""Based on the following content: {st.session_state.website_content[:4000]}... (truncated)
                    Please generate {num_questions} {', '.join(question_type)} questions at {difficulty} level.
                    {"Focus on these topics: " + specific_topics if specific_topics else ""}
                    Suggested time limit: {time_limit} minutes.
                    Please format each question with clear A, B, C, D options for multiple choice, or step-by-step solutions for problem solving."""

                    try:
                        chat = openai.ChatCompletion.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": System_Prompt},
                                {"role": "user", "content": user_message}
                            ]
                        )
                        st.session_state.quiz_text = chat.choices[0].message.content
                        st.session_state.quiz_generated = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
