# Required imports for application functionality
import os
import openai
import streamlit as st
from streamlit_option_menu import option_menu
import requests
import pandas as pd
import numpy as np
import faiss
from bs4 import BeautifulSoup
from openai import OpenAI
import tiktoken
from langchain import OpenAI as LangChainOpenAI
import chromadb

# Configure Streamlit page settings - MUST BE FIRST!
st.set_page_config(page_title="ShopRisk", page_icon="📊", layout="wide")

# Initialize session state variables
if 'accepted_terms' not in st.session_state:
    st.session_state.accepted_terms = False
if 'data_processed' not in st.session_state:
    st.session_state.data_processed = False
if 'embeddings_created' not in st.session_state:
    st.session_state.embeddings_created = False
if 'index_ready' not in st.session_state:
    st.session_state.index_ready = False
if 'api_key_valid' not in st.session_state:
    st.session_state.api_key_valid = False
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = None
if 'faiss_index' not in st.session_state:
    st.session_state.faiss_index = None
if 'struct' not in st.session_state:
    st.session_state.struct = []

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
            color: black;
        }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='warning-header'>⚠️ Important Warnings and Guidelines</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='warning-section'>", unsafe_allow_html=True)
    st.markdown("### 1. API Key Security")
    st.markdown("""
    - Keep your OpenAI API key secure and private
    - Never share your API key with others
    - Ensure proper API key format (starts with 'sk-')
    - Monitor API usage and costs
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='warning-section'>", unsafe_allow_html=True)
    st.markdown("### 2. Data Usage Guidelines")
    st.markdown("""
    - Only use accurate and verified delivery data
    - Ensure data is properly formatted
    - Keep sensitive business information confidential
    - Regular data updates recommended
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    agree = st.checkbox("I have read and agree to the above warnings and guidelines")
    if st.button("Continue to ShopRisk", disabled=not agree):
        st.session_state.accepted_terms = True
        st.rerun()
    
    st.stop()

# Set up sidebar with API key input and navigation
with st.sidebar:
    st.image('images/shoprisk.jpg', use_column_width=True)
    
    st.markdown('<p style="color: white;">Enter OpenAI API token:</p>', unsafe_allow_html=True)
    col1, col2 = st.columns([5,1], gap="small")
    with col1:
        api_key = st.text_input('', type='password', label_visibility="collapsed")
    with col2:
        check_api = st.button('▶', key='api_button')
    
    if check_api:
        if not api_key:
            st.warning('Please enter your OpenAI API token!')
        else:
            try:
                client = OpenAI(api_key=api_key)
                response = client.completions.create(
                    model="gpt-3.5-turbo-instruct",
                    prompt="Hello",
                    max_tokens=5
                )
                st.session_state.api_key_valid = True
                st.success('API key is valid!')
            except Exception as e:
                st.error('Invalid API key or API error occurred')
                st.session_state.api_key_valid = False
    
    options = option_menu(
        menu_title="Navigation",
        options=["Home", "Risk Analysis", "Data Insights", "Settings"],
        icons=["house", "graph-up", "lightbulb", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "icon": {"color": "#FBCD5D", "font-size": "20px"},
            "nav-link": {"font-size": "17px", "text-align": "left", "margin": "5px", "--hover-color": "#262730"},
            "nav-link-selected": {"background-color": "#262730"}
        }
    )

# Function to process delivery data and create embeddings
def process_delivery_data(text_data):
    try:
        # Create embeddings using OpenAI
        response = openai.Embedding.create(
            input=text_data,
            model="text-embedding-ada-002"
        )
        return np.array([response['data'][0]['embedding']])
    except Exception as e:
        st.error(f"Error creating embeddings: {str(e)}")
        return None

# Function to generate risk analysis
def generate_risk_analysis(context, query):
    try:
        structured_prompt = f"""
        Based on the following delivery data from the Philippine e-commerce operations:

        {context}

        Please analyze this data as ShopRisk and answer the following query:
        {query}

        Provide specific metrics and insights considering:
        1. Historical trends and patterns
        2. Weather impacts
        3. Seasonal factors
        4. Courier performance
        5. Regional variations
        """

        chat = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are ShopRisk, an AI expert in e-commerce delivery risk analysis."},
                {"role": "user", "content": structured_prompt}
            ],
            temperature=0.5,
            max_tokens=1500
        )
        return chat.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating analysis: {str(e)}")
        return None

# Options : Home
if options == "Home":
    st.markdown("<h1 style='text-align: center; margin-bottom: 15px; color: white;'>Welcome to ShopRisk!</h1>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align: center; padding: 10px; margin-bottom: 20px; font-size: 18px; color: white;'>ShopRisk is your intelligent companion for e-commerce risk assessment and financial loss prediction. Our AI-powered system analyzes delivery data to help you make informed decisions about your Lazada and Shopee operations in the Philippines.</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<h3 style='text-align: center; color: #FBCD5D; margin-bottom: 10px;'>Key Features</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; font-size: 16px; color: black; min-height: 200px;'>
        <ul style='list-style-type: none; padding-left: 0; margin: 0;'>
        <li style='margin-bottom: 8px;'>• Financial Loss Prediction</li>
        <li style='margin-bottom: 8px;'>• Risk Assessment Analysis</li>
        <li style='margin-bottom: 8px;'>• Courier Performance Tracking</li>
        <li style='margin-bottom: 8px;'>• Weather Impact Analysis</li>
        <li style='margin-bottom: 8px;'>• Regional Risk Mapping</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

# Options : Risk Analysis
elif options == "Risk Analysis":
    st.title("Risk Analysis")
    
    # File uploader for delivery data
    uploaded_file = st.file_uploader("Upload delivery data (CSV, Excel)", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        try:
            # Process the uploaded file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Convert dataframe to text for processing
            text_data = df.to_string()
            
            # Create embeddings
            embeddings = process_delivery_data(text_data)
            
            if embeddings is not None:
                st.session_state.embeddings = embeddings
                st.session_state.documents = [text_data]
                
                # Create FAISS index
                dimension = embeddings.shape[1]
                index = faiss.IndexFlatL2(dimension)
                index.add(embeddings)
                st.session_state.faiss_index = index
                
                st.success("Data processed successfully!")
                
                # Risk analysis query input
                user_query = st.text_area("Enter your risk analysis query:", 
                                        help="Example: What are the main risk factors affecting deliveries in Metro Manila?")
                
                if st.button("Generate Analysis"):
                    if user_query:
                        # Get similar documents
                        query_embedding = process_delivery_data(user_query)
                        D, I = st.session_state.faiss_index.search(query_embedding, 1)
                        
                        # Generate analysis
                        context = st.session_state.documents[I[0][0]]
                        analysis = generate_risk_analysis(context, user_query)
                        
                        if analysis:
                            st.markdown("### Analysis Results")
                            st.markdown(analysis)
                    else:
                        st.warning("Please enter a query for analysis.")
                        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

# Options : Data Insights
elif options == "Data Insights":
    st.title("Data Insights")
    # Add data visualization and insights features here

# Options : Settings
elif options == "Settings":
    st.title("Settings")
    # Add settings configuration options here
