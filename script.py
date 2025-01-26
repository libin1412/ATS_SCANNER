import streamlit as st
import google.generativeai as genai
import os
import tempfile
from pdf2image import convert_from_path
import PyPDF2 as pdf
import base64
from dotenv import load_dotenv
import io
import json
import re

# Load environment variables
load_dotenv()

# Specify the Poppler path explicitly in your code
poppler_path = r'C:\Users\libin\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin'
os.environ['PATH'] += os.pathsep + poppler_path

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def input_pdf_setup(uploaded_file):
    """Convert PDF to image for Gemini Vision processing"""
    if uploaded_file is not None:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

        try:
            # Convert PDF to images using convert_from_path
            images = convert_from_path(temp_file_path, poppler_path=poppler_path)
            
            # Take the first page and convert to base64
            first_page = images[0]
            img_byte_arr = io.BytesIO()
            first_page.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            return base64.b64encode(img_byte_arr).decode()
        
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)

def get_gemini_response(input_prompt, pdf_content, jd):
    """Generate response using Gemini Pro Vision with enhanced error handling"""
    try:
        model = genai.GenerativeModel('gemini-pro')  # Changed to gemini-pro
        
        # Validate inputs
        if not pdf_content or not jd:
            st.error("Missing PDF content or job description")
            return None

        # Combine inputs more explicitly
        full_prompt = f"""
        Analyze the following resume in the context of the job description:

        Job Description:
        {jd}

        Detailed Prompt:
        {input_prompt}
        """

        # Generate response
        response = model.generate_content(full_prompt)
        
        # Validate response
        if not response or not response.text:
            st.error("No response generated")
            return None

        # Attempt to extract JSON-like structure
        return extract_json_from_text(response.text)
    
    except Exception as e:
        st.error(f"Detailed Gemini API Error: {e}")
        return None

def extract_json_from_text(text):
    """
    Attempt to extract a JSON-like structure from the generated text
    """
    # Look for JSON-like structure
    json_match = re.search(r'\{.*?\}', text, re.DOTALL)
    
    if json_match:
        try:
            # Try to parse the extracted JSON-like text
            json_text = json_match.group(0)
            parsed_json = json.loads(json_text)
            return json.dumps(parsed_json, indent=2)
        except json.JSONDecodeError:
            # If direct parsing fails, try to clean and parse
            try:
                # Remove any leading/trailing non-JSON characters
                cleaned_text = re.sub(r'^[^\{]*', '', text)
                cleaned_text = re.sub(r'[^\}]*$', '', cleaned_text)
                return json.dumps(json.loads(cleaned_text), indent=2)
            except:
                return text
    
    return text

# Enhanced Prompt Template
input_prompt = """
You are an advanced AI-powered Applicant Tracking System (ATS) for a technical role in autonomous systems.

Evaluation Criteria:
1. Precisely match technical skills
2. Assess depth of technical experience
3. Identify specific skill gaps
4. Provide actionable technical feedback

Required Output Format (Strict JSON):
{
    "JD_Match_Percentage": "Exact percentage matching job requirements",
    "Missing_Critical_Keywords": ["technical keywords missing"],
    "Skill_Alignment_Score": "Numerical score out of 10",
    "Detailed_Technical_Feedback": "Precise technical assessment",
    "Recommended_Technical_Improvements": ["specific technical enhancement suggestions"]
}

Focus Areas:
- Autonomous driving technologies
- ROS implementation
- Sensor fusion techniques
- AI/ML algorithms
- Programming proficiency
"""

# Streamlit App
def main():
    st.set_page_config(
        page_title="Advanced ATS Resume Scanner",
        page_icon="🚀",
        layout="wide"
    )

    st.title("🚀 Advanced ATS Resume Scanner")
    st.markdown("## Optimize Your Technical Resume")

    # Job Description Input
    jd = st.text_area("Paste Detailed Job Description", height=200)
    
    # Resume Upload
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")

    if st.button("Analyze Resume"):
        if uploaded_file and jd:
            try:
                # Extract PDF content and convert to image
                pdf_text = extract_pdf_text(uploaded_file)
                pdf_image = input_pdf_setup(uploaded_file)

                # Generate Response from Gemini AI
                response = get_gemini_response(input_prompt, pdf_image, jd)
                
                # Display Results
                st.subheader("ATS Analysis Results")
                
                # Parse and display response
                if response:
                    try:
                        # Try to parse as JSON
                        parsed_response = json.loads(response)
                        st.json(parsed_response)
                    except json.JSONDecodeError:
                        # If JSON parsing fails, show raw response
                        st.warning("Detailed analysis:")
                        st.write(response)

                # Additional insights
                st.subheader("PDF Text Extraction")
                st.text_area("Extracted Text", pdf_text, height=200)

            except Exception as e:
                st.error(f"An error occurred during resume analysis: {e}")

def extract_pdf_text(uploaded_file):
    """Extract text from PDF"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name

    try:
        reader = pdf.PdfReader(temp_file_path)
        text = ""
        for page in range(len(reader.pages)):
            page = reader.pages[page]
            text += str(page.extract_text())
        return text
    finally:
        os.unlink(temp_file_path)

if __name__ == "__main__":
    main()
