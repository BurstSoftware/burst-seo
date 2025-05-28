import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup # for URL fetching

# --- Configuration & Helper Functions ---
def configure_genai(api_key):
    try:
        genai.configure(api_key=api_key)
        # You can also list models to verify connection and see available ones
        # models = [m.name for m in genai.list_models()]
        # print(f"Available models: {models}")
        return True
    except Exception as e:
        st.error(f"Error configuring Google AI: {e}")
        return False

def get_content_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text_content = "\n".join([p.get_text() for p in paragraphs])
        return text_content
    except Exception as e:
        st.error(f"Error fetching URL: {e}")
        return None

def analyze_with_gemini(prompt_template, user_content, criterion_name, model_name): # Added model_name
    if not st.session_state.get("gemini_configured"):
        st.warning("Google AI not configured. Please enter your API key.")
        return None
    if not model_name:
        st.warning("Please select a Gemini model in the sidebar.")
        return None
    try:
        st.info(f"Using model: {model_name} for {criterion_name}") # Info about which model is used
        model = genai.GenerativeModel(model_name) # Use the selected model_name
        full_prompt = prompt_template.format(user_content=user_content)

        with st.spinner(f"🤖 Gemini ({model_name.split('/')[-1]}) is analyzing for {criterion_name}..."):
            response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        # Improved error message to include model name
        st.error(f"Error during Gemini API call for {criterion_name} using model {model_name}: {e}")
        st.error("Hint: Ensure the selected model supports 'generateContent' and your API key has access. Common models are 'gemini-1.0-pro' or 'gemini-1.5-flash-latest'.")
        return f"Error: Could not get analysis for {criterion_name} using {model_name}."

# --- Streamlit App ---
st.set_page_config(layout="wide", page_title="AI Overview Content Optimizer")
st.title("🚀 AI Overview Content Optimizer (with Google AI)")

# --- API Key Input & Model Selection in Sidebar ---
st.sidebar.header("🔑 Google AI Configuration")
api_key_input = st.sidebar.text_input("Enter your Google AI API Key:", type="password", key="api_key_input_val")

# Available models - you might want to fetch this dynamically if you have many or they change often
# For now, providing common ones. The SDK uses 'models/gemini-1.0-pro', but 'gemini-1.0-pro' often works.
# The cURL example used 'gemini-2.0-flash'. The current SDK equivalent for "flash" is 'gemini-1.5-flash-latest'.
# Always check `genai.list_models()` for the exact names if you encounter issues.
AVAILABLE_MODELS = {
    "Gemini 1.0 Pro (General Purpose)": "gemini-1.0-pro",
    "Gemini 1.5 Flash (Fast & Efficient)": "gemini-1.5-flash-latest",
    # Add other models as needed, e.g., "gemini-1.5-pro-latest"
}
# Reverse mapping for display if needed, or just use keys for selectbox
model_display_names = list(AVAILABLE_MODELS.keys())

# Initialize session state for selected model
if 'selected_model_name' not in st.session_state:
    st.session_state.selected_model_name = AVAILABLE_MODELS[model_display_names[0]] # Default to first model

selected_model_display_name = st.sidebar.selectbox(
    "Choose Gemini Model:",
    options=model_display_names,
    index=model_display_names.index([k for k, v in AVAILABLE_MODELS.items() if v == st.session_state.selected_model_name][0]) # Find current index
)
st.session_state.selected_model_name = AVAILABLE_MODELS[selected_model_display_name]


if 'gemini_configured' not in st.session_state:
    st.session_state.gemini_configured = False

if api_key_input:
    if configure_genai(api_key_input):
        st.session_state.gemini_configured = True
        st.sidebar.success("Google AI Configured!")
        st.sidebar.info(f"Selected Model: {selected_model_display_name}")
    else:
        st.session_state.gemini_configured = False
        st.sidebar.error("Invalid API Key or configuration error.")
else:
    st.sidebar.info("Please enter your Google AI API key to enable analysis.")


st.markdown("This tool helps you optimize your web content for Google's AI Overviews by leveraging Google's own Generative AI.")
st.markdown("---")

# --- Content Input ---
st.header("1. Provide Your Content")
input_method = st.radio("How would you like to provide content?",
                        ("Enter URL", "Paste Text", "Describe Topic/Query"),
                        key="input_method_radio")

