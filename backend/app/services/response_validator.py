import re
from typing import Dict, List, Any, Tuple
from ..models.chat import KnowledgeDocument
import time

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
        
        # Cache for validation results to avoid re-computing
        self._validation_cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def validate_response(self, response: str, context_sources: List[Dict[str, Any]], question: str, fast_mode: bool = False) -> Dict[str, Any]:
        """
        Validate AI response against knowledge base context.
        
        Args:
            response: AI-generated response
            context_sources: Sources used to generate the response
            question: Original user question
            fast_mode: If True, skip expensive validation operations
            
        Returns:
            Validation results with confidence scores and warnings
        """
        print(f"🔍 ResponseValidator.validate_response called (fast_mode: {fast_mode})")
        print(f"🔍 Response length: {len(response)}")
        print(f"🔍 Context sources count: {len(context_sources)}")
        print(f"🔍 Question: {question}")
        
        # Check cache first
        cache_key = f"{hash(response)}:{hash(str(context_sources))}:{hash(question)}"
        if cache_key in self._validation_cache:
            cached_result = self._validation_cache[cache_key]
            if time.time() - cached_result.get('_timestamp', 0) < self._cache_ttl:
                print(f"✅ Using cached validation result")
                return {k: v for k, v in cached_result.items() if not k.startswith('_')}
        
        validation_result = {
            'is_valid': True,
            'confidence_score': 0.0,
            'warnings': [],
            'source_coverage': 0.0,
            'unverified_claims': [],
            'recommendations': [],
            'source_types': {'local': 0, 'web': 0}
        }
        
        try:
            # Quick source type counting (always fast)
            print(f"🔍 Counting source types...")
            for source in context_sources:
                if source.get('source_type') == 'web_search':
                    validation_result['source_types']['web'] += 1
                else:
                    validation_result['source_types']['local'] += 1
            print(f"🔍 Source types: {validation_result['source_types']}")
            
            # Fast citation extraction (always fast)
            print(f"🔍 Extracting source citations...")
            source_citations = self._extract_source_citations(response)
            print(f"🔍 Found {len(source_citations)} source citations: {source_citations}")
            validation_result['source_coverage'] = len(source_citations) / max(len(context_sources), 1)
            
            if fast_mode:
                # Fast mode: skip expensive operations, use heuristics
                print(f"🔍 Fast mode: using heuristic validation")
                validation_result = self._fast_validation(response, context_sources, source_citations, validation_result)
            else:
                # Full validation mode
                print(f"🔍 Full validation mode: performing comprehensive checks")
                
                # Validate source citations
                print(f"🔍 Validating citations...")
                citation_validation = self._validate_citations(source_citations, context_sources)
                validation_result['warnings'].extend(citation_validation['warnings'])
                print(f"🔍 Citation validation warnings: {citation_validation['warnings']}")
                
                # Check for unverified claims
                print(f"🔍 Identifying unverified claims...")
                unverified_claims = self._identify_unverified_claims(response, context_sources)
                validation_result['unverified_claims'] = unverified_claims
                print(f"🔍 Unverified claims: {unverified_claims}")
                
                # Special validation for budget/scheduling questions
                if self._is_budget_or_scheduling_question(question):
                    print(f"🔍 Performing budget/scheduling validation...")
                    budget_validation = self._validate_budget_scheduling_response(response, context_sources)
                    validation_result['warnings'].extend(budget_validation['warnings'])
                    validation_result['recommendations'].extend(budget_validation['recommendations'])
                    print(f"🔍 Budget validation warnings: {budget_validation['warnings']}")
            
            # Calculate confidence score
            print(f"🔍 Calculating confidence score...")
            confidence_score = self._calculate_confidence_score(validation_result)
            validation_result['confidence_score'] = confidence_score
            print(f"🔍 Confidence score: {confidence_score}")
            
            # Determine if response is valid
            validation_result['is_valid'] = confidence_score >= 0.7 and len(validation_result['warnings']) < 3
            print(f"🔍 Response is valid: {validation_result['is_valid']}")
            
            # Cache the result
            validation_result['_timestamp'] = time.time()
            self._validation_cache[cache_key] = validation_result
            
            return validation_result
            
        except Exception as e:
            print(f"❌ Error in validate_response: {str(e)}")
            import traceback
            print(f"❌ Validation error traceback: {traceback.format_exc()}")
            # Return a safe default validation result
            return {
                'is_valid': False,
                'confidence_score': 0.5,
                'warnings': [f"Validation error: {str(e)}"],
                'source_coverage': 0.0,
                'unverified_claims': [],
                'recommendations': [],
                'source_types': {'local': 0, 'web': 0}
            }
    
    def _fast_validation(self, response: str, context_sources: List[Dict[str, Any]], source_citations: List[str], base_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fast validation using heuristics instead of expensive operations."""
        result = base_result.copy()
        
        # Quick heuristic: if response has citations and sources, it's probably good
        if source_citations and len(source_citations) >= len(context_sources) * 0.5:
            result['warnings'].append("📝 Fast validation: Response appears well-sourced based on citation count.")
        elif not source_citations:
            result['warnings'].append("⚠️ Fast validation: Response lacks source citations.")
        
        # Quick source coverage check
        if result['source_coverage'] > 0.8:
            result['warnings'].append("✅ Fast validation: Excellent source coverage detected.")
        elif result['source_coverage'] < 0.3:
            result['warnings'].append("⚠️ Fast validation: Low source coverage detected.")
        
        return result
    
    def _extract_source_citations(self, response: str) -> List[str]:
        """Extract source citations from the response."""
        # Look for patterns like "According to [document]", "From [source]", etc.
        citation_patterns = [
            r'According to ([^,\.]+)',
            r'From ([^,\.]+)',
            r'Based on ([^,\.]+)',
            r'As stated in ([^,\.]+)',
            r'Per ([^,\.]+)',
            r'In ([^,\.]+)',
            r'According to the ([^,\.]+)',
            r'From the ([^,\.]+)',
            r'Based on the ([^,\.]+)'
        ]
        
        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            citations.extend(matches)
        
        # Filter out very short or generic citations
        filtered_citations = []
        for citation in citations:
            citation = citation.strip()
            # Only include citations that are substantial and not generic
            if (len(citation) > 5 and 
                citation.lower() not in ['script', 'budget', 'schedule', 'film', 'movie', 'production'] and
                not citation.isdigit()):
                filtered_citations.append(citation)
        
        print(f"🔍 Raw citations found: {citations}")
        print(f"🔍 Filtered citations: {filtered_citations}")
        
        return filtered_citations
    
    def _validate_citations(self, citations: List[str], context_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that citations match actual context sources."""
        result = {'warnings': []}
        
        if not citations:
            result['warnings'].append("⚠️ This response doesn't cite specific sources. While the information may be accurate, it's better when sources are clearly referenced.")
            return result
        
        # Get actual source names from context
        actual_sources = [source.get('title', '') for source in context_sources]
        print(f"🔍 Actual sources: {actual_sources}")
        print(f"🔍 Citations to validate: {citations}")
        
        unmatched_citations = []
        
        for citation in citations:
            # Check if citation matches any actual source
            citation_matched = False
            
            # Clean up the citation for better matching
            clean_citation = citation.strip().lower()
            
            for actual_source in actual_sources:
                clean_source = actual_source.lower()
                
                # More flexible matching - check if key words match
                citation_words = [word for word in clean_citation.split() if len(word) > 3]
                source_words = [word for word in clean_source.split() if len(word) > 3]
                
                # Check for word overlap
                word_overlap = any(word in clean_source for word in citation_words)
                source_in_citation = any(word in clean_citation for word in source_words)
                
                # Check for substring matches
                substring_match = (clean_citation in clean_source or 
                                clean_source in clean_citation or
                                word_overlap or source_in_citation)
                
                if substring_match:
                    citation_matched = True
                    print(f"✅ Citation '{citation}' matched source '{actual_source}'")
                    break
            
            if not citation_matched:
                # Only warn for citations that are clearly wrong
                if len(citation) > 10:  # Only warn for substantial citations
                    unmatched_citations.append(citation)
                    print(f"⚠️ Citation '{citation}' did not match any sources")
        
        # Create user-friendly warnings
        if unmatched_citations:
            if len(unmatched_citations) == 1:
                result['warnings'].append(f"📝 The response mentions information from '{unmatched_citations[0]}' but I couldn't find this exact source in my search results. This might be general knowledge or from a different source.")
            elif len(unmatched_citations) <= 3:
                result['warnings'].append(f"📝 The response references {len(unmatched_citations)} sources that don't exactly match my search results. This is common and usually means the information is accurate but phrased differently.")
            else:
                result['warnings'].append(f"📝 The response references several sources that don't exactly match my search results. This often happens when information is paraphrased or comes from general knowledge.")
        
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
            uncited_numbers = []
            for number in numbers_found:
                if not self._is_number_properly_cited(response, number):
                    uncited_numbers.append(number)
            
            if uncited_numbers:
                if len(uncited_numbers) == 1:
                    result['warnings'].append(f"💰 The response mentions a specific figure ({uncited_numbers[0]}) without clearly citing its source. For budgeting questions, it's important to know where numbers come from.")
                else:
                    result['warnings'].append(f"💰 The response mentions {len(uncited_numbers)} specific figures without clear sources. For accurate budgeting information, sources should be clearly referenced.")
        
        # Check for vague statements that might be assumptions
        vague_patterns = [
            r'typically costs',
            r'usually takes',
            r'generally requires',
            r'standard practice',
            r'industry average'
        ]
        
        vague_statements = []
        for pattern in vague_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                vague_statements.append(pattern)
        
        if vague_statements:
            result['warnings'].append("🤔 The response includes some general statements about industry practices. While these are often accurate, specific examples or sources would make the information more reliable.")
            result['recommendations'].append("💡 Consider adding specific examples or source citations for general statements about industry practices.")
        
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
        
        # Deduct points for warnings (less punitive)
        warning_penalty = len(validation_result['warnings']) * 0.05  # Reduced from 0.1
        base_score -= warning_penalty
        
        # Deduct points for unverified claims
        claim_penalty = len(validation_result['unverified_claims']) * 0.1  # Reduced from 0.15
        base_score -= claim_penalty
        
        # Bonus for good source coverage
        if validation_result['source_coverage'] > 0.8:
            base_score += 0.15  # Increased bonus
        elif validation_result['source_coverage'] > 0.5:
            base_score += 0.1   # Medium bonus
        elif validation_result['source_coverage'] < 0.3:
            base_score -= 0.1   # Reduced penalty
        
        # Bonus for having web sources (current information)
        web_sources = validation_result['source_types'].get('web', 0)
        if web_sources > 0:
            base_score += 0.1
        
        final_score = max(0.0, min(1.0, base_score))
        print(f"🔍 Confidence calculation: base={base_score:.3f}, warnings={len(validation_result['warnings'])}, claims={len(validation_result['unverified_claims'])}, coverage={validation_result['source_coverage']:.3f}, web_sources={web_sources}")
        print(f"🔍 Final confidence score: {final_score:.3f}")
        
        return final_score
    
    def generate_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """Generate a human-readable validation summary."""
        print(f"🔍 generate_validation_summary called")
        print(f"🔍 Validation result keys: {list(validation_result.keys())}")
        
        try:
            confidence_score = validation_result['confidence_score']
            
            # Create a user-friendly confidence description
            if confidence_score >= 0.9:
                confidence_desc = "🎯 Very High Confidence"
                confidence_explanation = "This response is highly reliable with excellent source coverage and minimal concerns."
            elif confidence_score >= 0.8:
                confidence_desc = "✅ High Confidence"
                confidence_explanation = "This response is reliable with good source coverage and few concerns."
            elif confidence_score >= 0.7:
                confidence_desc = "⚠️ Medium Confidence"
                confidence_explanation = "This response is generally reliable but has some areas that could use more specific sourcing."
            elif confidence_score >= 0.6:
                confidence_desc = "⚠️ Lower Confidence"
                confidence_explanation = "This response has some reliability concerns and would benefit from additional source verification."
            else:
                confidence_desc = "❌ Low Confidence"
                confidence_explanation = "This response has significant reliability concerns and should be verified with additional sources."
            
            summary = f"## 📊 Response Quality Assessment\n\n"
            summary += f"**{confidence_desc}** ({confidence_score:.1%})\n\n"
            summary += f"{confidence_explanation}\n\n"
            
            # Show source type breakdown
            if 'source_types' in validation_result:
                local_count = validation_result['source_types'].get('local', 0)
                web_count = validation_result['source_types'].get('web', 0)
                summary += f"**📚 Sources Used:** {local_count} from knowledge base, {web_count} from current web search\n\n"
            
            if validation_result['warnings']:
                summary += f"**⚠️ Areas for Improvement:**\n"
                for warning in validation_result['warnings']:
                    summary += f"• {warning}\n"
                summary += "\n"
            
            if validation_result['unverified_claims']:
                summary += f"**❓ Claims Needing Verification:**\n"
                for claim in validation_result['unverified_claims']:
                    summary += f"• {claim}\n"
                summary += "\n"
            
            if validation_result['recommendations']:
                summary += f"**💡 Recommendations:**\n"
                for rec in validation_result['recommendations']:
                    summary += f"• {rec}\n"
                summary += "\n"
            
            # Add a helpful note
            summary += f"**💭 Note:** This assessment helps you understand how reliable the information is. Higher confidence means better source coverage and fewer concerns."
            
            print(f"✅ Validation summary generated successfully")
            print(f"🔍 Summary length: {len(summary)} characters")
            print(f"🔍 Summary preview: {summary[:200]}...")
            
            return summary
            
        except Exception as e:
            print(f"❌ Error generating validation summary: {str(e)}")
            import traceback
            print(f"❌ Validation summary error traceback: {traceback.format_exc()}")
            # Return a safe fallback summary
            return f"## 📊 Response Quality Assessment\n\n**Confidence:** {validation_result.get('confidence_score', 0.5):.1%}\n\n*Note: Unable to generate detailed assessment due to an error.*" 

    def extract_citations_from_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Extract citations and source links from GPT's response.
        
        Args:
            response: GPT-generated response text
            
        Returns:
            List of extracted citations with metadata
        """
        print(f"🔍 Extracting citations from response...")
        citations = []
        
        # Look for URL patterns
        url_pattern = r'https?://[^\s\)]+'
        urls = re.findall(url_pattern, response)
        
        # Look for citation patterns
        citation_patterns = [
            r'According to ([^,\.]+)',
            r'Per ([^,\.]+)',
            r'As stated in ([^,\.]+)',
            r'Based on ([^,\.]+)',
            r'Source: ([^,\.]+)',
            r'From ([^,\.]+)'
        ]
        
        cited_sources = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            cited_sources.extend(matches)
        
        # Process URLs found
        for url in urls:
            try:
                # Try to extract title from URL
                domain = url.split('//')[1].split('/')[0] if '//' in url else url
                title = domain.replace('www.', '').replace('.com', '').replace('.org', '').replace('.edu', '')
                title = ' '.join(word.capitalize() for word in title.split('.'))
                
                citations.append({
                    'title': title,
                    'url': url,
                    'source_type': 'web_citation',
                    'relevance_score': 0.9,
                    'extracted_from': 'gpt_response'
                })
                print(f"✅ Extracted URL citation: {title} - {url}")
            except Exception as e:
                print(f"❌ Error processing URL {url}: {str(e)}")
        
        # Process cited sources without URLs
        for source in cited_sources:
            if source.strip() and len(source.strip()) > 3:
                citations.append({
                    'title': source.strip(),
                    'url': '',
                    'source_type': 'cited_source',
                    'relevance_score': 0.8,
                    'extracted_from': 'gpt_response'
                })
                print(f"✅ Extracted source citation: {source.strip()}")
        
        # Remove duplicates
        unique_citations = []
        seen_titles = set()
        for citation in citations:
            if citation['title'] not in seen_titles:
                unique_citations.append(citation)
                seen_titles.add(citation['title'])
        
        print(f"✅ Extracted {len(unique_citations)} unique citations from response")
        return unique_citations 