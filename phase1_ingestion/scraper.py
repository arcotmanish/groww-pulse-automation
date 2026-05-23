import pandas as pd
import re
import datetime
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from google_play_scraper import Sort, reviews
from app_store_scraper import AppStore

# Ensure consistent langdetect results
DetectorFactory.seed = 0

def clean_text(text):
    if not isinstance(text, str):
        return ""
    
    # Redact Emails
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '<REDACTED_EMAIL>', text)
    # Redact Phone Numbers (10 digits, optional country code)
    text = re.sub(r'(?:\+91|91)?\s?[6-9]\d{9}', '<REDACTED_PHONE>', text)
    # Redact PAN Cards
    text = re.sub(r'[A-Z]{5}[0-9]{4}[A-Z]{1}', '<REDACTED_PAN>', text, flags=re.IGNORECASE)
    # Redact standard 6-digit user IDs
    text = re.sub(r'\b\d{6}\b', '<REDACTED_ID>', text)

    return text.strip()

def is_english(text):
    try:
        return detect(text) == 'en'
    except LangDetectException:
        return False

def scrape_play_store():
    print("Scraping Play Store reviews...")
    # Fetching ~1000 recent reviews (adjust count as needed for 8-12 weeks)
    result, _ = reviews(
        'com.nextbillion.groww',
        lang='en',
        country='in',
        sort=Sort.NEWEST,
        count=1000
    )
    
    df = pd.DataFrame(result)
    # Standardize columns
    df = df[['reviewId', 'at', 'score', 'content']]
    df.columns = ['id', 'date', 'rating', 'review_text']
    df['source'] = 'play_store'
    return df

def scrape_app_store():
    print("Scraping App Store reviews...")
    groww_app = AppStore(country='in', app_name='groww-stocks-mutual-fund-ipo', app_id='1404871703')
    groww_app.review(how_many=1000)
    
    df = pd.DataFrame(groww_app.reviews)
    if not df.empty:
        # Standardize columns
        # AppStore output format: date, review, rating, isEdited, title, userName
        df = df.rename(columns={'review': 'review_text'})
        # Generate dummy IDs for Apple since they don't provide a unique review ID
        df['id'] = [f"apple_{i}" for i in range(len(df))]
        df = df[['id', 'date', 'rating', 'review_text']]
        df['source'] = 'app_store'
        return df
    return pd.DataFrame(columns=['id', 'date', 'rating', 'review_text', 'source'])

def is_high_quality(text):
    text_lower = str(text).lower()
    
    # 1. Keywords that signal business value (bugs, pricing, features, frustration, operations)
    signal_keywords = {
        'bug', 'glitch', 'error', 'fail', 'stuck', 'crash', 'hang', 'issue', 'problem', 'slow',
        'charge', 'fee', 'brokerage', 'money', 'deduct', 'amount', 'loss', 'profit', 'tax', 'fund',
        'support', 'customer care', 'reply', 'response', 'solve', 'ticket', 'call',
        'feature', 'add', 'option', 'chart', 'ui', 'update', 'data', 'indicator', 'show',
        'login', 'kyc', 'account', 'withdraw', 'deposit', 'order', 'execution', 'portfolio', 'buy', 'sell', 'trade', 'share',
        'scam', 'fraud', 'worst', 'pathetic', 'disgusting', 'terrible', 'trust', 'fake', 'cheat'
    }
    
    # If it contains any signal keyword, we keep it.
    if any(kw in text_lower for kw in signal_keywords):
        return True
        
    # 2. Filter out generic praise that has no signal
    generic_praise = {
        'good', 'nice', 'best', 'great', 'excellent', 'awesome', 'love', 'super', 
        'easy', 'perfect', 'fine', 'helpful', 'amazing', 'smooth', 'mast', 'osm'
    }
    
    app_words = {
        'app', 'application', 'platform', 'experience', 'trading', 'investment', 'investing', 
        'groww', 'very', 'is', 'for', 'to', 'use', 'this', 'aap', 'and', 'the', 'it', 'my', 'i', 'am'
    }
    
    # Extract distinct words
    words = set(re.findall(r'\b\w+\b', text_lower))
    
    # Remove app words and generic praise words
    remaining_words = words - app_words - generic_praise
    
    # If there are barely any other descriptive words left, it's low-information praise/noise
    if len(remaining_words) < 3:
        return False
        
    return True

def process_pipeline(output_path):
    # 1. Scrape
    play_df = scrape_play_store()
    app_df = scrape_app_store()
    
    # Merge
    df = pd.concat([play_df, app_df], ignore_index=True)
    initial_count = len(df)
    print(f"Total reviews scraped: {initial_count}")
    
    if initial_count == 0:
        print("No reviews found. Exiting.")
        return
        
    # 2. Drop NaNs
    df = df.dropna(subset=['review_text'])
    
    # 3. PII Scrubbing
    print("Scrubbing PII...")
    df['review_text'] = df['review_text'].apply(clean_text)
    
    # 4. Deduplicate exact matches
    print("Deduplicating...")
    df = df.drop_duplicates(subset=['review_text'])
    
    # 5. Filter short reviews (< 4 words)
    print("Filtering short reviews...")
    df = df[df['review_text'].apply(lambda x: len(str(x).split()) >= 4)]
    
    # 6. Filter non-English reviews
    print("Filtering non-English reviews...")
    df = df[df['review_text'].apply(is_english)]

    # 7. Semantic Quality Filter (Drop generic praise, keep signal)
    print("Applying Semantic Quality Filter...")
    pre_semantic_count = len(df)
    df = df[df['review_text'].apply(is_high_quality)]
    post_semantic_count = len(df)
    print(f"Semantic Filter dropped {pre_semantic_count - post_semantic_count} low-information reviews.")
    
    final_count = len(df)
    
    print("\n--- Pipeline Complete ---")
    print(f"Original Count : {initial_count}")
    print(f"Final Count    : {final_count}")
    print(f"Removed        : {initial_count - final_count} noise/spam reviews.")
    
    df.to_csv(output_path, index=False)
    print(f"Cleaned dataset saved to {output_path}")

if __name__ == "__main__":
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'cleaned_reviews.csv')
    process_pipeline(output_file)
