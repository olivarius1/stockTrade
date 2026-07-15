import pytest
from app.plugins.models.base import get_model, list_models
from app.plugins.factors.base import get_factor, list_factors


def test_model_registry():
    """Test that models are registered correctly."""
    models = list_models()
    assert len(models) > 0
    
    # Check that we have the expected 6 models
    model_codes = [m['code'] for m in models]
    expected_codes = ['staples', 'cyclical', 'tech', 'bank', 'pharma', 'soe']
    for code in expected_codes:
        assert code in model_codes, f"Model {code} not found in registry"


def test_get_model():
    """Test getting a specific model by code."""
    model_class = get_model('tech')
    assert model_class is not None
    
    # Must instantiate before calling methods
    model_instance = model_class()
    assert model_instance.get_name() == '科技股'
    assert model_instance.get_code() == 'tech'
    
    factors = model_instance.get_factors()
    assert isinstance(factors, list)
    assert len(factors) > 0
    
    weights = model_instance.get_weights()
    assert isinstance(weights, dict)
    assert len(weights) > 0
    
    # Weights should sum to roughly 1.0 (or close, before AI factor)
    total = sum(weights.values())
    assert 0.8 <= total <= 1.2  # Allow some tolerance


def test_factor_registry():
    """Test that factors are registered correctly."""
    factors = list_factors()
    assert len(factors) > 0
    
    # Check that we have the expected factors
    factor_codes = [f['code'] for f in factors]
    expected_codes = ['pe', 'pb', 'peg', 'ma_deviation', 'volatility', 'volume', 
                      'roe', 'dividend', 'ai_analysis']
    for code in expected_codes:
        assert code in factor_codes, f"Factor {code} not found in registry"


def test_get_factor():
    """Test getting a specific factor by code."""
    factor_class = get_factor('pe')
    assert factor_class is not None
    
    # Must instantiate before calling methods
    factor_instance = factor_class()
    assert factor_instance.get_name() == 'PE评分'
    assert factor_instance.get_code() == 'pe'
    
    requires = factor_instance.requires_data()
    assert isinstance(requires, list)


def test_pe_score():
    """Test PE factor scoring."""
    factor_class = get_factor('pe')
    assert factor_class is not None
    factor_instance = factor_class()
    
    # Test with low PE (should score high - undervalued)
    score_low_pe = factor_instance.score({'pe': 10, 'pe_min': 5, 'pe_max': 50})
    assert 0 <= score_low_pe <= 100
    assert score_low_pe > 50  # Low PE should be high score
    
    # Test with high PE (should score low - overvalued)
    score_high_pe = factor_instance.score({'pe': 45, 'pe_min': 5, 'pe_max': 50})
    assert 0 <= score_high_pe <= 100
    assert score_high_pe < 50  # High PE should be low score


def test_all_models_have_valid_factors():
    """Test that all models reference valid factors."""
    models = list_models()
    factors = list_factors()
    factor_codes = {f['code'] for f in factors}
    
    for model in models:
        for factor_code in model.get('factors', []):
            assert factor_code in factor_codes, \
                f"Model {model['code']} references unknown factor {factor_code}"
