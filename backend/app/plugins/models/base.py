from abc import ABC, abstractmethod
from typing import List, Dict

model_registry = {}

def register_model(cls):
    instance = cls()
    model_registry[instance.get_code()] = cls
    return cls

class ValuationModel(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_code(self) -> str:
        pass
    
    @abstractmethod
    def get_factors(self) -> List[str]:
        pass
    
    @abstractmethod
    def get_weights(self) -> Dict[str, float]:
        pass
    
    @abstractmethod
    def get_params(self) -> Dict[str, float]:
        pass

def get_model(model_code: str) -> ValuationModel:
    return model_registry.get(model_code)

def list_models() -> List[Dict]:
    result = []
    for code, model_cls in model_registry.items():
        instance = model_cls()
        result.append({
            "code": code,
            "name": instance.get_name(),
            "factors": instance.get_factors(),
            "weights": instance.get_weights()
        })
    return result
