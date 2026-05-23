import os
import json
import re
from dotenv import load_dotenv
from groq import Groq
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# Load environment variables (GROQ_API_KEY)
load_dotenv()

# Setup Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Define custom exception for Tenacity to catch specifically if we want
class GroqRateLimitError(Exception):
    pass

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60), 
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(Exception)
)
def call_groq_api(messages, model="llama-3.3-70b-versatile"):
    """Wrapper to call Groq API with robust retry logic for rate limits."""
    print(f"Calling Groq API ({model})...")
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.2, # Low temperature for deterministic/factual extraction
            max_tokens=1000
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"API Error: {str(e)}")
        raise e

def synthesize_themes(clusters):
    """Pass clusters to LLM to extract themes, quotes, and actions."""
    print("Synthesizing clusters into themes...")
    
    prompt = f"""
You are a senior product intelligence analyst writing an internal weekly product brief.

Below are clusters of real user reviews from a fintech trading app.

CLUSTERS:
{json.dumps(clusters, indent=2)}

TASK:
Identify the 3 strongest meaningful themes from these clusters.
If fewer than 3 distinct themes are present, derive sub-themes from the strongest cluster without hallucinating unrelated issues.

Output EXACTLY in this format:

## Top 3 Themes
- [Theme Name]: [1 sentence explaining the specific issue and its business impact]
- [Theme Name]: [1 sentence explaining the specific issue and its business impact]
- [Theme Name]: [1 sentence explaining the specific issue and its business impact]

## Voice of the User
- "[Exact verbatim quote from the reviews above]"
- "[Exact verbatim quote from the reviews above]"
- "[Exact verbatim quote from the reviews above]"

## Recommended Actions
- [Concrete operational action directly tied to Theme 1]
- [Concrete operational action directly tied to Theme 2]
- [Concrete operational action directly tied to Theme 3]

QUOTE SELECTION RULES:
- Quotes must come VERBATIM from the provided review data. Do not paraphrase.
- Prioritize quotes that express: pricing frustration, execution issues, feature gaps, workflow friction, or trust/reliability concerns.
- Never select a generic praise quote.

ACTION RULES:
- Actions must be operationally specific and directly map to the discovered themes.
- GOOD example: "Audit stop-loss execution logic during high-volatility market conditions and compare triggered vs missed SL events over the past 30 days."
- BAD example: "Improve the app experience."
- No vague advice. No generic statements.

HARD CONSTRAINTS:
- Maximum 230 words total output.
- No fluff, no preamble, no closing remarks.
- Do not mention AI, clustering, embeddings, or data science.
- Do not add any information not present in the provided reviews.
- Output must read like an internal weekly product intelligence brief.
"""
    
    messages = [
        {"role": "system", "content": "You are a senior product intelligence analyst writing concise internal briefs. You are factual, precise, and never hallucinate."},
        {"role": "user", "content": prompt}
    ]
    
    return call_groq_api(messages)

def deep_pii_validation(synthesis_text):
    """Extract quotes from the synthesis and do a secondary LLM PII scrub."""
    print("Performing Deep Contextual PII Validation...")
    
    prompt = f"""
    You are a strict data privacy officer. 
    Review the following product management report.
    Look strictly at the quotes in the "Voice of the User" section. 
    If you see ANY contextual PII (like someone accidentally typing their PAN, email, phone number, address, or internal user ID within a sentence), replace it with [REDACTED]. 
    Do NOT change the meaning or any other words.
    If no PII is present, return the text exactly as it was.
    
    TEXT:
    {synthesis_text}
    """
    
    messages = [
        {"role": "system", "content": "You are a strict data privacy officer."},
        {"role": "user", "content": prompt}
    ]
    
    return call_groq_api(messages)

def count_words(text):
    return len(re.findall(r'\b\w+\b', text))

def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found in environment variables. Please create a .env file.")
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, '..', 'phase2_clustering', 'output', 'clusters.json')
    
    if not os.path.exists(input_file):
        print(f"Error: Could not find {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        clusters = json.load(f)
        
    # Step 1: Synthesis
    raw_synthesis = synthesize_themes(clusters)
    
    # Step 2: Deep PII Validation
    safe_synthesis = deep_pii_validation(raw_synthesis)
    
    # Step 3: Word count enforcement (< 250 words)
    word_count = count_words(safe_synthesis)
    print(f"Final word count: {word_count}")
    
    if word_count > 250:
        print("Warning: Generated text exceeded 250 words! The LLM prompt might need tighter constraints.")
        # We accept it for now but log the warning.
        
    # Save output
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'pulse_note.md')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Groww Weekly Pulse\n\n")
        f.write(safe_synthesis)
        
    print(f"Successfully generated Weekly Pulse Note at {output_file}")

if __name__ == "__main__":
    main()
