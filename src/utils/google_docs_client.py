"""
Google Docs client for fetching and extracting text content from Google Documents.
"""

import os
import re
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

try:
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.exceptions import GoogleAuthError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class GoogleDocsClient:
    """Client for fetching content from Google Docs."""
    
    # Required scopes for reading Google Docs
    SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Docs client.
        
        Args:
            credentials_path: Path to Google API credentials JSON file
        """
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "Google API libraries not available. Install with: "
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
        
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.logger = logging.getLogger(__name__)
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google API."""
        if not self.credentials_path:
            raise ValueError(
                "Google credentials required. Set GOOGLE_APPLICATION_CREDENTIALS environment variable "
                "or provide credentials_path parameter"
            )
        
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
        
        try:
            creds = None
            token_path = 'token.json'
            
            # Load existing token if available
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            
            # If there are no valid credentials, request authorization
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            # Build the service
            self.service = build('docs', 'v1', credentials=creds)
            self.logger.info("Successfully authenticated with Google Docs API")
            
        except GoogleAuthError as e:
            raise RuntimeError(f"Google authentication failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Google Docs client: {e}")
    
    def extract_document_id(self, url: str) -> str:
        """
        Extract document ID from Google Docs URL.
        
        Args:
            url: Google Docs URL
            
        Returns:
            Document ID string
            
        Raises:
            ValueError: If URL is not a valid Google Docs URL
        """
        # Common Google Docs URL patterns
        patterns = [
            r'https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)',
            r'https://drive\.google\.com/file/d/([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Try parsing as query parameter
        try:
            parsed_url = urlparse(url)
            if 'docs.google.com' in parsed_url.netloc:
                # Extract from path
                path_parts = parsed_url.path.split('/')
                if 'd' in path_parts:
                    id_index = path_parts.index('d') + 1
                    if id_index < len(path_parts):
                        return path_parts[id_index]
            
            # Check query parameters
            query_params = parse_qs(parsed_url.query)
            if 'id' in query_params:
                return query_params['id'][0]
                
        except Exception:
            pass
        
        raise ValueError(f"Invalid Google Docs URL format: {url}")
    
    async def fetch_document_content(self, url: str) -> str:
        """
        Fetch text content from Google Docs.
        
        Args:
            url: Google Docs URL
            
        Returns:
            Plain text content of the document
            
        Raises:
            RuntimeError: If document cannot be fetched
        """
        try:
            document_id = self.extract_document_id(url)
            self.logger.info(f"Fetching document content for ID: {document_id}")
            
            # Fetch document
            document = self.service.documents().get(documentId=document_id).execute()
            
            # Extract text content
            content = self._extract_text_from_document(document)
            
            self.logger.info(f"Successfully fetched document content ({len(content)} characters)")
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to fetch document content: {e}")
            raise RuntimeError(f"Failed to fetch Google Doc content: {e}")
    
    def _extract_text_from_document(self, document: Dict[str, Any]) -> str:
        """
        Extract plain text from Google Docs API response.
        
        Args:
            document: Document data from Google Docs API
            
        Returns:
            Plain text content
        """
        content_parts = []
        
        try:
            body = document.get('body', {})
            content = body.get('content', [])
            
            for element in content:
                if 'paragraph' in element:
                    paragraph = element['paragraph']
                    paragraph_text = self._extract_paragraph_text(paragraph)
                    if paragraph_text.strip():
                        content_parts.append(paragraph_text)
                
                elif 'table' in element:
                    table = element['table']
                    table_text = self._extract_table_text(table)
                    if table_text.strip():
                        content_parts.append(table_text)
        
        except Exception as e:
            self.logger.error(f"Error extracting text from document: {e}")
            return "Error: Could not extract document content"
        
        return '\n\n'.join(content_parts)
    
    def _extract_paragraph_text(self, paragraph: Dict[str, Any]) -> str:
        """Extract text from a paragraph element."""
        text_parts = []
        
        elements = paragraph.get('elements', [])
        for element in elements:
            text_run = element.get('textRun', {})
            text_content = text_run.get('content', '')
            text_parts.append(text_content)
        
        return ''.join(text_parts)
    
    def _extract_table_text(self, table: Dict[str, Any]) -> str:
        """Extract text from a table element."""
        table_parts = []
        
        table_rows = table.get('tableRows', [])
        for row in table_rows:
            row_parts = []
            table_cells = row.get('tableCells', [])
            
            for cell in table_cells:
                cell_content = cell.get('content', [])
                cell_text = []
                
                for element in cell_content:
                    if 'paragraph' in element:
                        paragraph_text = self._extract_paragraph_text(element['paragraph'])
                        cell_text.append(paragraph_text)
                
                row_parts.append(' '.join(cell_text).strip())
            
            if any(part.strip() for part in row_parts):
                table_parts.append(' | '.join(row_parts))
        
        return '\n'.join(table_parts)
    
    def get_document_info(self, url: str) -> Dict[str, Any]:
        """
        Get metadata about a Google Doc.
        
        Args:
            url: Google Docs URL
            
        Returns:
            Document metadata dictionary
        """
        try:
            document_id = self.extract_document_id(url)
            document = self.service.documents().get(documentId=document_id).execute()
            
            return {
                'document_id': document_id,
                'title': document.get('title', 'Untitled'),
                'revision_id': document.get('revisionId', ''),
                'created_time': document.get('createdTime', ''),
                'modified_time': document.get('modifiedTime', ''),
                'authors': [author.get('displayName', 'Unknown') for author in document.get('authors', [])],
                'word_count': self._estimate_word_count(document),
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get document info: {e}")
            return {'error': str(e)}
    
    def _estimate_word_count(self, document: Dict[str, Any]) -> int:
        """Estimate word count from document structure."""
        try:
            content = self._extract_text_from_document(document)
            words = content.split()
            return len(words)
        except Exception:
            return 0


# Utility function for simple document fetching
async def fetch_google_doc_content(url: str, credentials_path: Optional[str] = None) -> str:
    """
    Simple utility function to fetch Google Doc content.
    
    Args:
        url: Google Docs URL
        credentials_path: Optional path to credentials file
        
    Returns:
        Document text content
    """
    client = GoogleDocsClient(credentials_path)
    return await client.fetch_document_content(url)