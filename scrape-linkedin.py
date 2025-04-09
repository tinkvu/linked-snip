# api/scrape-linkedin.py
from http.server import BaseHTTPRequestHandler
from bs4 import BeautifulSoup
import requests
import json
import re
import os
from urllib.parse import parse_qs

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            linkedin_url = data.get('url')
            
            if not linkedin_url or 'linkedin.com' not in linkedin_url:
                self._send_json_response({'error': 'Invalid LinkedIn URL'}, 400)
                return
            
            result = self._scrape_linkedin_comment(linkedin_url)
            self._send_json_response(result)
            
        except Exception as e:
            self._send_json_response({'error': str(e)}, 500)
    
    def do_GET(self):
        try:
            # Extract URL from query string for GET requests
            query_components = parse_qs(self.path.split('?')[1]) if '?' in self.path else {}
            linkedin_url = query_components.get('url', [''])[0]
            
            if not linkedin_url or 'linkedin.com' not in linkedin_url:
                self._send_json_response({'error': 'Invalid LinkedIn URL'}, 400)
                return
            
            result = self._scrape_linkedin_comment(linkedin_url)
            self._send_json_response(result)
            
        except Exception as e:
            self._send_json_response({'error': str(e)}, 500)
    
    def _scrape_linkedin_comment(self, url):
        """Scrape LinkedIn comment data from the provided URL"""
        
        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        # Add cookies if available (helps with authentication)
        cookies = {}
        linkedin_cookie = os.environ.get('LINKEDIN_COOKIE', '')
        if linkedin_cookie:
            cookie_parts = linkedin_cookie.split(';')
            for part in cookie_parts:
                if '=' in part:
                    name, value = part.strip().split('=', 1)
                    cookies[name] = value
        
        # Fetch the LinkedIn page
        response = requests.get(url, headers=headers, cookies=cookies)
        
        if response.status_code != 200:
            return {'error': f'Failed to fetch LinkedIn page, status code: {response.status_code}'}
        
        # Parse HTML with Beautiful Soup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Note: The actual selectors will depend on LinkedIn's current HTML structure
        # These are placeholders and would need to be updated based on inspection of LinkedIn's DOM
        try:
            # Find the comment container
            comment_container = soup.select_one('div.comments-comment-item')
            
            if not comment_container:
                # Try alternative selectors if needed
                comment_container = soup.select_one('article.comments-comment-item')
            
            if not comment_container:
                return {'error': 'Could not locate comment on the page'}
            
            # Extract user information
            name_element = comment_container.select_one('.comments-post-meta__name-text')
            title_element = comment_container.select_one('.comments-post-meta__headline')
            comment_element = comment_container.select_one('.comments-comment-item__main-content')
            profile_pic_element = comment_container.select_one('.comments-post-meta__actor-link img')
            
            # Extract image if present
            image_element = comment_container.select_one('.feed-shared-image__image')
            image_caption_element = comment_container.select_one('.feed-shared-image__description')
            
            # Build result object
            result = {
                'name': name_element.text.strip() if name_element else 'LinkedIn User',
                'title': title_element.text.strip() if title_element else '',
                'comment': comment_element.text.strip() if comment_element else 'No comment text found',
                'profilePicture': profile_pic_element.get('src') if profile_pic_element else '',
                'includeImage': bool(image_element),
                'commentImage': image_element.get('src') if image_element else '',
                'imageCaption': image_caption_element.text.strip() if image_caption_element else ''
            }
            
            return result
            
        except Exception as e:
            return {'error': f'Error parsing LinkedIn comment: {str(e)}'}
    
    def _send_json_response(self, data, status=200):
        """Helper method to send JSON response with proper headers"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
