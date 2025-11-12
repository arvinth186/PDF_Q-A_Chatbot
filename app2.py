import streamlit as st
import os
from dotenv import load_dotenv
import time

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")

# Initialize the Groq LLM
llm=ChatGroq(model="llama-3.1-8b-instant")

# prompt template
prompt = ChatPromptTemplate.from_template(
    """
You are a helpful research assistant. 
Answer the question thoroughly and clearly based on the provided context only.

<context>
{context}
</context>

Question: {input}

Provide a detailed, structured, and well-explained answer. 
If applicable, include reasoning, definitions, and examples from the document. 
Use paragraph form — not just bullet points.
"""
)


# Streamlit App

st.set_page_config(page_title="📄 PDF Q&A Chatbot", layout="wide")
st.title("📘 PDF Q&A Chatbot")

uploaded_file = st.file_uploader("📤 Upload your PDF", type=["pdf"])
user_question = st.text_input("💬 Ask a question about your PDF")



# ---------------------- TYPING EFFECT FUNCTION ----------------------
def type_text(text, delay=0.008, chunk_size=3):
    display_box = st.empty()
    displayed_text = ""
    for i in range(0, len(text), chunk_size):
        displayed_text += text[i:i + chunk_size]
        display_box.markdown(f"**🤖 Chatbot:** {displayed_text}▌")
        time.sleep(delay)
    display_box.markdown(f"**🤖 Chatbot:** {displayed_text}")


# ---------------------- FUNCTION TO PROCESS UPLOADED PDF ----------------------

# process uploaded PDF and create vector embeddings

def process_upload_pdf(uploaded_file):
    if uploaded_file is not None:
        with open("temp_uploaded.pdf",'wb') as f:
            f.write(uploaded_file.getbuffer())

        loader = PyPDFLoader("temp_uploaded.pdf")
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        final_docs = text_splitter.split_documents(docs)

        embeddings = HuggingFaceEmbeddings()
        vector_store = FAISS.from_documents(final_docs, embeddings)

        return vector_store,final_docs
    else:
        st.warning("Please upload a PDF file to proceed.")
        return None,None
    

# Button actions

if uploaded_file:

    if st.button("Answer My Question"):
        if user_question:
            vector_store,docs = process_upload_pdf(uploaded_file)
            if vector_store:
                retriever = vector_store.as_retriever()
                document_chain = create_stuff_documents_chain(llm,prompt)
                retrieval_chain = create_retrieval_chain(retriever,document_chain)

                start = time.process_time()
                response = retrieval_chain.invoke({'input':user_question})
                end = time.process_time()

                st.write(f"⏱ Time taken: {end - start:.2f} seconds")
                with st.spinner("Generating response..."):
                    type_text(response['answer'], delay=0.015)


                with st.expander("📚 Retrieved Context"):
                    for i, doc in enumerate(response['context']):
                        st.markdown(f"**Chunk {i+1}:**")
                        st.write(doc.page_content)
                        st.write("---")
        else:
            st.warning("Please enter a question before clicking.")



































