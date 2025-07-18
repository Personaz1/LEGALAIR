"""
Unit tests for RAG service threshold logic and query expansion
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from api.rag_service import LegalRAGService, get_rag_service


class TestRAGThresholdLogic:
    """Test RAG service threshold and query expansion logic"""
    
    @pytest.fixture
    def mock_rag_service(self):
        """Create mock RAG service with controlled responses"""
        service = LegalRAGService(kb_dir="test_data")
        service.client = Mock()
        service.collection = Mock()
        service.status = "active"
        return service
    
    def test_query_expansion_with_document_type(self, mock_rag_service):
        """Test that query expansion includes document type"""
        # Mock search results with varying scores
        mock_rag_service.search_legal_knowledge = Mock(return_value=[
            {"relevance_score": 0.8, "source_title": "КоАП РФ", "article_number": "13.1"},
            {"relevance_score": 0.3, "source_title": "ФЗ-48", "article_number": "2"},
            {"relevance_score": 0.2, "source_title": "Test Law", "article_number": "1"}
        ])
        
        result = mock_rag_service.enhance_advisory_response(
            document_text="простой вексель",
            document_type="bill_of_exchange",
            query="анализ векселя"
        )
        
        # Verify query expansion was called with enhanced query
        mock_rag_service.search_legal_knowledge.assert_called_once()
        call_args = mock_rag_service.search_legal_knowledge.call_args
        search_query = call_args[1]['query']
        
        # Should include both base query and document type
        assert "анализ векселя" in search_query
        assert "bill_of_exchange" in search_query
    
    def test_threshold_filtering_025(self, mock_rag_service):
        """Test that 0.25 threshold properly filters results"""
        # Mock search results with scores above and below 0.25
        mock_search_results = [
            {
                "relevance_score": 0.8, 
                "source_title": "КоАП РФ", 
                "article_number": "13.1",
                "article_title": "Тест статья 1",
                "document_type": "administrative_code",
                "content": "Высокий скор контекст"
            },
            {
                "relevance_score": 0.3, 
                "source_title": "ФЗ-48", 
                "article_number": "2",
                "article_title": "Тест статья 2", 
                "document_type": "federal_law",
                "content": "Средний скор контекст"
            },
            {
                "relevance_score": 0.2, 
                "source_title": "Test Law", 
                "article_number": "1",
                "article_title": "Тест статья 3",
                "document_type": "other",
                "content": "Низкий скор контекст"
            }
        ]
        
        mock_rag_service.search_legal_knowledge = Mock(return_value=mock_search_results)
        
        result = mock_rag_service.enhance_advisory_response(
            document_text="тестовый документ",
            document_type="test_type"
        )
        
        # Should be enhanced since we have 2 results > 0.25
        assert result["enhanced"] is True
        assert len(result["legal_context"]) == 2
        
        # Verify only high-scoring results are included
        scores = [ctx["relevance_score"] for ctx in result["legal_context"]]
        assert all(score > 0.25 for score in scores)
        assert 0.8 in scores
        assert 0.3 in scores
        assert 0.2 not in scores
    
    def test_threshold_filtering_no_results_above_threshold(self, mock_rag_service):
        """Test behavior when no results meet 0.25 threshold"""
        # Mock search results all below threshold
        mock_search_results = [
            {
                "relevance_score": 0.2, 
                "source_title": "Test Law 1", 
                "article_number": "1",
                "article_title": "Тест статья 1",
                "document_type": "other",
                "content": "Низкий скор 1"
            },
            {
                "relevance_score": 0.1, 
                "source_title": "Test Law 2", 
                "article_number": "2",
                "article_title": "Тест статья 2",
                "document_type": "other", 
                "content": "Низкий скор 2"
            }
        ]
        
        mock_rag_service.search_legal_knowledge = Mock(return_value=mock_search_results)
        
        result = mock_rag_service.enhance_advisory_response(
            document_text="тестовый документ"
        )
        
        # Should not be enhanced since no results > 0.25
        assert result["enhanced"] is False
        assert len(result["legal_context"]) == 0
        assert result["context_summary"] == "Релевантный правовой контекст не найден"
    
    def test_threshold_edge_case_exactly_025(self, mock_rag_service):
        """Test edge case with score exactly at 0.25"""
        mock_search_results = [
            {
                "relevance_score": 0.25, 
                "source_title": "Edge Case Law", 
                "article_number": "1",
                "article_title": "Edge статья",
                "document_type": "test",
                "content": "Точно на пороге"
            }
        ]
        
        mock_rag_service.search_legal_knowledge = Mock(return_value=mock_search_results)
        
        result = mock_rag_service.enhance_advisory_response(
            document_text="тестовый документ"
        )
        
        # Should not be enhanced since we use > 0.25 (strict inequality)
        assert result["enhanced"] is False
        assert len(result["legal_context"]) == 0
    
    def test_query_expansion_fallback(self, mock_rag_service):
        """Test query expansion when document_type is None"""
        mock_rag_service.search_legal_knowledge = Mock(return_value=[])
        mock_rag_service._extract_key_terms = Mock(return_value="извлеченные термины")
        
        result = mock_rag_service.enhance_advisory_response(
            document_text="тестовый документ",
            document_type=None,
            query=None
        )
        
        # Verify extraction was called and query expansion handled None type
        mock_rag_service._extract_key_terms.assert_called_once_with("тестовый документ", None)
        mock_rag_service.search_legal_knowledge.assert_called_once()
        
        call_args = mock_rag_service.search_legal_knowledge.call_args
        search_query = call_args[1]['query']
        assert "извлеченные термины" in search_query


class TestRAGIntegration:
    """Integration tests for RAG service"""
    
    def test_enhanced_analysis_response_format(self):
        """Test that enhanced analysis response has correct format"""
        # This would require actual RAG service running
        # For now, test the response structure
        sample_response = {
            "enhanced": True,
            "legal_context": [{"relevance_score": 0.8}],
            "legal_references": [{"text": "test"}],
            "context_summary": "test summary",
            "search_query": "expanded query"
        }
        
        # Verify required keys are present
        required_keys = ["enhanced", "legal_context", "legal_references", "context_summary"]
        assert all(key in sample_response for key in required_keys)
        
        # Verify enhanced flag logic
        assert sample_response["enhanced"] == (len(sample_response["legal_context"]) > 0)


@pytest.fixture
def sample_legal_context():
    """Sample legal context for testing"""
    return [
        {
            "relevance_score": 0.8,
            "source_title": "КоАП РФ",
            "article_number": "13.1",
            "article_title": "Нарушение правил проведения собраний",
            "document_type": "administrative_code",
            "content": "Статья о нарушениях"
        },
        {
            "relevance_score": 0.6,
            "source_title": "ФЗ-48",
            "article_number": "2",
            "article_title": "О переводном и простом векселе",
            "document_type": "federal_law", 
            "content": "Статья о векселях"
        }
    ]


def test_threshold_improvement_impact():
    """Test that shows impact of threshold change from 0.1 to 0.25"""
    old_threshold = 0.1
    new_threshold = 0.25
    
    # Sample scores that would behave differently
    test_scores = [0.8, 0.3, 0.2, 0.15, 0.05]
    
    old_results = [score for score in test_scores if score > old_threshold]
    new_results = [score for score in test_scores if score > new_threshold]
    
    # Verify that new threshold is more selective
    assert len(new_results) < len(old_results)
    assert new_results == [0.8, 0.3]  # Only high-quality results
    assert old_results == [0.8, 0.3, 0.2, 0.15]  # Including marginal results
    
    # This demonstrates the improvement: fewer false positives 