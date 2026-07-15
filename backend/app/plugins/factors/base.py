from abc import ABC, abstractmethod
from typing import List, Dict

factor_registry = {}

def register_factor(cls):
    instance = cls()
    factor_registry[instance.get_code()] = cls
    return cls

class ValuationFactor(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_code(self) -> str:
        pass
    
    @abstractmethod
    def score(self, data: Dict) -> float:
        pass
    
    @abstractmethod
    def requires_data(self) -> List[str]:
        pass

def get_factor(factor_code: str) -> ValuationFactor:
    return factor_registry.get(factor_code)

def list_factors() -> List[Dict]:
    result = []
    for code, factor_cls in factor_registry.items():
        instance = factor_cls()
        result.append({
            "code": code,
            "name": instance.get_name(),
            "requires_data": instance.requires_data()
        })
    return result