user_content_for_analysis = "" # This variable seems unused, direct use of session_state.user_content is better

if input_method == "Enter URL":
    url = st.text_input("Enter the URL of your web page:")
    if url:
        if st.button("Fetch Content from URL"):
            with st.spinner("Fetching content..."):
                content = get_content_from_url(url)
                if content:
                    st.session_state.user_content = content
                    st.text_area("Fetched Content (first 1000 chars):", content[:1000]+"...", height=150, disabled=True)
                else:
                    st.session_state.user_content = "" # Clear if fetch failed
elif input_method == "Paste Text":
    pasted_text = st.text_area("Paste your content here:", height=200, key="pasted_content_area")
    if pasted_text: # Update session state on input
        st.session_state.user_content = pasted_text
elif input_method == "Describe Topic/Query":
    query_topic_for_analysis = st.text_input("Describe the main topic or target query for your content:", key="query_topic_input")
    if query_topic_for_analysis: # Update session state on input
        st.session_state.user_content = f"Content Topic: {query_topic_for_analysis}" # Use this as context for Gemini


# Store content in session state for reuse
if 'user_content' not in st.session_state:
    st.session_state.user_content = ""


# --- Guided Analysis Section ---
if st.session_state.user_content and st.session_state.gemini_configured:
    st.markdown("---")
    st.header("2. AI-Powered Content Analysis")
    st.markdown(f"**Using Model: {selected_model_display_name}** (`{st.session_state.selected_model_name}`)")


    if st.button("Analyze for Clarity & Conciseness"):
        st.subheader("Clarity & Conciseness Analysis")
        prompt_clarity = """
        Your role is an expert content editor specializing in optimizing web text for Google AI Overviews.
        Analyze the following content for clarity and conciseness, keeping in mind it might be used by Google to generate a summary.
        Identify 1-2 strengths and provide 2-3 actionable suggestions to improve its suitability for AI summarization.
        Be specific in your suggestions.

        Content to analyze:
        ---
        {user_content}
        ---
        """
        if st.session_state.user_content:
            feedback = analyze_with_gemini(
                prompt_clarity,
                st.session_state.user_content,
                "Clarity & Conciseness",
                st.session_state.selected_model_name # Pass selected model
            )
            if feedback:
                st.markdown(feedback)
        else:
            st.warning("Please provide content first.")

    if st.button("Analyze for E-E-A-T Signals"):
        st.subheader("E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) Analysis")
        prompt_eeat = """
        Your role is an SEO expert focusing on Google's E-E-A-T guidelines for AI Overviews.
        Review the provided content. What signals of Experience, Expertise, Authoritativeness, and Trustworthiness are present?
        What signals are missing or could be strengthened? Provide 3 specific, actionable recommendations
        to enhance E-E-A-T for this content in the context of Google AI Overviews.

        Content to analyze:
        ---
        {user_content}
        ---
        """
        if st.session_state.user_content:
            feedback = analyze_with_gemini(
                prompt_eeat,
                st.session_state.user_content,
                "E-E-A-T",
                st.session_state.selected_model_name # Pass selected model
            )
            if feedback:
                st.markdown(feedback)
        else:
            st.warning("Please provide content first.")

    st.markdown("---")
    st.info("Remember: AI suggestions are guidance. Always use your best judgment and knowledge of your audience.")

elif not st.session_state.gemini_configured and st.session_state.get('api_key_input_val'):
    # This case might occur if API key was entered but configuration failed silently or was cleared
    st.warning("Google AI configuration might be incomplete or API key is invalid. Please check the sidebar.")
elif not st.session_state.gemini_configured:
    st.warning("Please configure your Google AI API Key in the sidebar to proceed.")
elif not st.session_state.user_content:
    st.info("Please provide content using one of the methods above to start the analysis.")


st.sidebar.markdown("---")
st.sidebar.caption("This app uses the Google Generative AI SDK. Ensure you have a valid API key and understand the API usage terms and potential costs. Model availability and naming can change; check the official Google AI documentation for the latest model identifiers if you encounter issues.")
st.sidebar.markdown("To see all available models for your API key, you can temporarily add this to the `configure_genai` function: `print([m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods])` and check your terminal when the app runs with an API key.")
