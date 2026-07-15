import pytest
from app.services.valuation import ValuationService


def test_valuation_calculate():
    """Test valuation calculation with tech model."""
    service = ValuationService()
    
    data = {
        'pe': 20,
        'pb': 5,
        'price': 100,
        'ma20': 100,
        'ma60': 100,
        'volatility': 0.03
    }
    
    result = service.calculate('600519', 'tech', data)
    
    assert 'score' in result
    assert 'factors' in result
    assert 'weights' in result
    assert 0 <= result['score'] <= 100
    assert isinstance(result['factors'], dict)
    assert len(result['factors']) > 0
    
    # All factor scores should be 0-100
    for factor_code, score in result['factors'].items():
        assert 0 <= score <= 100, f"Factor {factor_code} score {score} out of range"


def test_valuation_calculate_with_ai():
    """Test valuation calculation with AI enabled."""
    service = ValuationService()
    
    data = {
        'pe': 20,
        'pb': 5,
        'price': 100,
        'ma20': 100,
        'ma60': 100,
        'volatility': 0.03
    }
    
    result = service.calculate('600519', 'tech', data, ai_enabled=True)
    
    assert 'score' in result
    assert 0 <= result['score'] <= 100
    # When AI is enabled, ai_analysis should be in factors
    assert 'ai_analysis' in result['factors']


def test_valuation_invalid_model():
    """Test that invalid model code raises error."""
    service = ValuationService()
    
    with pytest.raises(ValueError):
        service.calculate('600519', 'invalid_model', {})


def test_status_levels():
    """Test status string for different percentiles."""
    service = ValuationService()
    
    assert service.get_status(95) == '极度低估'
    assert service.get_status(90) == '极度低估'
    assert service.get_status(75) == '低估'
    assert service.get_status(70) == '低估'
    assert service.get_status(55) == '中性偏低'
    assert service.get_status(50) == '中性偏低'
    assert service.get_status(35) == '中性偏高'
    assert service.get_status(30) == '中性偏高'
    assert service.get_status(15) == '高估'
    assert service.get_status(10) == '高估'
    assert service.get_status(5) == '极度高估'
    assert service.get_status(0) == '极度高估'


def test_get_models():
    """Test getting all models."""
    service = ValuationService()
    models = service.get_models()
    assert isinstance(models, list)
    assert len(models) >= 6  # At least 6 built-in models


def test_get_factors():
    """Test getting all factors."""
    service = ValuationService()
    factors = service.get_factors()
    assert isinstance(factors, list)
    assert len(factors) >= 9  # At least 9 built-in factors
