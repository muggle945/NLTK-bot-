import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from groq import Groq
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from backend.data_processor import WellDataProcessor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize session state variables
if 'conversation' not in st.session_state:
    st.session_state.conversation = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'processor' not in st.session_state:
    st.session_state.processor = WellDataProcessor()
if 'metrics' not in st.session_state:
    st.session_state.metrics = None

def initialize_chat():
    if st.session_state.conversation is None:
        groq_api_key = os.getenv('GROQ_API_KEY', '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')
        model = st.session_state.get('model', 'mixtral-8x7b-32768')
        
        groq_chat = ChatGroq(
            groq_api_key=groq_api_key,
            model_name=model
        )
        
        memory = ConversationBufferWindowMemory(k=st.session_state.get('memory_length', 5))
        
        # Restore chat history
        for message in st.session_state.chat_history:
            memory.save_context(
                {'input': message['human']},
                {'output': message['AI']}
            )
        
        st.session_state.conversation = ConversationChain(
            llm=groq_chat,
            memory=memory
        )
    
    return st.session_state.conversation

def on_submit():
    user_input = st.session_state.user_input
    if user_input:
        with st.spinner('Processing...'):
            try:
                conversation = initialize_chat()
                
                # Prepare context if metrics are available
                if st.session_state.metrics is not None:
                    metrics_df = st.session_state.metrics
                    context = f"Based on the well data analysis:\n"
                    context += f"Average daily duration: {metrics_df['total_duration_minutes'].mean():.2f} minutes\n"
                    context += f"Average off hours: {metrics_df['off_hours'].mean():.2f} hours\n"
                    full_prompt = f"{context}\nQuestion: {user_input}"
                else:
                    full_prompt = user_input
                
                # Get response
                response = conversation(full_prompt)
                
                # Store in chat history
                st.session_state.chat_history.append({
                    'human': user_input,
                    'AI': response['response']
                })
                
                # Clear input
                st.session_state.user_input = ""
            except Exception as e:
                st.error(f"Error: {str(e)}")

def main():
    st.title("Well Analysis Chat Assistant")
    
    # Sidebar configuration
    st.sidebar.title("Configuration")
    model = st.sidebar.selectbox(
        'Choose Model',
        ['mixtral-8x7b-32768', 'llama2-70b-4096'],
        key='model'
    )
    
    memory_length = st.sidebar.slider(
        'Conversation Memory Length:',
        1, 10, 5,
        key='memory_length'
    )
    
    # File upload
    uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
    
    if uploaded_file is not None:
        result = st.session_state.processor.load_data(uploaded_file)
        if isinstance(result, str):
            st.error(f"Error loading file: {result}")
        else:
            st.success("File loaded successfully!")
            
            # Date range selection
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
            with col2:
                end_date = st.date_input("End Date")
            
            if st.button("Process Data"):
                with st.spinner('Processing data...'):
                    metrics = st.session_state.processor.calculate_daily_metrics(start_date, end_date)
                    if isinstance(metrics, pd.DataFrame):
                        st.session_state.metrics = metrics
                        st.write("Daily Metrics:")
                        st.dataframe(metrics)
                    else:
                        st.error(f"Error processing data: {metrics}")
    
    # Display chat history
    st.subheader("Chat History")
    for message in st.session_state.chat_history:
        st.write("User:", message['human'])
        st.write("Assistant:", message['AI'])
    
    # Chat input with callback
    st.text_input(
        "Ask a question:",
        key="user_input",
        max_chars=500,
        on_change=on_submit
    )
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.conversation = None
        st.experimental_rerun()

if __name__ == "__main__":
    main()