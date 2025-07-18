"""
Legal ASI - Document Classification Router
Enhanced with document section parsing and field extraction
"""

import logging
import asyncio
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from api.auth import current_annotator_user
from api.models.user import User

# Import document processing capabilities
from ml.preprocess import split_sections, analyze_document_structure
from ml.extract_fields import extract_fields_from_sections

logger = logging.getLogger(__name__)

# Request/Response Models
class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="Document text to classify")
    include_sections: bool = Field(default=True, description="Include document section parsing")
    include_fields: bool = Field(default=True, description="Include field extraction from sections")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")

class SectionInfo(BaseModel):
    content: str = Field(description="Section content")
    length: int = Field(description="Character count")
    line_count: int = Field(description="Line count")

class DocumentSections(BaseModel):
    header: SectionInfo
    body: SectionInfo  
    footer: SectionInfo

class DocumentAnalysis(BaseModel):
    completeness_score: float = Field(description="Document structure completeness (0-1)")
    document_type_indicators: Dict[str, float] = Field(description="Document type confidence scores")
    section_lengths: Dict[str, int] = Field(description="Character counts by section")
    section_line_counts: Dict[str, int] = Field(description="Line counts by section")

class ExtractedField(BaseModel):
    value: str = Field(description="Extracted value")
    section: str = Field(description="Source section")
    context: str = Field(description="Surrounding context")
    position: int = Field(description="Position in text")

class ExtractedAmount(ExtractedField):
    amount: int = Field(description="Numeric amount")
    currency: str = Field(description="Currency")
    formatted: str = Field(description="Formatted display")

class ExtractedDate(ExtractedField):
    formatted: str = Field(description="Formatted date")
    day: int = Field(description="Day")
    month: int = Field(description="Month") 
    year: int = Field(description="Year")

class ExtractedPerson(ExtractedField):
    name: str = Field(description="Person name")
    role: str = Field(description="Role/function")

class ExtractedOrganization(ExtractedField):
    name: str = Field(description="Organization name")
    type: str = Field(description="Organization type")

class ExtractedFields(BaseModel):
    amounts: List[ExtractedAmount] = Field(default=[], description="Monetary amounts")
    dates: List[ExtractedDate] = Field(default=[], description="Dates")
    persons: List[ExtractedPerson] = Field(default=[], description="Person names")
    organizations: List[ExtractedOrganization] = Field(default=[], description="Organizations")
    document_numbers: List[ExtractedField] = Field(default=[], description="Document numbers")
    passports: List[ExtractedField] = Field(default=[], description="Passport data")
    inn_codes: List[ExtractedField] = Field(default=[], description="INN codes")
    legal_articles: List[ExtractedField] = Field(default=[], description="Legal articles")

class ClassifyResponse(BaseModel):
    document_type: str = Field(description="Predicted document type")
    confidence: float = Field(description="Classification confidence")
    patterns_matched: List[str] = Field(description="Matched classification patterns")
    russian_text_ratio: float = Field(description="Ratio of Russian text")
    text_length: int = Field(description="Input text length")
    processing_time_ms: float = Field(description="Processing time in milliseconds")
    
    # Enhanced with document structure analysis
    sections: DocumentSections = Field(None, description="Document sections (if requested)")
    document_analysis: DocumentAnalysis = Field(None, description="Structure analysis (if requested)")
    extracted_fields: ExtractedFields = Field(None, description="Extracted structured fields (if requested)")

