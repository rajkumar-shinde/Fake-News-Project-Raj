import requests
from bs4 import BeautifulSoup

def extract_article_text(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Common article text containers
        # We try to get the title first
        title = soup.title.string if soup.title else ""
        
        # Get all paragraph text
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text() for p in paragraphs])
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return {
            "title": title,
            "text": text,
            "snippet": text[:500] + "..." if len(text) > 500 else text
        }
    except Exception as e:
        return {"error": str(e)}
