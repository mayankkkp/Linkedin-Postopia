import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.8-flash')



def generate_post(topic):
    prompt = f"""
    Write a professional LinkedIn post about: {topic}.
    It should be engaging, insightful, and under 280 characters.
    Include 2-3 relevant hashtags.
    Do not use emojis. Do not include any introductory text, just the post content.
    """
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 15 * (attempt + 1)  # Wait 15, 30 seconds
                print(f"Quota limit hit, waiting {wait} seconds before retry...")
                time.sleep(wait)
            else:
                raise  # Non-429 errors are thrown directly
    raise Exception("Retries exhausted, Gemini still returns 429")

def publish_to_linkedin(text):
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    author_urn = os.getenv("LINKEDIN_PERSON_URN")
    
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print("✅ Successfully posted to LinkedIn!")
    else:
        print(f"❌ Failed to post. Status: {response.status_code}")
        print(response.text)

def main():
    print("🤖 LinkedIn Agent started.")
    topic = input("What topic should the post be about? ")
    
    print("\nGenerating post...")
    post_text = generate_post(topic)
    
    print("\n" + "="*40)
    print("DRAFT POST:")
    print(post_text)
    print("="*40)
    
    approval = input("\nPublish this? (yes/no): ").lower().strip()
    
    if approval == 'yes':
        publish_to_linkedin(post_text)
    else:
        print("Discarded. No post published.")

if __name__ == "__main__":
    main()