# Document Classification Engine
class DocumentClassifier:
    """Enhanced document classifier with section parsing"""
    
    def __init__(self):
        # Document type patterns (existing + enhanced)
        self.patterns = {
            "bill_of_exchange": {
                "keywords": ["вексель", "обязательство", "должник", "кредитор", "выплатить"],
                "regex": [r"вексель\s*№?\s*\d*", r"обязуюсь\s+выплатить", r"сумм[аые]\s+.*?\d+.*?руб"],
                "negative": ["протокол", "постановление", "заседание", "административный"],
                "section_indicators": {
                    "header": ["вексель"],
                    "body": ["обязательство", "должник", "кредитор"],
                    "footer": ["подпись"]
                }
            },
            "fine_notice": {
                "keywords": ["постановление", "правонарушение", "штраф", "коап", "нарушение"],
                "regex": [r"постановление.*?правонарушени", r"штраф.*?\d+.*?руб", r"статья.*?\d+.*?коап"],
                "negative": ["вексель", "протокол", "заседание", "обязательство"],
                "section_indicators": {
                    "header": ["постановление"],
                    "body": ["нарушение", "штраф", "правонарушение"],
                    "footer": ["инспектор", "дата составления"]
                }
            },
            "protocol": {
                "keywords": ["протокол", "заседание", "решение", "председатель", "секретарь"],
                "regex": [r"протокол.*?заседания", r"председатель.*?секретарь", r"решение.*?принято"],
                "negative": ["вексель", "постановление", "штраф", "обязательство"],
                "section_indicators": {
                    "header": ["протокол"],
                    "body": ["повестка", "присутствовали", "решение"],
                    "footer": ["председатель", "секретарь"]
                }
            }
        }
    
    def classify_document(self, 
                         text: str, 
                         include_sections: bool = True,
                         include_fields: bool = True,
                         confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Classify document with optional section parsing and field extraction
        """
        import time
        start_time = time.time()
        
        # Basic text analysis
        text_length = len(text)
        russian_chars = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        russian_ratio = russian_chars / text_length if text_length > 0 else 0
        
        # Document structure analysis
        sections_data = None
        analysis_data = None
        fields_data = None
        
        if include_sections:
            # Parse document sections
            structure_result = analyze_document_structure(text)
            sections = structure_result["sections"]
            analysis = structure_result["analysis"]
            
            # Convert to response format
            sections_data = DocumentSections(
                header=SectionInfo(
                    content=sections["header"],
                    length=len(sections["header"]),
                    line_count=len(sections["header"].split('\n')) if sections["header"] else 0
                ),
                body=SectionInfo(
                    content=sections["body"],
                    length=len(sections["body"]),
                    line_count=len(sections["body"].split('\n')) if sections["body"] else 0
                ),
                footer=SectionInfo(
                    content=sections["footer"],
                    length=len(sections["footer"]),
                    line_count=len(sections["footer"].split('\n')) if sections["footer"] else 0
                )
            )
            
            analysis_data = DocumentAnalysis(
                completeness_score=analysis["completeness_score"],
                document_type_indicators=analysis["document_type_indicators"],
                section_lengths=analysis["section_lengths"],
                section_line_counts=analysis["section_line_counts"]
            )
            
            # Extract fields if requested
            if include_fields:
                extracted = extract_fields_from_sections(sections)
                
                # Convert to response format
                fields_data = ExtractedFields(
                                         amounts=[
                         ExtractedAmount(
                             value=str(a["amount"]),
                             section=a["section"],
                             context=a["context"],
                             position=a["position"],
                             amount=a["amount"],
                             currency=a.get("currency", "руб"),
                             formatted=a["formatted"]
                         ) for a in extracted["amounts"]
                     ],
                    dates=[
                        ExtractedDate(
                            value=d["formatted"],
                            section=d["section"],
                            context=d["context"],
                            position=d["position"],
                            formatted=d["formatted"],
                            day=d["day"],
                            month=d["month"],
                            year=d["year"]
                        ) for d in extracted["dates"]
                    ],
                    persons=[
                        ExtractedPerson(
                            value=p["name"],
                            section=p["section"],
                            context=p["context"],
                            position=p["position"],
                            name=p["name"],
                            role=p["role"]
                        ) for p in extracted["persons"]
                    ],
                    organizations=[
                        ExtractedOrganization(
                            value=o["name"],
                            section=o["section"],
                            context=o["context"],
                            position=o["position"],
                            name=o["name"],
                            type=o["type"]
                        ) for o in extracted["organizations"]
                    ],
                    document_numbers=[
                        ExtractedField(
                            value=n["number"],
                            section=n["section"],
                            context=n["context"],
                            position=n["position"]
                        ) for n in extracted["document_numbers"]
                    ],
                    passports=[
                        ExtractedField(
                            value=p["formatted"],
                            section=p["section"],
                            context=f"Series: {p['series']}, Number: {p['number']}",
                            position=p["position"]
                        ) for p in extracted["passports"]
                    ],
                    inn_codes=[
                        ExtractedField(
                            value=i["inn"],
                            section=i["section"],
                            context=f"Type: {i['type']}, Length: {i['length']}",
                            position=i["position"]
                        ) for i in extracted["inn_codes"]
                    ],
                    legal_articles=[
                        ExtractedField(
                            value=a["formatted"],
                            section=a["section"],
                            context=f"Article {a['article']} of {a['code']}",
                            position=a["position"]
                        ) for a in extracted["legal_articles"]
                    ]
                )
        
        # Pattern-based classification with section awareness
        text_lower = text.lower()
        scores = {}
        all_patterns_matched = []
        
        for doc_type, pattern_config in self.patterns.items():
            score = 0.0
            patterns_matched = []
            
            # Keyword matching
            for keyword in pattern_config["keywords"]:
                if keyword in text_lower:
                    score += 0.3
                    patterns_matched.append(f"keyword:{keyword}")
            
            # Regex matching
            import re
            for regex_pattern in pattern_config["regex"]:
                if re.search(regex_pattern, text_lower):
                    score += 0.4
                    patterns_matched.append(f"regex:{regex_pattern}")
            
            # Negative pattern penalty
            for negative in pattern_config["negative"]:
                if negative in text_lower:
                    score -= 0.2
                    patterns_matched.append(f"negative:{negative}")
            
            # Section-based scoring (if sections available)
            if sections_data and "section_indicators" in pattern_config:
                section_indicators = pattern_config["section_indicators"]
                
                # Check header indicators
                if "header" in section_indicators:
                    header_text = sections_data.header.content.lower()
                    for indicator in section_indicators["header"]:
                        if indicator in header_text:
                            score += 0.5
                            patterns_matched.append(f"header:{indicator}")
                
                # Check body indicators
                if "body" in section_indicators:
                    body_text = sections_data.body.content.lower()
                    for indicator in section_indicators["body"]:
                        if indicator in body_text:
                            score += 0.3
                            patterns_matched.append(f"body:{indicator}")
                
                # Check footer indicators
                if "footer" in section_indicators:
                    footer_text = sections_data.footer.content.lower()
                    for indicator in section_indicators["footer"]:
                        if indicator in footer_text:
                            score += 0.2
                            patterns_matched.append(f"footer:{indicator}")
            
            # Russian text bonus
            if russian_ratio > 0.8:
                score += 0.1
                patterns_matched.append("russian_text_bonus")
            
            # Document structure bonus (if analysis available)
            if analysis_data:
                doc_type_score = analysis_data.document_type_indicators.get(doc_type, 0.0)
                score += doc_type_score * 0.3
                if doc_type_score > 0:
                    patterns_matched.append(f"structure:{doc_type_score:.2f}")
            
            scores[doc_type] = max(0.0, score)
            if patterns_matched:
                all_patterns_matched.extend([f"{doc_type}:{p}" for p in patterns_matched])
        
        # Determine best classification
        best_type = max(scores.keys(), key=lambda k: scores[k])
        best_confidence = scores[best_type]
        
        # Apply confidence threshold
        if best_confidence < confidence_threshold:
            best_type = "unknown"
            best_confidence = 0.0
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "document_type": best_type,
            "confidence": best_confidence,
            "patterns_matched": all_patterns_matched,
            "russian_text_ratio": russian_ratio,
            "text_length": text_length,
            "processing_time_ms": processing_time,
            "sections": sections_data,
            "document_analysis": analysis_data,
            "extracted_fields": fields_data
        }

# Router setup
router = APIRouter(prefix="/classify", tags=["classification"])
classifier = DocumentClassifier()

@router.post("/", response_model=ClassifyResponse)
async def classify_document(
    request: ClassifyRequest,
    user: User = Depends(current_annotator_user)
):
    """
    Classify legal document type with optional section parsing and field extraction
    Requires annotator or admin role.
    
    Enhanced with:
    - Document structure analysis (header/body/footer)
    - Field extraction (amounts, dates, persons, organizations, etc.)
    - Section-aware pattern matching
    - Confidence scoring with thresholds
    """
    try:
        logger.info(f"Classifying document: length={len(request.text)}, "
                   f"sections={request.include_sections}, fields={request.include_fields}")
        
        # Classify with enhanced features
        result = classifier.classify_document(
            text=request.text,
            include_sections=request.include_sections,
            include_fields=request.include_fields,
            confidence_threshold=request.confidence_threshold
        )
        
        # Build response
        response = ClassifyResponse(**result)
        
        logger.info(f"Classification complete: type={response.document_type}, "
                   f"confidence={response.confidence:.3f}, time={response.processing_time_ms:.1f}ms")
        
        return response
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@router.get("/types")
async def get_supported_types():
    """Get list of supported document types and their indicators"""
    return {
        "supported_types": list(classifier.patterns.keys()),
        "type_details": {
            doc_type: {
                "keywords": config["keywords"],
                "description": f"Patterns for {doc_type} documents"
            }
            for doc_type, config in classifier.patterns.items()
        }
    }

@router.post("/batch")
async def classify_batch(documents: List[str], include_sections: bool = True, include_fields: bool = False):
    """Classify multiple documents in batch"""
    results = []
    
    for i, text in enumerate(documents):
        try:
            result = classifier.classify_document(
                text=text,
                include_sections=include_sections,
                include_fields=include_fields
            )
            results.append({"index": i, "result": result, "error": None})
        except Exception as e:
            results.append({"index": i, "result": None, "error": str(e)})
    
    return {
        "total_documents": len(documents),
        "successful": len([r for r in results if r["error"] is None]),
        "failed": len([r for r in results if r["error"] is not None]),
        "results": results
    } 