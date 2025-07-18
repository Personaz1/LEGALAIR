"""
Legal ASI - Field Extraction from Document Sections
Extracts specific fields (amounts, dates, parties) from parsed document sections
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FieldExtractor:
    """Extracts structured fields from document sections"""
    
    def __init__(self):
        self.money_patterns = [
            r'(\d{1,3}(?:\s?\d{3})*(?:\s?\d{3})*)\s*(руб(?:л[ей]й?)?|₽)',
            r'сумм[аые]\s*[:\-]?\s*(\d{1,3}(?:\s?\d{3})*(?:\s?\d{3})*)\s*(руб(?:л[ей]й?)?|₽)?',
            r'штраф\s+в\s+размере\s+(\d{1,3}(?:\s?\d{3})*)\s*(руб(?:л[ей]й?)?|₽)?',
            r'к\s+платежу\s+(\d{1,3}(?:\s?\d{3})*)\s*(руб(?:л[ей]й?)?|₽)?',
            r'выплатить\s+.*?(\d{1,3}(?:\s?\d{3})*)\s*(руб(?:л[ей]й?)?|₽)?'
        ]
        
        self.date_patterns = [
            r'(\d{1,2})[./](\d{1,2})[./](\d{2,4})',
            r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{2,4})',
            r'до\s+(\d{1,2})[./](\d{1,2})[./](\d{2,4})',
            r'от\s+(\d{1,2})[./](\d{1,2})[./](\d{2,4})',
            r'дата[:\s]+(\d{1,2})[./](\d{1,2})[./](\d{2,4})'
        ]
        
        self.person_patterns = [
            r'([А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.)',  # Иванов И.И.
            r'([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+)',  # Иванов Иван Иванович
            r'должник\s*[:\-]?\s*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][\.\w]*)*)',
            r'кредитор\s*[:\-]?\s*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][\.\w]*)*)',
            r'нарушитель\s*[:\-]?\s*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][\.\w]*)*)',
            r'гражданин\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][\.\w]*)*)',
            r'инспектор\s*[:\-]?\s*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][\.\w]*)*)',
            r'председатель\s*[:\-]?\s*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][\.\w]*)*)',
            r'секретарь\s*[:\-]?\s*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][\.\w]*)*)'
        ]
        
        self.organization_patterns = [
            r'((?:ООО|ЗАО|ОАО|ПАО|АО)\s+"[^"]+?")',
            r'(ИП\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][\.\w]*)*)',
            r'организация\s*[:\-]?\s*((?:ООО|ЗАО|ОАО|ПАО|АО)\s+"[^"]+?")',
            r'кредитор\s*[:\-]?\s*((?:ООО|ЗАО|ОАО|ПАО|АО)\s+"[^"]+?")'
        ]
        
        self.document_number_patterns = [
            r'№\s*([А-ЯЁа-яё]{0,3}\-?\d+[\w\-\/]*)',
            r'номер\s*[:\-]?\s*([А-ЯЁа-яё]{0,3}\-?\d+[\w\-\/]*)',
            r'вексель\s*№\s*(\d+[\w\-\/]*)',
            r'постановление\s*.*?№\s*([А-ЯЁа-яё]{0,3}\-?\d+[\w\-\/]*)',
            r'протокол\s*.*?№\s*(\d+[\w\-\/]*)'
        ]
        
        self.passport_patterns = [
            r'паспорт\s*[:\-]?\s*(\d{4})\s*(\d{6})',
            r'паспорт\s*[:\-]?\s*серия\s+(\d{4})\s*№?\s*(\d{6})',
            r'серия\s+(\d{4})\s+№\s*(\d{6})'
        ]
        
        self.inn_patterns = [
            r'инн\s*[:\-]?\s*(\d{10,12})',
            r'ИНН[:\s]*(\d{10,12})'
        ]
        
        self.legal_article_patterns = [
            r'стать[ея]\s+(\d+(?:\.\d+)?)\s+(коап|ук|гк|тк)',
            r'(\d+(?:\.\d+)?)\s+коап\s+рф',
            r'кодекс[а-я]*\s+стать[ея]\s+(\d+(?:\.\d+)?)'
        ]
        
        # Month name mapping for Russian dates
        self.month_names = {
            'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
            'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
            'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
        }
    
    def extract_all_fields(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract all fields from document sections
        
        Args:
            sections: Dict with 'header', 'body', 'footer' sections
            
        Returns:
            Dict with extracted fields organized by type and section
        """
        all_text = f"{sections.get('header', '')} {sections.get('body', '')} {sections.get('footer', '')}"
        
        result = {
            "amounts": self.extract_money_amounts(sections),
            "dates": self.extract_dates(sections),
            "persons": self.extract_persons(sections),
            "organizations": self.extract_organizations(sections),
            "document_numbers": self.extract_document_numbers(sections),
            "passports": self.extract_passports(sections),
            "inn_codes": self.extract_inn_codes(sections),
            "legal_articles": self.extract_legal_articles(sections),
            "extraction_summary": self._generate_summary(sections)
        }
        
        # Clean and validate extracted data
        result = self._clean_extracted_data(result)
        
        logger.debug(f"Extracted fields: {len(result['amounts'])} amounts, "
                    f"{len(result['dates'])} dates, {len(result['persons'])} persons")
        
        return result
    
    def extract_money_amounts(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract money amounts with context and section"""
        amounts = []
        
        for section_name, text in sections.items():
            if not text:
                continue
                
            for pattern in self.money_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    amount_str = match.group(1).replace(' ', '').replace(',', '')
                    if amount_str.isdigit():
                        amount = int(amount_str)
                        currency = match.group(2) if len(match.groups()) > 1 and match.group(2) else 'руб'
                        
                        # Get context around the match
                        start = max(0, match.start() - 30)
                        end = min(len(text), match.end() + 30)
                        context = text[start:end].strip()
                        
                        amounts.append({
                            "amount": amount,
                            "currency": currency,
                            "formatted": f"{amount:,} {currency}".replace(',', ' '),
                            "section": section_name,
                            "context": context,
                            "position": match.start()
                        })
        
        # Remove duplicates and sort by amount
        amounts = self._deduplicate_amounts(amounts)
        amounts.sort(key=lambda x: x["amount"], reverse=True)
        
        return amounts
    
    def extract_dates(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract dates with context and section"""
        dates = []
        
        for section_name, text in sections.items():
            if not text:
                continue
                
            # Numeric dates
            for pattern in self.date_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    date_info = self._parse_date_match(match, text)
                    if date_info:
                        date_info["section"] = section_name
                        dates.append(date_info)
        
        # Remove duplicates and sort chronologically
        dates = self._deduplicate_dates(dates)
        dates.sort(key=lambda x: x.get("parsed_date", ""))
        
        return dates
    
    def extract_persons(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract person names with roles and context"""
        persons = []
        
        for section_name, text in sections.items():
            if not text:
                continue
                
            for pattern in self.person_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    name = match.group(1).strip()
                    if len(name) > 3:  # Basic validation
                        role = self._determine_person_role(match.group(0), text)
                        
                        # Get context
                        start = max(0, match.start() - 20)
                        end = min(len(text), match.end() + 20)
                        context = text[start:end].strip()
                        
                        persons.append({
                            "name": name,
                            "role": role,
                            "section": section_name,
                            "context": context,
                            "position": match.start()
                        })
        
        # Remove duplicates
        persons = self._deduplicate_persons(persons)
        
        return persons
    
    def extract_organizations(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract organization names with types"""
        organizations = []
        
        for section_name, text in sections.items():
            if not text:
                continue
                
            for pattern in self.organization_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    org_name = match.group(1).strip()
                    org_type = self._determine_org_type(org_name)
                    
                    # Get context
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    context = text[start:end].strip()
                    
                    organizations.append({
                        "name": org_name,
                        "type": org_type,
                        "section": section_name,
                        "context": context,
                        "position": match.start()
                    })
        
        # Remove duplicates
        organizations = self._deduplicate_organizations(organizations)
        
        return organizations
    
    def extract_document_numbers(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract document numbers with types"""
        numbers = []
        
        for section_name, text in sections.items():
            if not text:
                continue
                
            for pattern in self.document_number_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    number = match.group(1).strip()
                    doc_type = self._determine_document_type_from_number(match.group(0))
                    
                    # Get context
                    start = max(0, match.start() - 15)
                    end = min(len(text), match.end() + 15)
                    context = text[start:end].strip()
                    
                    numbers.append({
                        "number": number,
                        "document_type": doc_type,
                        "section": section_name,
                        "context": context,
                        "position": match.start()
                    })
        
        return numbers
    
    def extract_passports(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract passport data"""
        passports = []
        
        for section_name, text in sections.items():
            if not text:
                continue
                
            for pattern in self.passport_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    series = match.group(1)
                    number = match.group(2)
                    
                    passports.append({
                        "series": series,
                        "number": number,
                        "formatted": f"{series} {number}",
                        "section": section_name,
                        "position": match.start()
                    })
        
        return passports
    
    def extract_inn_codes(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract INN codes"""
        inn_codes = []
        
        for section_name, text in sections.items():
            if not text:
                continue
                
            for pattern in self.inn_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    inn = match.group(1)
                    
                    inn_codes.append({
                        "inn": inn,
                        "length": len(inn),
                        "type": "individual" if len(inn) == 12 else "organization",
                        "section": section_name,
                        "position": match.start()
                    })
        
        return inn_codes
    
    def extract_legal_articles(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract legal article references"""
        articles = []
        
        for section_name, text in sections.items():
            if not text:
                continue
                
            for pattern in self.legal_article_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    article_num = match.group(1)
                    code_type = match.group(2).upper() if len(match.groups()) > 1 else "UNKNOWN"
                    
                    articles.append({
                        "article": article_num,
                        "code": code_type,
                        "formatted": f"ст. {article_num} {code_type}",
                        "section": section_name,
                        "position": match.start()
                    })
        
        return articles
    
    def _parse_date_match(self, match, text) -> Optional[Dict[str, Any]]:
        """Parse a date match into structured format"""
        groups = match.groups()
        
        try:
            if len(groups) == 3:
                if groups[1] in self.month_names:
                    # Named month format
                    day = int(groups[0])
                    month = int(self.month_names[groups[1]])
                    year = int(groups[2])
                else:
                    # Numeric format
                    day = int(groups[0])
                    month = int(groups[1])
                    year = int(groups[2])
                
                # Convert 2-digit year to 4-digit
                if year < 100:
                    year += 2000 if year < 50 else 1900
                
                # Validate date
                try:
                    parsed_date = datetime(year, month, day)
                    formatted_date = parsed_date.strftime("%d.%m.%Y")
                    
                    # Get context
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    context = text[start:end].strip()
                    
                    return {
                        "original": match.group(0),
                        "formatted": formatted_date,
                        "parsed_date": parsed_date.isoformat(),
                        "day": day,
                        "month": month,
                        "year": year,
                        "context": context,
                        "position": match.start()
                    }
                except ValueError:
                    return None
            
        except (ValueError, IndexError):
            return None
        
        return None
    
    def _determine_person_role(self, match_text: str, full_text: str) -> str:
        """Determine the role of a person based on context"""
        match_lower = match_text.lower()
        
        if "должник" in match_lower:
            return "debtor"
        elif "кредитор" in match_lower:
            return "creditor"
        elif "нарушитель" in match_lower or "гражданин" in match_lower:
            return "violator"
        elif "инспектор" in match_lower:
            return "inspector"
        elif "председатель" in match_lower:
            return "chairman"
        elif "секретарь" in match_lower:
            return "secretary"
        else:
            return "person"
    
    def _determine_org_type(self, org_name: str) -> str:
        """Determine organization type from name"""
        name_upper = org_name.upper()
        
        if name_upper.startswith("ООО"):
            return "LLC"
        elif name_upper.startswith("ЗАО"):
            return "CJSC"
        elif name_upper.startswith("ОАО") or name_upper.startswith("ПАО"):
            return "JSC"
        elif name_upper.startswith("ИП"):
            return "individual_entrepreneur"
        else:
            return "organization"
    
    def _determine_document_type_from_number(self, context: str) -> str:
        """Determine document type from number context"""
        context_lower = context.lower()
        
        if "вексель" in context_lower:
            return "bill_of_exchange"
        elif "постановление" in context_lower:
            return "fine_notice"
        elif "протокол" in context_lower:
            return "protocol"
        else:
            return "document"
    
    def _clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate extracted data"""
        # Remove empty or invalid entries
        for key in data:
            if isinstance(data[key], list):
                data[key] = [item for item in data[key] if item and self._is_valid_extraction(item, key)]
        
        return data
    
    def _is_valid_extraction(self, item: Dict[str, Any], field_type: str) -> bool:
        """Validate individual extraction"""
        if field_type == "amounts":
            return item.get("amount", 0) > 0
        elif field_type == "dates":
            return "formatted" in item and len(item["formatted"]) >= 8
        elif field_type == "persons":
            return len(item.get("name", "")) > 3
        elif field_type == "organizations":
            return len(item.get("name", "")) > 3
        else:
            return True
    
    def _deduplicate_amounts(self, amounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate amounts"""
        seen = set()
        unique = []
        for amount in amounts:
            key = (amount["amount"], amount["section"])
            if key not in seen:
                seen.add(key)
                unique.append(amount)
        return unique
    
    def _deduplicate_dates(self, dates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate dates"""
        seen = set()
        unique = []
        for date in dates:
            key = (date.get("formatted", ""), date["section"])
            if key not in seen:
                seen.add(key)
                unique.append(date)
        return unique
    
    def _deduplicate_persons(self, persons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate persons"""
        seen = set()
        unique = []
        for person in persons:
            key = (person["name"].lower(), person["section"])
            if key not in seen:
                seen.add(key)
                unique.append(person)
        return unique
    
    def _deduplicate_organizations(self, orgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate organizations"""
        seen = set()
        unique = []
        for org in orgs:
            key = (org["name"].lower(), org["section"])
            if key not in seen:
                seen.add(key)
                unique.append(org)
        return unique
    
    def _generate_summary(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Generate extraction summary statistics"""
        all_text = " ".join(sections.values())
        
        return {
            "total_characters": len(all_text),
            "sections_processed": len([s for s in sections.values() if s]),
            "extraction_patterns_used": {
                "money": len(self.money_patterns),
                "dates": len(self.date_patterns),
                "persons": len(self.person_patterns),
                "organizations": len(self.organization_patterns)
            }
        }

# Global extractor instance
_extractor = None

def get_extractor() -> FieldExtractor:
    """Get global field extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = FieldExtractor()
    return _extractor

def extract_fields_from_sections(sections: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract structured fields from document sections
    
    Args:
        sections: Dict with 'header', 'body', 'footer' sections
        
    Returns:
        Dict with extracted and structured fields
    """
    extractor = get_extractor()
    return extractor.extract_all_fields(sections) 