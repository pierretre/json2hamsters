import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from ir_model import TaskIR, OperatorIR


class HmstParser:
    """Parser to convert HAMSTERS .hmst (XML) files back to JSON format, using the shared IR."""

    HAMSTERS_NAMESPACE = "https://www.irit.fr/ICS/HAMSTERS/7.0"

    def __init__(self, hmst_filepath: str):
        self.hmst_filepath = hmst_filepath
        self.task_ir: Optional[TaskIR] = None
        self.root_task: Optional[Dict[str, Any]] = None
        self.datas: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.namespace = {'h': self.HAMSTERS_NAMESPACE}

    def parse(self) -> Dict[str, Any]:
        """Parse HMST XML file and create JSON representation (schema-friendly)."""
        tree = ET.parse(self.hmst_filepath)
        root = tree.getroot()

        # Extract namespace from root tag if present
        if '}' in root.tag:
            ns_uri = root.tag[1:].split('}')[0]
            self.namespace = {'h': ns_uri}

        # Parse the main task (first task in nodes element)
        nodes = root.find('h:nodes', self.namespace)
        if nodes is not None:
            first_task = nodes.find('h:task', self.namespace)
            if first_task is not None:
                self.task_ir = self._parse_task_element(first_task, is_root=True)
                self.root_task = self._task_ir_to_json(self.task_ir, is_root=True)

        # Parse datas section
        datas_elem = root.find('h:datas', self.namespace)
        if datas_elem is not None:
            for data_elem in datas_elem.findall('h:data', self.namespace):
                self.datas.append(self._parse_data_element(data_elem))

        # Parse errors section (phenotypes and genotypes)
        errors_elem = root.find('h:errors', self.namespace)
        if errors_elem is not None:
            for pheno_elem in errors_elem.findall('h:phenotype', self.namespace):
                self.errors.append(self._parse_phenotype_element(pheno_elem))
            for geno_elem in errors_elem.findall('h:genotype', self.namespace):
                self.errors.append(self._parse_genotype_element(geno_elem))

        result = self.root_task.copy() if self.root_task else {}
        if self.datas:
            result['datas'] = self.datas
        if self.errors:
            result['errors'] = self.errors

        return result

    def _parse_task_element(self, task_elem: ET.Element, is_root: bool = False) -> TaskIR:
        task_ir = TaskIR()
        task_ir.id = task_elem.get('id', '')
        task_ir.type = task_elem.get('type', 'abstract')

        desc_elem = task_elem.find('h:description', self.namespace)
        task_ir.label = desc_elem.text if desc_elem is not None and desc_elem.text else f"Task {task_ir.id}"

        # Parse simulation properties
        coreprops = task_elem.find('h:coreproperties', self.namespace)
        if coreprops is not None:
            sim_category = coreprops.find("h:categories/h:category[@name='simulation']", self.namespace)
            if sim_category is not None:
                props = {prop.get('name'): prop.get('value', '') for prop in sim_category.findall('h:property', self.namespace)}

                task_ir.optional = props.get('optional', 'false').lower() == 'true'

                iter_val = props.get('iterative', '*')
                if iter_val == '*':
                    task_ir.iterative = True
                elif iter_val == '0':
                    task_ir.iterative = False
                elif iter_val.isdigit():
                    task_ir.iterative = int(iter_val)
                elif iter_val.lower() in ('true', 'false'):
                    task_ir.iterative = iter_val.lower() == 'true'

                min_time = float(props.get('minexectime', '0') or 0)
                max_time = float(props.get('maxexectime', '0') or 0)
                task_ir.duration = {"min": min_time, "max": max_time, "unit": "s"}

        # Parse operator if present
        operator_elem = task_elem.find('h:operator', self.namespace)
        if operator_elem is not None:
            task_ir.operator = self._parse_operator_element(operator_elem)

        return task_ir

    def _parse_operator_element(self, operator_elem: ET.Element) -> OperatorIR:
        operator_ir = OperatorIR()
        operator_ir.type = operator_elem.get('type', 'enable')

        # Preserve document order of child tasks/operators
        for child in list(operator_elem):
            tag = self._strip_ns(child.tag)
            if tag == 'task':
                operator_ir.children.append(self._parse_task_element(child, is_root=False))
            elif tag == 'operator':
                operator_ir.children.append(self._parse_operator_element(child))

        return operator_ir

    def _task_ir_to_json(self, task_ir: TaskIR, is_root: bool = False) -> Dict[str, Any]:
        task_json: Dict[str, Any] = {"label": task_ir.label}

        has_children = bool(task_ir.operator and task_ir.operator.children)
        default_type = "goal" if is_root else ("abstract" if has_children else "inputouput")
        if task_ir.type != default_type:
            task_json["type"] = task_ir.type

        if task_ir.optional:
            task_json["optional"] = True

        if task_ir.iterative is not True:
            task_json["iterative"] = task_ir.iterative

        min_dur = task_ir.duration.get("min", 0)
        max_dur = task_ir.duration.get("max", 0)
        if min_dur != 0 or max_dur != 0:
            task_json["duration"] = {
                "min": min_dur,
                "max": max_dur,
                "unit": task_ir.duration.get("unit", "s")
            }

        if task_ir.refs:
            task_json["refs"] = task_ir.refs

        if task_ir.operator:
            task_json["operator"] = self._operator_ir_to_json(task_ir.operator)

        return task_json

    def _operator_ir_to_json(self, operator_ir: OperatorIR) -> Dict[str, Any]:
        op_json: Dict[str, Any] = {"type": operator_ir.type}
        children_json: List[Dict[str, Any]] = []

        for child in operator_ir.children:
            if isinstance(child, TaskIR):
                children_json.append(self._task_ir_to_json(child, is_root=False))
            else:
                children_json.append(self._operator_ir_to_json(child))

        if children_json:
            op_json["children"] = children_json

        return op_json

    def _parse_data_element(self, data_elem: ET.Element) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        data['id'] = data_elem.get('id', '')
        data['type'] = data_elem.get('type', 'objectdod')

        desc_elem = data_elem.find('h:description', self.namespace)
        if desc_elem is not None and desc_elem.text:
            data['label'] = desc_elem.text

        position_elem = data_elem.find('h:graphics/h:graphic/h:position', self.namespace)
        if position_elem is not None:
            x = position_elem.get('x', '0')
            y = position_elem.get('y', '0')
            data['position'] = {'x': int(x), 'y': int(y)}

        links = []
        for link_elem in data_elem.findall('h:link', self.namespace):
            link: Dict[str, Any] = {}
            task_id = link_elem.get('sourceid', '')
            link_type = link_elem.get('type', '')
            if task_id:
                link['taskId'] = task_id
            if link_type:
                link['linkType'] = link_type
            if link:
                links.append(link)

        if links:
            data['links'] = links

        return data

    def _parse_phenotype_element(self, pheno_elem: ET.Element) -> Dict[str, Any]:
        error: Dict[str, Any] = {}
        error['type'] = pheno_elem.get('type', 'humanerror')
        description = pheno_elem.get('name', '')
        if description:
            error['description'] = description

        position_elem = pheno_elem.find('h:graphics/h:graphic/h:position', self.namespace)
        if position_elem is not None:
            x = position_elem.get('x', '0')
            y = position_elem.get('y', '0')
            error['position'] = {'x': int(x), 'y': int(y)}

        phenotonodeid_elem = pheno_elem.find('h:phenotypetonode', self.namespace)
        if phenotonodeid_elem is not None:
            node_id = phenotonodeid_elem.get('nodeid', '')
            if node_id:
                error['nodeid'] = node_id

        return error

    def _parse_genotype_element(self, geno_elem: ET.Element) -> Dict[str, Any]:
        error: Dict[str, Any] = {}
        error['type'] = geno_elem.get('type', 'slip')
        description = geno_elem.get('name', '')
        if description:
            error['description'] = description

        position_elem = geno_elem.find('h:graphics/h:graphic/h:position', self.namespace)
        if position_elem is not None:
            x = position_elem.get('x', '0')
            y = position_elem.get('y', '0')
            error['position'] = {'x': int(x), 'y': int(y)}

        genotonodeid_elem = geno_elem.find('h:genotypetonode', self.namespace)
        if genotonodeid_elem is not None:
            node_id = genotonodeid_elem.get('nodeid', '')
            if node_id:
                error['nodeid'] = node_id

        return error

    def to_json(self, indent: int = 2) -> str:
        if self.root_task is None:
            raise ValueError("No task data available. Call parse() first.")

        result = self.root_task.copy()
        if self.datas:
            result['datas'] = self.datas
        if self.errors:
            result['errors'] = self.errors
        return json.dumps(result, indent=indent)

    def add_refs_from_datas(self):
        # HMST files lack stable task identifiers matching the JSON schema; keep as no-op for compatibility.
        return

    def _strip_ns(self, tag: str) -> str:
        return tag.split('}', 1)[1] if '}' in tag else tag
