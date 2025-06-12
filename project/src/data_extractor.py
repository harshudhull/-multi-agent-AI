import json
import PyPDF2
import re
from typing import Dict, Any, List
from email.parser import Parser
from email.policy import default
import os

class DataExtractor:
    """Service for extracting data from different file formats"""
    
    def __init__(self):
        self.supported_formats = ["pdf", "json", "txt", "eml"]
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract data from uploaded file based on file extension"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == ".pdf":
                return self._extract_from_pdf(file_path)
            elif file_extension == ".json":
                return self._extract_from_json_file(file_path)
            elif file_extension in [".txt", ".eml"]:
                return self._extract_from_text_file(file_path)
            else:
                return {"error": f"Unsupported file format: {file_extension}"}
                
        except Exception as e:
            return {"error": f"Error extracting from file: {str(e)}"}
    
    def extract_from_email(self, file_path: str) -> Dict[str, Any]:
        """Extract data from email file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            # Try to parse as email
            try:
                msg = Parser(policy=default).parsestr(content)
                return {
                    "type": "email",
                    "sender": msg.get('From', 'Unknown'),
                    "subject": msg.get('Subject', 'No Subject'),
                    "date": msg.get('Date', 'Unknown'),
                    "to": msg.get('To', 'Unknown'),
                    "body": self._extract_email_body(msg),
                    "intent": self._classify_email_intent(msg.get('Subject', '') + ' ' + str(msg.get_payload())),
                    "urgency": self._detect_urgency(content),
                    "extracted_fields": self._extract_email_fields(content)
                }
            except:
                # Fallback to text parsing
                return {
                    "type": "email_text",
                    "content": content,
                    "sender": self._extract_sender_from_text(content),
                    "intent": self._classify_email_intent(content),
                    "urgency": self._detect_urgency(content),
                    "extracted_fields": self._extract_email_fields(content)
                }
                
        except Exception as e:
            return {"error": f"Error extracting from email: {str(e)}"}
    
    def extract_from_json(self, file_path: str) -> Dict[str, Any]:
        """Extract and reformat JSON data"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Convert to FlowBit schema format
            formatted_data = self._format_to_flowbit_schema(data)
            
            return {
                "type": "json",
                "original_data": data,
                "formatted_data": formatted_data,
                "anomalies": self._detect_json_anomalies(data),
                "missing_fields": self._detect_missing_fields(data),
                "data_quality_score": self._calculate_data_quality(data)
            }
            
        except Exception as e:
            return {"error": f"Error extracting from JSON: {str(e)}"}
    
    def _extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text and data from PDF"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            return {
                "type": "pdf",
                "text_content": text,
                "page_count": len(pdf_reader.pages),
                "extracted_fields": self._extract_pdf_fields(text),
                "document_type": self._classify_pdf_type(text)
            }
            
        except Exception as e:
            return {"error": f"Error extracting from PDF: {str(e)}"}
    
    def _extract_from_json_file(self, file_path: str) -> Dict[str, Any]:
        """Extract data from JSON file"""
        return self.extract_from_json(file_path)
    
    def _extract_from_text_file(self, file_path: str) -> Dict[str, Any]:
        """Extract data from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            
            return {
                "type": "text",
                "content": content,
                "word_count": len(content.split()),
                "extracted_fields": self._extract_text_fields(content),
                "sentiment": self._analyze_sentiment(content)
            }
            
        except Exception as e:
            return {"error": f"Error extracting from text file: {str(e)}"}
    
    def _extract_email_body(self, msg) -> str:
        """Extract body from email message"""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        return part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                return str(msg.get_payload(decode=True).decode('utf-8', errors='ignore'))
        except:
            return str(msg.get_payload())
    
    def _extract_sender_from_text(self, content: str) -> str:
        """Extract sender from text content"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        return emails[0] if emails else "Unknown"
    
    def _classify_email_intent(self, content: str) -> str:
        """Classify email intent"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['rfq', 'quote', 'quotation', 'pricing']):
            return "RFQ"
        elif any(word in content_lower for word in ['complaint', 'issue', 'problem', 'dissatisfied']):
            return "Complaint"
        elif any(word in content_lower for word in ['invoice', 'bill', 'payment', 'amount due']):
            return "Invoice"
        elif any(word in content_lower for word in ['regulation', 'compliance', 'policy']):
            return "Regulation"
        else:
            return "General"
    
    def _detect_urgency(self, content: str) -> str:
        """Detect urgency level"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['urgent', 'asap', 'immediate', 'emergency']):
            return "High"
        elif any(word in content_lower for word in ['soon', 'priority', 'important']):
            return "Medium"
        else:
            return "Low"
    
    def _extract_email_fields(self, content: str) -> Dict[str, Any]:
        """Extract structured fields from email content"""
        fields = {}
        
        # Extract phone numbers
        phone_pattern = r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s?\d{3}-\d{4}\b'
        phones = re.findall(phone_pattern, content)
        if phones:
            fields['phone_numbers'] = phones
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        if emails:
            fields['email_addresses'] = emails
        
        # Extract amounts/prices
        amount_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?'
        amounts = re.findall(amount_pattern, content)
        if amounts:
            fields['amounts'] = amounts
        
        return fields
    
    def _extract_pdf_fields(self, text: str) -> Dict[str, Any]:
        """Extract structured fields from PDF text"""
        fields = {}
        
        # Extract dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        dates = re.findall(date_pattern, text)
        if dates:
            fields['dates'] = dates
        
        # Extract amounts
        amount_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?'
        amounts = re.findall(amount_pattern, text)
        if amounts:
            fields['amounts'] = amounts
        
        return fields
    
    def _classify_pdf_type(self, text: str) -> str:
        """Classify PDF document type"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['invoice', 'bill', 'amount due']):
            return "Invoice"
        elif any(word in text_lower for word in ['contract', 'agreement', 'terms']):
            return "Contract"
        elif any(word in text_lower for word in ['report', 'analysis', 'summary']):
            return "Report"
        else:
            return "Document"
    
    def _extract_text_fields(self, content: str) -> Dict[str, Any]:
        """Extract fields from plain text"""
        return self._extract_email_fields(content)  # Reuse email field extraction
    
    def _analyze_sentiment(self, content: str) -> str:
        """Simple sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'satisfied', 'happy', 'pleased']
        negative_words = ['bad', 'terrible', 'awful', 'dissatisfied', 'angry', 'frustrated']
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return "Positive"
        elif negative_count > positive_count:
            return "Negative"
        else:
            return "Neutral"
    
    def _format_to_flowbit_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format data to FlowBit schema"""
        return {
            "id": data.get("id", "unknown"),
            "timestamp": data.get("timestamp", "unknown"),
            "type": data.get("type", "unknown"),
            "data": data,
            "processed_at": "2025-01-22T10:00:00Z"
        }
    def _detect_json_anomalies(self, data: Dict[str, Any]) -> list[str]:

        """Detect anomalies in JSON data"""
        anomalies = []
        
        # Check for null values
        if self._has_null_values(data):
            anomalies.append("Contains null values")
        
        # Check for empty strings
        if self._has_empty_strings(data):
            anomalies.append("Contains empty strings")
        
        return anomalies
    
    def _detect_missing_fields(self, data: Dict[str, Any]) -> List[str]:
        """Detect missing required fields"""
        required_fields = ["id", "timestamp", "type"]
        missing = []
        
        for field in required_fields:
            if field not in data:
                missing.append(field)
        
        return missing
    
    def _calculate_data_quality(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score"""
        total_fields = len(data)
        if total_fields == 0:
            return 0.0
        
        quality_score = 0.0
        
        # Check completeness
        non_empty_fields = sum(1 for v in data.values() if v is not None and v != "")
        quality_score += (non_empty_fields / total_fields) * 0.5
        
        # Check for required fields
        required_fields = ["id", "timestamp", "type"]
        present_required = sum(1 for field in required_fields if field in data)
        quality_score += (present_required / len(required_fields)) * 0.3
        
        # Check data types
        quality_score += 0.2  # Base score for valid JSON
        
        return min(quality_score, 1.0)
    
    def _has_null_values(self, data: Dict[str, Any]) -> bool:
        """Check if data has null values"""
        def check_null(obj):
            if isinstance(obj, dict):
                return any(v is None or check_null(v) for v in obj.values())
            elif isinstance(obj, list):
                return any(v is None or check_null(v) for v in obj)
            return obj is None
        
        return check_null(data)
    
    def _has_empty_strings(self, data: Dict[str, Any]) -> bool:
        """Check if data has empty string values"""
        def check_empty(obj):
            if isinstance(obj, dict):
                return any(v == "" or check_empty(v) for v in obj.values())
            elif isinstance(obj, list):
                return any(v == "" or check_empty(v) for v in obj)
            return obj == ""
        
        return check_empty(data)