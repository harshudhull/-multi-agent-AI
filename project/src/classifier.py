import os
from typing import Dict, Any, Tuple
import json

class ClassifierAgent:
    """Agent for classifying input format and intent"""
    
    def __init__(self):
        self.format_mappings = {
            '.pdf': 'PDF',
            '.json': 'JSON',
            '.txt': 'Email',
            '.eml': 'Email'
        }
        
        self.intent_keywords = {
            'Invoice': ['invoice', 'bill', 'payment', 'amount due', 'billing'],
            'RFQ': ['rfq', 'quote', 'quotation', 'pricing', 'request for quote'],
            'Complaint': ['complaint', 'issue', 'problem', 'dissatisfied', 'error'],
            'Regulation': ['regulation', 'compliance', 'policy', 'guideline', 'standard'],
            'Contract': ['contract', 'agreement', 'terms', 'conditions'],
            'Report': ['report', 'analysis', 'summary', 'findings']
        }
    
    def classify(self, file_path: str, input_type: str) -> Dict[str, Any]:
        """Classify input format and intent"""
        try:
            # Determine format
            file_extension = os.path.splitext(file_path)[1].lower()
            format_type = self.format_mappings.get(file_extension, 'Unknown')
            
            # Read file content for intent classification
            content = self._read_file_content(file_path)
            intent = self._classify_intent(content)
            
            # Determine urgency
            urgency = self._classify_urgency(content)
            
            classification = {
                'format': format_type,
                'intent': intent,
                'urgency': urgency,
                'confidence_score': self._calculate_confidence(content, intent),
                'file_size': os.path.getsize(file_path),
                'processing_notes': self._generate_processing_notes(format_type, intent)
            }
            
            return classification
            
        except Exception as e:
            return {
                'format': 'Unknown', 
                'intent': 'Unknown', 
                'urgency': 'Low',
                'error': f"Classification error: {str(e)}"
            }
    
    def _read_file_content(self, file_path: str) -> str:
        """Read file content based on file type"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.json':
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    return json.dumps(data, indent=2)
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    return file.read()
                    
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def _classify_intent(self, content: str) -> str:
        """Classify the intent of the content"""
        content_lower = content.lower()
        
        intent_scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        else:
            return 'General'
    
    def _classify_urgency(self, content: str) -> str:
        """Classify urgency level"""
        content_lower = content.lower()
        
        high_urgency_keywords = ['urgent', 'asap', 'immediate', 'emergency', 'critical']
        medium_urgency_keywords = ['soon', 'priority', 'important', 'timely']
        
        if any(keyword in content_lower for keyword in high_urgency_keywords):
            return 'High'
        elif any(keyword in content_lower for keyword in medium_urgency_keywords):
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_confidence(self, content: str, intent: str) -> float:
        """Calculate confidence score for classification"""
        if intent == 'General':
            return 0.3
        
        content_lower = content.lower()
        keywords = self.intent_keywords.get(intent, [])
        
        if not keywords:
            return 0.5
        
        matches = sum(1 for keyword in keywords if keyword in content_lower)
        confidence = min(matches / len(keywords) + 0.3, 1.0)
        
        return round(confidence, 2)
    
    def _generate_processing_notes(self, format_type: str, intent: str) -> str:
        """Generate processing notes based on classification"""
        notes = []
        
        if format_type == 'PDF':
            notes.append("PDF document detected - text extraction required")
        elif format_type == 'JSON':
            notes.append("JSON data detected - structure validation recommended")
        elif format_type == 'Email':
            notes.append("Email content detected - sender and metadata extraction needed")
        
        if intent == 'Invoice':
            notes.append("Invoice processing - extract amounts and dates")
        elif intent == 'RFQ':
            notes.append("RFQ processing - identify requirements and pricing requests")
        elif intent == 'Complaint':
            notes.append("Complaint processing - prioritize for customer service")
        
        return "; ".join(notes)