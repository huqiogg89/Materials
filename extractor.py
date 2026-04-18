import re
import json
import urllib.request
import time

def parse_text_for_links(filepath):
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'^(\d+)\.\s.*?(?:URL:\s*|//\s*)(https?://[^\s()]+)'
    matches = re.finditer(pattern, content, re.MULTILINE)
    
    # Deduplicate just in case
    seen = set()
    for match in matches:
        source_id = int(match.group(1))
        url = match.group(2)
        if source_id not in seen:
            results.append({'id': source_id, 'url': url})
            seen.add(source_id)
        
    return results

def fetch_url(url):
    req = urllib.request.Request(
        url, 
        data=None, 
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            return {'status': 'success', 'html_len': len(html)}
    except Exception as e:
        return {'status': 'fail', 'error': str(e)}

if __name__ == "__main__":
    links = parse_text_for_links('Источники для таблицы.txt')
    print(f"Total links successfully extracted: {len(links)}")
    
    results = []
    for link in links:
        res = fetch_url(link['url'])
        link['fetch'] = res
        results.append(link)
        print(f"ID {link['id']:3} | {res['status']:7} | {link['url']}")
        time.sleep(0.5)
        
    with open('fetch_report.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Report saved.")
