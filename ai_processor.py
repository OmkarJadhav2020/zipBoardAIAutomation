import config
import time
import os
import json
import re
from openai import OpenAI
from google.api_core import exceptions

class AIProcessor:
    def __init__(self):
        # Setup Groq (using the key user pasted in GROK_API_KEY)
        # Check both env vars just in case
        grok_key = os.getenv("GROK_API_KEY") or os.getenv("GROQ_API_KEY")
        
        self.client = None
        self.models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-safeguard-20b",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "meta-llama/llama-4-scout-17b-16e-instruct"
        ]
        self.model_index = 0
        
        if grok_key:
            try:
                self.client = OpenAI(
                    api_key=grok_key,
                    base_url="https://api.groq.com/openai/v1",
                )
                print(f"DEBUG: Groq AI configured. Primary model: {self.models[0]}")
            except Exception as e:
                print(f"Error configuring Groq: {e}")
        else:
             print("WARNING: GROK_API_KEY not found. AI will fail.")

    def _clean_json_text(self, text):
        """Extracts JSON from markdown code blocks or raw text."""
        # Check for markdown code block
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        # Check for plain code block
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        return text

    def _format_output(self, raw_json):
        """Parses JSON and returns formatted text for Excel."""
        try:
            data = json.loads(raw_json)
            
            # Format Gaps
            gaps = data.get("gap", [])
            if isinstance(gaps, list):
                gap_text = "\n".join([f"- {g}" for g in gaps])
            else:
                gap_text = str(gaps)
                
            # Format Suggestions
            suggestions = data.get("suggestions", [])
            if isinstance(suggestions, list):
                sugg_text = ""
                for s in suggestions:
                    topic = s.get("topic", "")
                    desc = s.get("description", "")
                    sugg_text += f"**{topic}**\n{desc}\n\n"
            else:
                sugg_text = str(suggestions)
                
            # Format Topics
            topics = data.get("topics_covered", "")
            if isinstance(topics, list):
                topics = ", ".join(topics)
                
            # Format Content Type
            c_type = data.get("content_type", "Unknown")
                
            return gap_text, sugg_text.strip(), topics, c_type
        except json.JSONDecodeError as e:
            # print(f"JSON Parse Error: {e}") # Optional: debug
            return f"Raw Output (Parse Error): {raw_json}", "Parse Error"
        except Exception as e:
            return f"Error formatting: {e}", "Error"

    def analyze_article(self, title, content):
        """
        Analyzes a single article using Groq.
        """
        if not self.client:
            return {"gap": "No AI Configured", "suggestions": ""}
        
        prompt = f"""
        You are a content strategist. Analyze the following help center article.
        
        Title: {title}
        Content Snippet: {content[:15000]}
        
        Identify:
        1. Gaps (missing information based on the title and context).
        2. Suggestions (related topics or articles that should be created).
        3. Topics Covered (comma-separated keywords).
        4. Content Type (One of: "How-to Guide", "FAQ", "Troubleshooting", "Reference", "Other").
        
        Return STRICT JSON format only:
        {{
          "gap": ["gap 1", "gap 2", ...],
          "suggestions": [
             {{"topic": "Topic Name", "description": "Why this is needed..."}},
             ...
          ],
          "topics_covered": "Topic 1, Topic 2, ...",
          "content_type": "Type"
        }}
        """

        try:
            current_model = self.models[self.model_index]
            # print(f"Analyzing: {title} using {current_model}...") # Debug
            
            completion = self.client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs strict JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            raw_response = completion.choices[0].message.content
                
            # Clean and parse
            json_text = self._clean_json_text(raw_response)
            gap_text, sugg_text, topics, c_type = self._format_output(json_text)
            
            return {
                "gap": gap_text,
                "suggestions": sugg_text,
                "topics": topics,
                "type": c_type
            }
            
        except Exception as e:
            error_msg = str(e)
            if "rate_limit_exceeded" in error_msg.lower():
                 print(f"Rate Limit Hit on {self.models[self.model_index]}: {error_msg}")
                 
                 # Switch to next model
                 old_index = self.model_index
                 self.model_index = (self.model_index + 1) % len(self.models)
                 
                 if self.model_index != 0:
                     print(f"Switching fallback model: {self.models[old_index]} -> {self.models[self.model_index]}")
                     # Immediate retry with new model
                     return self.analyze_article(title, content)
                 
                 # If we wrapped back to 0, we've exhausted all models. Now sleep.
                 print("All available models exhausted. Waiting for rate limits to reset...")
                 
                 # Try to extract wait time
                 wait_time = 60 # Default
                 import re
                 # Look for "try again in Xs" or "try again in XmYs"
                 # Example: "in 1m53.184s"
                 
                 # Regex for minutes/seconds
                 match = re.search(r'in (\d+)m(\d+\.?\d*)s', error_msg)
                 if match:
                     minutes = int(match.group(1))
                     seconds = float(match.group(2))
                     wait_time = (minutes * 60) + seconds + 5 # Add buffer
                     
                 else:
                     # Check for just seconds
                     match_s = re.search(r'in (\d+\.?\d*)s', error_msg)
                     if match_s:
                         wait_time = float(match_s.group(1)) + 5
               
                 print(f"Sleeping for {wait_time:.2f} seconds before restarting from primary model...")
                 time.sleep(wait_time)
                 
                 # Retry recursively (will start from model_index 0)
                 return self.analyze_article(title, content)
                 
            print(f"AI Failure: {e}")
            return {
                "gap": f"Error: {e}",
                "suggestions": "Error",
                "topics": "Error",
                "type": "Error"
            }
