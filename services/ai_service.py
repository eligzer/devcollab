import os
import google.generativeai as genai

# Setup API Key securely
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    # We will handle misconfigurations gracefully in the route
    pass

# Initialize the model instance
# Using gemini-2.5-flash as the standard fast default for text operations
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_notes(topic: str) -> str:
    """Generate structured markdown notes for a given topic."""
    prompt = f"""
    You are an expert tutor. Please generate comprehensive, structured study notes on the topic: "{topic}".
    Format the response in pure Markdown. Ensure it includes:
    - A main heading
    - An easy-to-understand explanation
    - Key bullet points
    - Practical examples if applicable.
    Do not wrap the whole response in a markdown code block (e.g. ```markdown), just return the raw markdown text.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating notes: {str(e)}"

def summarize_note(content: str) -> str:
    """Provide a concise summary of the provided text."""
    prompt = f"""
    You are a highly efficient assistant. Please provide a concise, high-level summary of the following notes.
    Keep it brief and capture the main takeaways.
    
    Notes:
    {content}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error summarizing notes: {str(e)}"

def explain_text(text: str, is_code: bool = False) -> str:
    """Explain a specific concept or code snippet."""
    if is_code:
        prompt = f"""
        You are a senior software engineer. Please explain the following code snippet step-by-step.
        Describe what it does and how it works.
        
        Code:
        {text}
        """
    else:
        prompt = f"""
        You are a knowledgeable tutor. Please explain the following concept or text in simple, easy-to-understand terms.
        
        Text:
        {text}
        """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error explaining text: {str(e)}"

def generate_questions(content: str) -> str:
    """Generate practice questions based on the note content."""
    prompt = f"""
    You are an educational assistant. Based on the provided study notes, generate a brief practice quiz.
    Include:
    - 2 Multiple Choice Questions (with answers at the bottom)
    - 2 Short Answer Questions
    - A list of 3-5 key vocabulary terms to remember.
    
    Format the output cleanly in Markdown. Do not wrap in a markdown code block.
    
    Notes:
    {content}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating questions: {str(e)}"

def chat_assistant(query: str, context: str) -> str:
    """Answer a chat query using the note content as context."""
    prompt = f"""
    You are a helpful AI study assistant. Answer the user's question, using the provided context as your primary source of truth.
    If the answer isn't in the context, use your general knowledge but mention it's outside the current notes.
    Keep the answer conversational and informative.
    
    Context:
    {context}
    
    User Question: {query}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error processing chat: {str(e)}"
