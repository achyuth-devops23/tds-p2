import anthropic
import os
import json
import base64
import requests
from io import BytesIO

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

def download_file(url):
    """Download file and return content"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

def ask_llm(quiz_text, page_html):
    """Use Claude to solve the quiz"""
    
    # Build the prompt
    prompt = f"""You are solving a data analysis quiz. Here is the question:

{quiz_text}

Instructions:
1. Carefully read the question
2. If there's a file to download, note the URL
3. Determine what calculation or analysis is needed
4. Return ONLY the final answer in the appropriate format (number, string, boolean, or JSON)

Think step by step, but your final response should be just the answer value.

For example:
- If asked for a sum, return just the number: 12345
- If asked for a name, return just the string: "John Doe"
- If asked for yes/no, return just: true or false
- If asked for multiple values, return a JSON object

Question: {quiz_text}

What is the answer?"""

    try:
        # Check if we need to download and process a file
        if 'download' in quiz_text.lower() or 'href=' in page_html:
            # Extract file URL from HTML
            import re
            url_match = re.search(r'href="([^"]+)"', page_html)
            if url_match:
                file_url = url_match.group(1)
                print(f"Found file URL: {file_url}")
                
                # Download the file
                file_content = download_file(file_url)
                if file_content:
                    prompt += f"\n\nFile downloaded successfully. Size: {len(file_content)} bytes"
                    
                    # If it's a PDF, we can pass it to Claude
                    if file_url.endswith('.pdf'):
                        # Convert to base64 for Claude
                        base64_content = base64.b64encode(file_content).decode('utf-8')
                        
                        # Use Claude with PDF support
                        response = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=4096,
                            messages=[{
                                "role": "user",
                                "content": [
                                    {
                                        "type": "document",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "application/pdf",
                                            "data": base64_content
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": prompt
                                    }
                                ]
                            }]
                        )
                        
                        answer_text = response.content[0].text.strip()
                        return parse_answer(answer_text)
        
        # Regular text-based question
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        answer_text = response.content[0].text.strip()
        return parse_answer(answer_text)
        
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None

def parse_answer(answer_text):
    """Parse the LLM's answer into the appropriate format"""
    answer_text = answer_text.strip()
    
    # Try to parse as JSON first
    try:
        return json.loads(answer_text)
    except:
        pass
    
    # Try to parse as number
    try:
        if '.' in answer_text:
            return float(answer_text)
        return int(answer_text)
    except:
        pass
    
    # Try to parse as boolean
    if answer_text.lower() in ['true', 'yes']:
        return True
    if answer_text.lower() in ['false', 'no']:
        return False
    
    # Return as string
    return answer_text
