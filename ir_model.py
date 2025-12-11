from typing import Dict, List, Any, Optional, Union


class TaskIR:
    """Intermediate Representation for a Task"""
    def __init__(self):
        self.id: str = ""
        self.label: str = ""
        self.type: str = "abstract"
        self.duration: Dict[str, Any] = {"min": 0, "max": 0, "unit": "s"}
        self.operator: Optional['OperatorIR'] = None
        # Iterative property: True by default (interpreted as wildcard '*').
        # Can be an integer >=0, the wildcard string "*", or a boolean.
        self.iterative: Union[int, str, bool] = True
        self.optional: bool = False
        self.refs: List[Dict[str, str]] = []
        # Allow parsers to attach direct children if they want (not required for XML conversion)
        self.children: List[Union['TaskIR', 'OperatorIR']] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert IR to dictionary"""
        result = {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "duration": self.duration,
            "optional": self.optional,
            "iterative": self.iterative,
            "refs": self.refs
        }
        
        if self.operator:
            result["operator"] = self.operator
        
        if self.children:
            result["children"] = [
                child.to_dict() if isinstance(child, TaskIR) else child.to_dict()
                for child in self.children
            ]
        
        if self.operator:
            result["operator"] = self.operator.to_dict()
        return result


class OperatorIR:
    """Intermediate Representation for an Operator node"""
    def __init__(self):
        self.type: str = "enable"
        self.children: List[Union[TaskIR, 'OperatorIR']] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "children": [
                child.to_dict() if isinstance(child, TaskIR) else child.to_dict()
                for child in self.children
            ]
        }
