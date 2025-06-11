# app.py 
# Streamlit app to load a local prospecting tool
import streamlit as st
import logging
import os
from dotenv import load_dotenv
import datetime # <-- Import datetime
import re # <-- Import re for filename sanitization

# --- Load Environment Variables ---
# Make sure your .env file is in the same directory or configure secrets for deployment
load_dotenv()
# Check if essential keys are loaded (optional but recommended)
AZURE_KEY_LOADED = bool(os.getenv("AZURE_OPENAI_API_KEY"))
LM_STUDIO_API_KEY = "lm-studio"
BRAVE_KEY_LOADED = bool(os.getenv("BRAVE_SEARCH_KEY"))


# --- Import the main function from your generator script ---
# Ensure report_generator_local.py is in the same directory
try:
    # <-- Import the new function
    from report_generator_local3 import generate_full_report, generate_docx_bytes, CHROMEDRIVER_PATH
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - StreamlitApp - %(message)s')

except ImportError as e:
    # Check specifically for docx import error if it occurs again
    if 'docx' in str(e):
         st.error(f"Fatal Error: Import failed. The 'python-docx' library is required for downloading reports but might be missing.")
         st.error(f"Please add 'python-docx' to your requirements.txt and run 'pip install -r requirements.txt'.")
         st.error(f"Details: {e}")
    else:
        st.error(f"Fatal Error: Could not import from 'report_generator_local.py'. Ensure it's in the same directory. Details: {e}")
    st.stop()

# --- Initialize Session State ---
if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False
    st.session_state.report_text = None
    st.session_state.identifier = None

# --- Streamlit App UI ---
st.set_page_config(layout="wide")
st.title("🤖 Company Prospecting Report Generator")
st.markdown("Enter a company domain name (e.g., `google.com`) or company name (e.g., `Microsoft`) to generate a sales prospecting report.")

# --- Check Configuration Status (Sidebar) ---
# (Keep the sidebar code as it was)
st.sidebar.header("Configuration Status")
if AZURE_KEY_LOADED:
    st.sidebar.success("Azure OpenAI Key: Loaded")
else:
    st.sidebar.error("Azure OpenAI Key: Not Found in .env")

if BRAVE_KEY_LOADED:
    st.sidebar.success("Brave Search Key: Loaded")
else:
    st.sidebar.warning("Brave Search Key: Not Found in .env (News/Size search disabled)")

try:
    # from report_generator_local import CHROMEDRIVER_PATH # Already imported above
    if os.path.exists(CHROMEDRIVER_PATH):
         st.sidebar.success(f"ChromeDriver: Found")
         st.sidebar.caption(f"`{CHROMEDRIVER_PATH}`")
    else:
         st.sidebar.error("ChromeDriver: NOT FOUND.")
         st.sidebar.caption(f"Path: `{CHROMEDRIVER_PATH}`\nWebsite scraping skipped.")
         st.sidebar.warning("Check path in report_generator_local.py or install.")
except NameError: # Handle if CHROMEDRIVER_PATH isn't defined
     st.sidebar.warning("Could not check ChromeDriver path (constant missing?).")
except Exception as e: # Catch other potential errors
     st.sidebar.error(f"Error checking ChromeDriver path: {e}")


# --- Input Area ---
identifier_input = st.text_input(
    "Enter Company Domain or Name:",
    placeholder="example.com or Example Inc.",
    help="The script will attempt to derive the name from domain or guess domain from name."
)

# --- Report Generation Button ---
if st.button("✨ Generate Report", type="primary"):
    # Reset previous report state on new generation attempt
    st.session_state.report_generated = False
    st.session_state.report_text = None
    st.session_state.identifier = None

    if not identifier_input:
        st.warning("Please enter a company domain or name.")
    elif not AZURE_KEY_LOADED:
         st.error("Cannot generate report: Azure OpenAI API Key is missing.")
    else:
        st.info(f"Starting report generation for: **{identifier_input}**")
        st.info("This process can take a few minutes...")

        with st.spinner("Gathering data, analyzing, and generating report..."):
            try:
                result = generate_full_report(identifier_input)
                st.success("Report generation process finished!")

                if isinstance(result, dict):
                    if "report" in result:
                        # --- Store result in session state ---
                        st.session_state.report_text = result["report"]
                        st.session_state.identifier = identifier_input
                        st.session_state.report_generated = True # Flag success

                        # --- Display Report ---
                        st.markdown("---")
                        st.header("Generated Report:")
                        st.markdown(st.session_state.report_text) # Display report

                    elif "error" in result:
                        st.error(f"An error occurred during report generation:")
                        st.error(f"**Error:** {result.get('error', 'Unknown Error')}")
                        if result.get('details'):
                            st.warning(f"**Details:** {result.get('details')}")
                    else:
                        st.error("Received an unexpected result format.")
                        st.json(result)
                else:
                     st.error("Received an unexpected result type.")
                     st.write(result)

            except Exception as e:
                st.error("A critical error occurred while running report generation.")
                st.exception(e)

# --- Display Download Button (Only if report was generated successfully) ---
if st.session_state.report_generated and st.session_state.report_text:
    st.markdown("---") # Separator
    try:
        # Generate DOCX bytes using the stored text and identifier
        docx_bytes = generate_docx_bytes(
            st.session_state.identifier,
            st.session_state.report_text
        )

        if docx_bytes:
            # Create a filename (basic sanitization)
            sanitized_id = re.sub(r'[^\w\s-]', '', st.session_state.identifier).strip().replace(' ', '_')[:50]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            file_name = f"Report_{sanitized_id}_{timestamp}.docx"

            st.download_button(
                label="📄 Download Report as DOCX",
                data=docx_bytes,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key='download-docx' # Add a key for stability
            )
        else:
             st.warning("Could not generate DOCX file content for download.")

    except Exception as e:
         st.error("An error occurred while preparing the DOCX file for download.")
         st.exception(e)


# --- Footer ---
st.markdown("---")
st.caption("© 2025 MarketStar. All rights reserved.")