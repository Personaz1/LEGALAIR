"""
Legal ASI - Document Structure Preprocessing
Splits legal documents into logical sections for better analysis
"""

import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DocumentSectionParser:
    """Parser for splitting legal documents into logical sections"""
    
    def __init__(self):
        self.header_markers = [
            r'ВЕКСЕЛЬ\s*№?\s*\d*',
            r'ПОСТАНОВЛЕНИЕ\s+об?\s+административном',
            r'ПРОТОКОЛ\s+заседания',
            r'ДОГОВОР\s+№?\s*\d*',
            r'СПРАВКА\s+№?\s*\d*'
        ]
        
        self.footer_markers = [
            r'подпись[и]?\s*[:\-]?',
            r'__{3,}',
            r'дата\s+составления',
            r'место\s+составления',
            r'печать',
            r'м\.п\.',
            r'/подпись/',
            r'секретарь\s*[:\-].*_+',
            r'председатель\s*[:\-].*_+'
        ]
        
        self.body_transition_markers = [
            r'основание\s*[:\-]',
            r'обязательство\s*[:\-]',
            r'сумм[аые]\s*[:\-]',
            r'должник\s*[:\-]',
            r'кредитор\s*[:\-]',
            r'нарушитель\s*[:\-]',
            r'гражданин\s+[А-ЯЁ]',
            r'организация\s*[:\-]',
            r'участники\s*[:\-]'
        ]
    
    def split_sections(self, text: str) -> Dict[str, str]:
        """
        Split document text into header, body, and footer sections
        
        Args:
            text: Full document text
            
        Returns:
            Dict with 'header', 'body', 'footer' keys
        """
        if not text or len(text.strip()) < 20:
            return {"header": "", "body": text.strip(), "footer": ""}
        
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        
        # Find section boundaries
        header_end = self._find_header_end(cleaned_lines)
        footer_start = self._find_footer_start(cleaned_lines)
        
        # Adjust boundaries to avoid overlap
        if footer_start <= header_end:
            footer_start = len(cleaned_lines)
        
        # Extract sections
        header_lines = cleaned_lines[:header_end]
        body_lines = cleaned_lines[header_end:footer_start]
        footer_lines = cleaned_lines[footer_start:]
        
        result = {
            "header": '\n'.join(header_lines).strip(),
            "body": '\n'.join(body_lines).strip(),
            "footer": '\n'.join(footer_lines).strip()
        }
        
        # Validate sections
        result = self._validate_sections(result, cleaned_lines)
        
        logger.debug(f"Document split: header={len(result['header'])}, "
                    f"body={len(result['body'])}, footer={len(result['footer'])}")
        
        return result
    
    def _find_header_end(self, lines: List[str]) -> int:
        """Find where header ends and body begins"""
        header_found = False
        
        # Look for header markers first
        for i, line in enumerate(lines):
            if any(re.search(marker, line, re.IGNORECASE) for marker in self.header_markers):
                header_found = True
                continue
            
            # After header is found, look for transition to body
            if header_found:
                # Empty lines often indicate section break
                if not line:
                    # Check if next few lines are also empty or contain body content
                    empty_count = 0
                    for j in range(i, min(i + 3, len(lines))):
                        if j < len(lines) and not lines[j]:
                            empty_count += 1
                        elif j < len(lines) and any(re.search(marker, lines[j], re.IGNORECASE) 
                                                   for marker in self.body_transition_markers):
                            return j
                    
                    if empty_count >= 2:  # Multiple empty lines
                        return i + empty_count
                
                # Direct body transition markers
                if any(re.search(marker, line, re.IGNORECASE) for marker in self.body_transition_markers):
                    return i
        
        # Fallback: if no clear structure, assume first 3-5 lines are header
        if header_found:
            return min(5, len(lines) // 3)
        
        # No header markers found - treat as minimal header
        return min(2, len(lines))
    
    def _find_footer_start(self, lines: List[str]) -> int:
        """Find where footer begins"""
        # Search from end backwards
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            if any(re.search(marker, line, re.IGNORECASE) for marker in self.footer_markers):
                # Find the start of footer section (might be a few lines before)
                footer_start = i
                
                # Look backwards for related footer content
                for j in range(i - 1, max(0, i - 5), -1):
                    prev_line = lines[j]
                    if (not prev_line or  # Empty line
                        any(re.search(marker, prev_line, re.IGNORECASE) for marker in self.footer_markers) or
                        re.search(r'[А-ЯЁ][а-яё]+\s*[:\-]\s*_+', prev_line)):  # Name: ___
                        footer_start = j
                    else:
                        break
                
                return footer_start
        
        # No footer markers found
        return len(lines)
    
    def _validate_sections(self, sections: Dict[str, str], all_lines: List[str]) -> Dict[str, str]:
        """Validate and adjust section boundaries if needed"""
        # Ensure body is not empty
        if not sections["body"] and sections["header"]:
            # Move some header content to body
            header_lines = sections["header"].split('\n')
            if len(header_lines) > 2:
                sections["header"] = '\n'.join(header_lines[:2])
                sections["body"] = '\n'.join(header_lines[2:] + [sections["body"]])
        
        # Ensure no section is overly dominant
        total_length = len('\n'.join(all_lines))
        if total_length > 0:
            header_ratio = len(sections["header"]) / total_length
            body_ratio = len(sections["body"]) / total_length
            
            # If header is more than 60% of document, redistribute
            if header_ratio > 0.6 and body_ratio < 0.2:
                header_lines = sections["header"].split('\n')
                split_point = len(header_lines) // 2
                sections["header"] = '\n'.join(header_lines[:split_point])
                sections["body"] = '\n'.join(header_lines[split_point:] + [sections["body"]])
        
        return sections
    
    def analyze_section_structure(self, sections: Dict[str, str]) -> Dict[str, any]:
        """Analyze the structure of parsed sections"""
        analysis = {
            "section_lengths": {
                "header": len(sections["header"]),
                "body": len(sections["body"]), 
                "footer": len(sections["footer"])
            },
            "section_line_counts": {
                "header": len(sections["header"].split('\n')) if sections["header"] else 0,
                "body": len(sections["body"].split('\n')) if sections["body"] else 0,
                "footer": len(sections["footer"].split('\n')) if sections["footer"] else 0
            },
            "document_type_indicators": self._analyze_document_type(sections),
            "completeness_score": self._calculate_completeness_score(sections)
        }
        
        return analysis
    
    def _analyze_document_type(self, sections: Dict[str, str]) -> Dict[str, float]:
        """Analyze document type based on section content"""
        header_text = sections["header"].lower()
        body_text = sections["body"].lower()
        
        scores = {
            "bill_of_exchange": 0.0,
            "fine_notice": 0.0,
            "protocol": 0.0
        }
        
        # Bill of exchange indicators
        if "вексель" in header_text:
            scores["bill_of_exchange"] += 0.8
        if any(word in body_text for word in ["обязательство", "должник", "кредитор"]):
            scores["bill_of_exchange"] += 0.3
        
        # Fine notice indicators  
        if "постановление" in header_text:
            scores["fine_notice"] += 0.8
        if any(word in body_text for word in ["штраф", "нарушение", "коап"]):
            scores["fine_notice"] += 0.3
        
        # Protocol indicators
        if "протокол" in header_text:
            scores["protocol"] += 0.8
        if any(word in body_text for word in ["заседание", "решение", "участники"]):
            scores["protocol"] += 0.3
        
        return scores
    
    def _calculate_completeness_score(self, sections: Dict[str, str]) -> float:
        """Calculate how complete the document structure appears"""
        score = 0.0
        
        # Check if all sections exist
        if sections["header"]:
            score += 0.4
        if sections["body"]:
            score += 0.5
        if sections["footer"]:
            score += 0.1
        
        # Check for balanced distribution
        total_length = sum(len(s) for s in sections.values())
        if total_length > 0:
            body_ratio = len(sections["body"]) / total_length
            if 0.3 <= body_ratio <= 0.8:  # Body should be substantial but not everything
                score += 0.2
        
        return min(1.0, score)

# Global parser instance
_parser = None

def get_parser() -> DocumentSectionParser:
    """Get global parser instance"""
    global _parser
    if _parser is None:
        _parser = DocumentSectionParser()
    return _parser

def split_sections(text: str) -> Dict[str, str]:
    """
    Split document text into header, body, and footer sections
    
    Args:
        text: Full document text
        
    Returns:
        Dict with 'header', 'body', 'footer' keys
    """
    parser = get_parser()
    return parser.split_sections(text)

def analyze_document_structure(text: str) -> Dict[str, any]:
    """
    Analyze document structure and return detailed information
    
    Args:
        text: Full document text
        
    Returns:
        Dict with sections and structural analysis
    """
    parser = get_parser()
    sections = parser.split_sections(text)
    analysis = parser.analyze_section_structure(sections)
    
    return {
        "sections": sections,
        "analysis": analysis
    } 