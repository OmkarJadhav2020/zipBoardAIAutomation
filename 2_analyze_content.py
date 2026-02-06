import database
import ai_processor
import time
import sys
from sqlalchemy import or_

def analyze_data():
    print("Step 2: AI Analysis (Groq)")
    
    # 1. Initialize DB & AI
    Session = database.init_db()
    session = Session()
    
    ai = ai_processor.AIProcessor()
    
    # 2. Fetch Pending Articles
    # Pending = gap_analysis is NULL or gap_analysis starts with "Error" (retry errors)
    articles = session.query(database.Article).filter(
        or_(database.Article.gap_analysis == None, database.Article.gap_analysis.like("Error%"))
    ).all()
    
    total = len(articles)
    print(f"Found {total} articles needing analysis.")
    
    if total == 0:
        print("Nothing to analyze.")
        return

    # 3. Process Loop
    for i, art in enumerate(articles):
        print(f"[{i+1}/{total}] Analyzing: {art.title}...", end="", flush=True)
        
        start_t = time.time()
        
        try:
            # Call AI
            result = ai.analyze_article(art.title, art.content_text)
            
            # Update DB
            art.gap_analysis = result['gap']
            art.suggested_topics = result['suggestions'] # "Suggestions" column
            art.topics_covered = result['topics']
            art.content_type = result['type']
            
            session.commit() # SAVE IMMEDIATELY
            
            elapsed = time.time() - start_t
            if "Error" in result['gap']:
                 print(f" FAILED ({elapsed:.2f}s) - {result['gap']}")
            else:
                 print(f" DONE ({elapsed:.2f}s)")
                 
            # Rate limit is handled inside ai_processor or here?
            # AIProcessor has no internal rate limit loop for single client, 
            # we should add small sleep here just in case Groq 30RPM
            # 60s / 30 = 2s
            time.sleep(1)
            
        except Exception as e:
            print(f" EXCEPTION: {e}")
            session.rollback()

    print("\nAnalysis Complete.")

if __name__ == "__main__":
    analyze_data()
