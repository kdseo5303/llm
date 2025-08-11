import re
from typing import Dict, List, Any, Tuple
from ..models.chat import KnowledgeDocument

class ResponseValidator:
    """Service for validating AI responses and preventing hallucinations."""
    
    def __init__(self):
        self.budget_keywords = [
            'budget', 'cost', 'price', 'expense', 'financial', 'money', 'dollar', 'euro',
            'funding', 'investment', 'costing', 'estimate', 'quotation', 'rate', 'fee'
        ]
        
        self.scheduling_keywords = [
            'schedule', 'timeline', 'deadline', 'duration', 'time', 'date', 'week',
            'month', 'day', 'hour', 'minute', 'milestone', 'phase', 'stage'
        ]
    
    def validate_response(self, response: str, context_sources: List[Dict[str, Any]], question: str) -> Dict[str, Any]:
        """
        Validate AI response against knowledge base context.
        
        Args:
            response: AI-generated response
            context_sources: Sources used to generate the response
            question: Original user question
            
        Returns:
            Validation results with confidence scores and warnings
        """
        validation_result = {
            'is_valid': True,
            'confidence_score': 0.0,
            'warnings': [],
            'source_coverage': 0.0,
            'unverified_claims': [],
            'recommendations': []
        }
        
        # Check if response cites sources
        source_citations = self._extract_source_citations(response)
        validation_result['source_coverage'] = len(source_citations) / max(len(context_sources), 1)
        
        # Validate source citations
        citation_validation = self._validate_citations(source_citations, context_sources)
        validation_result['warnings'].extend(citation_validation['warnings'])
        
        # Check for unverified claims
        unverified_claims = self._identify_unverified_claims(response, context_sources)
        validation_result['unverified_claims'] = unverified_claims
        
        # Special validation for budget/scheduling questions
        if self._is_budget_or_scheduling_question(question):
            budget_validation = self._validate_budget_scheduling_response(response, context_sources)
            validation_result['warnings'].extend(budget_validation['warnings'])
            validation_result['recommendations'].extend(budget_validation['recommendations'])
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(validation_result)
        validation_result['confidence_score'] = confidence_score
        
        # Determine if response is valid
        validation_result['is_valid'] = confidence_score >= 0.7 and len(validation_result['warnings']) < 3
        
        return validation_result
    
    def _extract_source_citations(self, response: str) -> List[str]:
        """Extract source citations from the response."""
        # Look for patterns like "According to [document]", "From [source]", etc.
        citation_patterns = [
            r'According to ([^,\.]+)',
            r'From ([^,\.]+)',
            r'Based on ([^,\.]+)',
            r'As stated in ([^,\.]+)',
            r'Per ([^,\.]+)',
            r'In ([^,\.]+)'
        ]
        
        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            citations.extend(matches)
        
        return [citation.strip() for citation in citations if citation.strip()]
    
    def _validate_citations(self, citations: List[str], context_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that citations match actual context sources."""
        result = {'warnings': []}
        
        if not citations:
            result['warnings'].append("Response contains no source citations")
            return result
        
        # Get actual source names from context
        actual_sources = [source.get('title', '') for source in context_sources]
        
        for citation in citations:
            # Check if citation matches any actual source
            citation_matched = False
            for actual_source in actual_sources:
                if citation.lower() in actual_source.lower() or actual_source.lower() in citation.lower():
                    citation_matched = True
                    break
            
            if not citation_matched:
                result['warnings'].append(f"Citation '{citation}' may not match actual sources")
        
        return result
    
    def _identify_unverified_claims(self, response: str, context_sources: List[Dict[str, Any]]) -> List[str]:
        """Identify claims that may not be supported by the context."""
        claims = []
        
        # Look for definitive statements that might need verification
        definitive_patterns = [
            r'The cost is (\$[\d,]+)',
            r'It takes (\d+ [a-z]+)',
            r'The budget is (\$[\d,]+)',
            r'(\d+) percent of',
            r'(\d+) days to complete',
            r'(\d+) weeks for'
        ]
        
        for pattern in definitive_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                claims.append(f"Specific figure: {match}")
        
        return claims
    
    def _is_budget_or_scheduling_question(self, question: str) -> bool:
        """Check if question is about budgeting or scheduling."""
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in self.budget_keywords + self.scheduling_keywords)
    
    def _validate_budget_scheduling_response(self, response: str, context_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extra validation for budget and scheduling responses."""
        result = {'warnings': [], 'recommendations': []}
        
        # Check for specific numbers without clear sources
        number_patterns = [
            r'\$[\d,]+',
            r'\d+ percent',
            r'\d+ days?',
            r'\d+ weeks?',
            r'\d+ months?'
        ]
        
        numbers_found = []
        for pattern in number_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            numbers_found.extend(matches)
        
        if numbers_found:
            # Check if these numbers are properly cited
            for number in numbers_found:
                if not self._is_number_properly_cited(response, number):
                    result['warnings'].append(f"Specific figure '{number}' may not be properly sourced")
        
        # Check for vague statements that might be assumptions
        vague_patterns = [
            r'typically costs',
            r'usually takes',
            r'generally requires',
            r'standard practice',
            r'industry average'
        ]
        
        for pattern in vague_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                result['warnings'].append("Response contains potentially unsourced generalizations")
                result['recommendations'].append("Consider adding specific source citations for generalizations")
        
        return result
    
    def _is_number_properly_cited(self, response: str, number: str) -> bool:
        """Check if a specific number is properly cited in the response."""
        # Look for the number near a citation
        number_index = response.find(number)
        if number_index == -1:
            return False
        
        # Check if there's a citation within 100 characters before or after the number
        start = max(0, number_index - 100)
        end = min(len(response), number_index + 100)
        surrounding_text = response[start:end]
        
        citation_indicators = ['according to', 'from', 'based on', 'per', 'in']
        return any(indicator in surrounding_text.lower() for indicator in citation_indicators)
    
    def _calculate_confidence_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate confidence score based on validation results."""
        base_score = 1.0
        
        # Deduct points for warnings
        warning_penalty = len(validation_result['warnings']) * 0.1
        base_score -= warning_penalty
        
        # Deduct points for unverified claims
        claim_penalty = len(validation_result['unverified_claims']) * 0.15
        base_score -= claim_penalty
        
        # Bonus for good source coverage
        if validation_result['source_coverage'] > 0.8:
            base_score += 0.1
        elif validation_result['source_coverage'] < 0.3:
            base_score -= 0.2
        
        return max(0.0, min(1.0, base_score))
    
    def generate_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """Generate a human-readable validation summary."""
        summary = f"Confidence Score: {validation_result['confidence_score']:.1%}\n"
        
        if validation_result['warnings']:
            summary += "\n⚠️ Warnings:\n"
            for warning in validation_result['warnings']:
                summary += f"• {warning}\n"
        
        if validation_result['unverified_claims']:
            summary += "\n❓ Unverified Claims:\n"
            for claim in validation_result['unverified_claims']:
                summary += f"• {claim}\n"
        
        if validation_result['recommendations']:
            summary += "\n💡 Recommendations:\n"
            for rec in validation_result['recommendations']:
                summary += f"• {rec}\n"
        
        return summary 