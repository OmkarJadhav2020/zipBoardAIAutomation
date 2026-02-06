import database
import scraper
import config
import time
from datetime import datetime

def collect_data():
    print("Step 1: Help Article Cataloging (Scraping)")
    
    Session = database.init_db()
    session = Session()
    
    s = scraper.Scraper()
    
    # 1. Get Categories
    print("Fetching categories...")
    categories = s.get_categories()
    print(f"Found {len(categories)} categories.")
    
    for cat_data in categories:
        # Save or update category in DB
        cat = session.query(database.Category).filter_by(url=cat_data['url']).first()
        if not cat:
            cat = database.Category(
                name=cat_data['name'],
                url=cat_data['url'],
                article_count=cat_data['count']
            )
            session.add(cat)
            session.commit()
            print(f"Added Category: {cat.name}")
        else:
            cat.article_count = cat_data['count']
            session.commit()
            
        # 2. Get Articles for this category
        print(f"  Fetching articles for: {cat.name}...")
        articles = s.get_articles_from_category(cat.url)
        print(f"  Found {len(articles)} articles.")
        
        for art_data in articles:
            # Check if article already exists
            art = session.query(database.Article).filter_by(url=art_data['url']).first()
            
            if art:
                # print(f"    Skipping (exists): {art.title}")
                continue
                
            print(f"    New Article: {art_data['title']}")
            
            # Get full content and metadata
            content, word_count, has_screenshots = s.get_article_content(art_data['url'])
            custom_id = s.extract_id_from_url(art_data['url'])
            
            new_art = database.Article(
                title=art_data['title'],
                url=art_data['url'],
                category_id=cat.id,
                content_text=content,
                word_count=word_count,
                has_screenshots=has_screenshots,
                article_custom_id=custom_id,
                last_updated=datetime.utcnow()
            )
            session.add(new_art)
            session.commit()
            
            # Small delay to be polite
            time.sleep(0.5)

    print("\nData Collection Complete.")
    session.close()

if __name__ == "__main__":
    collect_data()
