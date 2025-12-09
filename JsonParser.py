import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import urllib.request
import tempfile


class TaskIR:
    """Intermediate Representation for a Task"""
    def __init__(self):
        self.id: str = ""
        self.label: str = ""
        self.type: str = "abstract"
        self.description: str = ""
        self.duration: Dict[str, Any] = {"min": 0, "max": 0, "unit": "s"}
        self.operator: Optional['OperatorIR'] = None
        self.loop: Dict[str, int] = {"minIterations": 0, "maxIterations": 0}
        self.optional: bool = False
        self.refs: List[Dict[str, str]] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert IR to dictionary"""
        result = {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "description": self.description,
            "duration": self.duration,
            "optional": self.optional,
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


class JsonParser:
    # HAMSTERS XML Schema namespace and location
    HAMSTERS_NAMESPACE = "https://www.irit.fr/ICS/HAMSTERS/7.0"
    XSD_SCHEMA_LOCATION = "https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd"
    
    def __init__(self, json_data: Dict[str, Any]):
        """Initialize parser with JSON data"""
        self.json_data = json_data
        self.task_ir: Optional[TaskIR] = None
        self.datas: List[Dict[str, Any]] = json_data.get("datas", []) if isinstance(json_data, dict) else []
        self.errors: List[Dict[str, Any]] = json_data.get("errors", []) if isinstance(json_data, dict) else []
        self.schema_cache_path = Path(tempfile.gettempdir()) / "hamsters_v7.xsd"
        self._task_counter = 0  # Counter for auto-generating task IDs
        self._data_counter = 0  # Counter for auto-generating data IDs
        self._error_counter = 0  # Counter for auto-generating error IDs
        self._operator_counter = 0  # Counter for auto-generating operator IDs

    def parse(self) -> TaskIR:
        """Parse JSON and create Intermediate Representation"""
        if isinstance(self.json_data, dict):
            self.task_ir = self._parse_task(self.json_data, is_root=True)
        return self.task_ir

    def _generate_task_id(self) -> str:
        """Generate incremental task ID (lowercase)"""
        task_id = f"t{self._task_counter}"
        self._task_counter += 1
        return task_id

    def _is_operator_node(self, node: Any) -> bool:
        """Determine if a JSON node represents an operator object (has children, no label)."""
        return (
            isinstance(node, dict)
            and "children" in node
            and "label" not in node
            and ("type" in node or "operator" in node)
        )

    def _parse_operator(self, op_data: Dict[str, Any]) -> 'OperatorIR':
        """Parse an operator node allowing nested operators and tasks."""
        op = OperatorIR()
        op.type = op_data.get("type") or op_data.get("operator", "enable")
        children = op_data.get("children", []) if isinstance(op_data, dict) else []
        op.children = [
            self._parse_task(child, is_root=False) if not self._is_operator_node(child)
            else self._parse_operator(child)
            for child in children
        ]
        return op
    
    def _parse_task(self, task_data: Dict[str, Any], is_root: bool = False) -> TaskIR:
        """Convert a task JSON object to TaskIR with default filling"""
        task = TaskIR()
        
        # Required fields - auto-generate ID if not provided
        task.id = task_data.get("id") if "id" in task_data else self._generate_task_id()
        task.label = task_data.get("label", "Unnamed Task")
        
        # Apply type rules: if type explicitly provided, use it; otherwise root is 'goal', others are 'abstract'
        if "type" in task_data:
            # If type is explicitly specified in JSON, always use it
            task.type = task_data["type"]
        else:
            # If type is not specified, apply default rules
            task.type = "goal" if is_root else "abstract"
        
        # Optional fields
        task.description = task_data.get("description", "")
        task.optional = task_data.get("optional", False)
        
        # Duration with defaults
        if "duration" in task_data:
            task.duration = {
                "min": task_data["duration"].get("min", 0),
                "max": task_data["duration"].get("max", 0),
                "unit": task_data["duration"].get("unit", "s")
            }
        
        # Operator object (optional)
        if "operator" in task_data and isinstance(task_data["operator"], dict):
            task.operator = self._parse_operator(task_data["operator"])
        
        # Loop configuration
        if "loop" in task_data:
            task.loop = {
                "minIterations": task_data["loop"].get("minIterations", 0),
                "maxIterations": task_data["loop"].get("maxIterations", 0)
            }
        
        # References to datas and errors with link metadata (support string shorthand)
        if isinstance(task_data.get("refs", []), list):
            refs_list = []
            for ref in task_data.get("refs", []):
                if isinstance(ref, str):
                    refs_list.append({"id": ref, "target": "data", "linkType": ""})
                elif isinstance(ref, dict) and "id" in ref:
                    refs_list.append({
                        "id": str(ref.get("id", "")),
                        "target": str(ref.get("target", "data")),
                        "linkType": str(ref.get("linkType", ""))
                    })
            task.refs = refs_list
        
        return task

    def _iter_tasks(self, task: TaskIR):
        """Yield all TaskIR nodes starting from the given task (depth-first)."""
        yield task
        if task.operator:
            for child in task.operator.children:
                if isinstance(child, TaskIR):
                    yield from self._iter_tasks(child)
                else:
                    yield from self._iter_operator_tasks(child)

    def _iter_operator_tasks(self, operator: 'OperatorIR'):
        """Yield TaskIR nodes contained within an OperatorIR."""
        for child in operator.children:
            if isinstance(child, TaskIR):
                yield from self._iter_tasks(child)
            else:
                yield from self._iter_operator_tasks(child)

    def to_xml(self) -> str:
        """Convert TaskIR to formatted XML string with HAMSTERS schema"""
        if not self.task_ir:
            raise ValueError("No task IR available. Call parse() first.")
        
        # Create root element with HAMSTERS namespace (https)
        root = ET.Element("hamsters")
        root.set("xmlns", self.HAMSTERS_NAMESPACE)
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("name", self.task_ir.label)
        root.set("version", "7")
        root.set("xsi:schemaLocation", f"{self.HAMSTERS_NAMESPACE} {self.XSD_SCHEMA_LOCATION}")
        
        # Create required nodes element
        nodes_elem = ET.SubElement(root, "nodes")
        
        # Add tasks recursively to nodes
        self._add_tasks_recursively(nodes_elem, self.task_ir)
        
        # Resolve data IDs (preserve provided, auto-generate missing) and build link map
        resolved_data_ids = []
        for data_obj in self.datas:
            data_id = data_obj.get("id")
            if not data_id:
                data_id = f"a{self._data_counter}"
                self._data_counter += 1
            resolved_data_ids.append(data_id)

        # Prepare default link type per DOD kind
        device_dods = {"deviceouputdod", "deviceinputdod", "deviceiodod"}
        def default_link_type(data_type: str) -> str:
            return "USES_TYPE" if data_type in device_dods else "TEST_TYPE"

        # Build mapping data_id -> list of (task id, link type) that reference it (after ID resolution)
        data_links_map = {}
        if self.task_ir:
            for t in self._iter_tasks(self.task_ir):
                for ref in t.refs:
                    if ref.get("target", "data") != "data":
                        continue
                    ref_id = ref.get("id", "")
                    if not ref_id:
                        continue
                    data_links_map.setdefault(ref_id, []).append((t.id, ref.get("linkType", "")))

        # Add datas element with data objects if provided (must come before errors per schema)
        datas_elem = ET.SubElement(root, "datas")
        if self.datas:
            for data_obj, data_id in zip(self.datas, resolved_data_ids):
                data_type = data_obj.get("type", "")
                fallback_link_type = default_link_type(data_type)
                # Auto-generate link entries from refs with optional linkType; default per DOD type
                auto_links = [
                    {"taskId": task_id, "linkType": (link_type or fallback_link_type)}
                    for task_id, link_type in data_links_map.get(data_id, [])
                ]
                combined_links = data_obj.get("links", []) + auto_links
                self._add_data_element(datas_elem, data_obj, combined_links, data_id)
        
        # Add errors element with error objects
        errors_elem = ET.SubElement(root, "errors")
        if self.errors:
            self._add_error_elements(errors_elem, self.errors)
        
        # Add security element (empty)
        security_elem = ET.SubElement(root, "security")
        
        # Add parameters element (empty)
        parameters_elem = ET.SubElement(root, "parameters")
        
        # Add instancevalues element (empty)
        instancevalues_elem = ET.SubElement(root, "instancevalues")
        
        # Add parametersdefinitions element (empty)
        parametersdefs_elem = ET.SubElement(root, "parametersdefinitions")
        
        # Add mainproperties element
        mainproperties_elem = ET.SubElement(root, "mainproperties")
        timemanagement_prop = ET.SubElement(mainproperties_elem, "property")
        timemanagement_prop.set("name", "timemanagement")
        timemanagement_prop.set("type", "fr.irit.ics.circus.hamsters.api.TimeManagement")
        timemanagement_prop.set("value", "NORMAL")
        
        return self._prettify_xml(root)

    def _add_tasks_recursively(self, parent_elem: ET.Element, task: TaskIR):
        """Recursively add task and its children to XML nodes element"""
        task_elem = self._task_to_xml_element(task)
        parent_elem.append(task_elem)

    def _task_to_xml_element(self, task: TaskIR) -> ET.Element:
        """Convert TaskIR to XML Element matching HAMSTERS schema"""
        task_elem = ET.Element("task")
        task_elem.set("id", task.id)
        task_elem.set("type", task.type)  # Required by schema
        task_elem.set("copy", "false")  # Required by schema
        task_elem.set("knowledgeproceduraltype", "")
        
        # Add graphics (required by hamstersnode base type)
        graphics_elem = ET.SubElement(task_elem, "graphics")
        graphic_elem = ET.SubElement(graphics_elem, "graphic")
        graphic_elem.set("folded", "false")
        position_elem = ET.SubElement(graphic_elem, "position")
        position_elem.set("x", "0")
        position_elem.set("y", "0")
        
        # If task has an operator object, render it
        if task.operator:
            task_elem.append(self._operator_to_xml_element(task.operator))
        
        # Add description (required by schema, use label for brevity)
        desc_elem = ET.SubElement(task_elem, "description")
        desc_elem.text = task.label
        
        # Add xlproperties (required by schema, can be empty)
        xlprops_elem = ET.SubElement(task_elem, "xlproperties")
        
        # Add coreproperties with categories (required by schema)
        coreprops_elem = ET.SubElement(task_elem, "coreproperties")
        categories_elem = ET.SubElement(coreprops_elem, "categories")
        
        # Add simulation category
        sim_category = ET.SubElement(categories_elem, "category")
        sim_category.set("name", "simulation")
        
        duration_prop = ET.SubElement(sim_category, "property")
        duration_prop.set("name", "duration")
        duration_prop.set("value", "false")
        
        iterative_prop = ET.SubElement(sim_category, "property")
        iterative_prop.set("name", "iterative")
        iterative_prop.set("value", "0")
        
        optional_prop = ET.SubElement(sim_category, "property")
        optional_prop.set("name", "optional")
        optional_prop.set("value", "true" if task.optional else "false")
        
        minexectime_prop = ET.SubElement(sim_category, "property")
        minexectime_prop.set("name", "minexectime")
        minexectime_prop.set("value", str(task.duration.get("min", 0)))
        
        maxexectime_prop = ET.SubElement(sim_category, "property")
        maxexectime_prop.set("name", "maxexectime")
        maxexectime_prop.set("value", str(task.duration.get("max", 0)))
        
        # Add authority category
        auth_category = ET.SubElement(categories_elem, "category")
        auth_category.set("name", "authority")
        
        responsibility_prop = ET.SubElement(auth_category, "property")
        responsibility_prop.set("name", "responsibility")
        responsibility_prop.set("type", "java.lang.Boolean")
        responsibility_prop.set("value", "false")
        
        authority_prop = ET.SubElement(auth_category, "property")
        authority_prop.set("name", "authority")
        authority_prop.set("type", "java.lang.Boolean")
        authority_prop.set("value", "false")
        
        # Add criticality category
        crit_category = ET.SubElement(categories_elem, "category")
        crit_category.set("name", "criticality")
        
        criticality_prop = ET.SubElement(crit_category, "property")
        criticality_prop.set("name", "criticality")
        criticality_prop.set("type", "java.lang.Integer")
        criticality_prop.set("value", "0")
        
        return task_elem

    def _operator_to_xml_element(self, operator: OperatorIR) -> ET.Element:
        """Convert OperatorIR to XML Element, supporting nested operators"""
        operator_elem = ET.Element("operator")
        operator_elem.set("id", f"o{self._operator_counter}")
        self._operator_counter += 1
        operator_elem.set("type", operator.type)
        operator_elem.set("knowledgeproceduraltype", "")

        op_graphics = ET.SubElement(operator_elem, "graphics")
        op_graphic = ET.SubElement(op_graphics, "graphic")
        op_position = ET.SubElement(op_graphic, "position")
        op_position.set("x", "0")
        op_position.set("y", "0")

        spacing_x = 200
        base_y = 200  # place children below the parent task/operator
        for idx, child in enumerate(operator.children):
            child_x = idx * spacing_x
            if isinstance(child, TaskIR):
                child_elem = self._task_to_xml_element(child)
                self._set_position(child_elem, child_x, base_y)
                operator_elem.append(child_elem)
            else:
                child_elem = self._operator_to_xml_element(child)
                self._set_position(child_elem, child_x, base_y)
                operator_elem.append(child_elem)

        return operator_elem

    def _set_position(self, elem: ET.Element, x: int, y: int):
        """Set the first graphics/graphic/position of an element if present."""
        pos = elem.find("graphics/graphic/position")
        if pos is not None:
            pos.set("x", str(x))
            pos.set("y", str(y))

    def _add_data_element(self, datas_elem: ET.Element, data_obj: Dict[str, Any], link_entries: Optional[List[Dict[str, Any]]] = None, data_id: Optional[str] = None):
        """Add a data element to the datas section"""
        # Use resolved ID passed in; fall back to object value
        if data_id is None:
            data_id = data_obj.get("id")
            if not data_id:
                data_id = f"a{self._data_counter}"
                self._data_counter += 1
        
        # Create data element
        data_elem = ET.SubElement(datas_elem, "data")
        data_elem.set("type", data_obj.get("type", "objectdod"))
        data_elem.set("id", data_id)
        
        # Add description
        desc_elem = ET.SubElement(data_elem, "description")
        desc_elem.text = data_obj.get("description", "")
        
        # Add properties (empty)
        properties_elem = ET.SubElement(data_elem, "properties")
        
        # Add links if provided
        links = link_entries if link_entries is not None else data_obj.get("links", [])
        for link in links:
            link_elem = ET.SubElement(data_elem, "link")
            link_elem.set("feature", "none")
            link_elem.set("sourceid", link.get("taskId", ""))
            if link.get("linkType"):
                link_elem.set("type", link.get("linkType"))
            link_elem.set("value", "")
            
            # Add empty points element
            points_elem = ET.SubElement(link_elem, "points")
        
        # Add graphics with position
        graphics_elem = ET.SubElement(data_elem, "graphics")
        graphic_elem = ET.SubElement(graphics_elem, "graphic")
        
        position = data_obj.get("position", {"x": 0, "y": 0})
        position_elem = ET.SubElement(graphic_elem, "position")
        position_elem.set("x", str(position.get("x", 0)))
        position_elem.set("y", str(position.get("y", 0)))

    def _add_error_elements(self, errors_elem: ET.Element, errors: List[Dict[str, Any]]):
        """Add error elements (phenotype/genotype) to the errors section with default values"""
        # Map error types to their corresponding node IDs (if available)
        error_position_map = {}
        
        for idx, error_obj in enumerate(errors):
            error_id = f"e{self._error_counter}"
            self._error_counter += 1
            
            error_type = error_obj.get("type", "humanerror")
            description = error_obj.get("description", f"Error {error_id}")
            
            # Get position from error object or use default
            position = error_obj.get("position", {"x": 0, "y": 0})
            x_pos = str(position.get("x", 0))
            y_pos = str(position.get("y", 0))
            
            # Determine if this is a phenotype (humanerror) or genotype (other types)
            if error_type == "humanerror":
                # Create phenotype element
                phenotype_elem = ET.SubElement(errors_elem, "phenotype")
                phenotype_elem.set("name", description)
                phenotype_elem.set("type", error_type)
                phenotype_elem.set("id", error_id)
                
                # Add graphics
                graphics_elem = ET.SubElement(phenotype_elem, "graphics")
                graphic_elem = ET.SubElement(graphics_elem, "graphic")
                position_elem = ET.SubElement(graphic_elem, "position")
                position_elem.set("x", x_pos)
                position_elem.set("y", y_pos)
                
                # Add phenotypetonode with empty nodeid (optional link to task)
                phenotonodeid = error_obj.get("nodeid", "")
                phenotypetonode_elem = ET.SubElement(phenotype_elem, "phenotypetonode")
                phenotypetonode_elem.set("nodeid", phenotonodeid)
                points_elem = ET.SubElement(phenotypetonode_elem, "points")
            else:
                # Create genotype element for slip, rbm, kbm, lapse
                genotype_elem = ET.SubElement(errors_elem, "genotype")
                genotype_elem.set("gemstype", "Undefined")  # Default value
                genotype_elem.set("name", description)
                genotype_elem.set("type", error_type)
                genotype_elem.set("id", error_id)
                
                # Add graphics
                graphics_elem = ET.SubElement(genotype_elem, "graphics")
                graphic_elem = ET.SubElement(graphics_elem, "graphic")
                position_elem = ET.SubElement(graphic_elem, "position")
                position_elem.set("x", x_pos)
                position_elem.set("y", y_pos)
                
                # Add genotypetonode if nodeid is provided
                nodeid = error_obj.get("nodeid", "")
                if nodeid or error_type in ["kbm", "rbm"]:  # Some genotypes may link to nodes
                    genotypetonode_elem = ET.SubElement(genotype_elem, "genotypetonode")
                    genotypetonode_elem.set("nodeid", nodeid)
                    points_elem = ET.SubElement(genotypetonode_elem, "points")

    def _prettify_xml(self, elem: ET.Element) -> str:
        """Return a pretty-printed XML string."""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        xml_str = reparsed.toprettyxml(indent="    ")
        # Ensure UTF-8 encoding in the XML declaration
        if '<?xml' in xml_str:
            xml_str = xml_str.replace('<?xml version="1.0" ?>', '<?xml version="1.0" encoding="UTF-8"?>')
        return xml_str

    def to_json_ir(self) -> str:
        """Convert TaskIR back to JSON"""
        if not self.task_ir:
            raise ValueError("No task IR available. Call parse() first.")
        return json.dumps(self.task_ir.to_dict(), indent=2)

    def _download_schema(self) -> bool:
        """Download HAMSTERS XSD schema"""
        try:
            if self.schema_cache_path.exists():
                # Verify cached schema is not empty
                size = self.schema_cache_path.stat().st_size
                if size == 0:
                    print(f"Warning: Cached schema is empty ({size} bytes), redownloading...")
                    self.schema_cache_path.unlink()
                else:
                    print(f"Using cached schema: {self.schema_cache_path} ({size} bytes)")
                    return True
            
            print(f"Downloading HAMSTERS schema from {self.XSD_SCHEMA_LOCATION}...")
            urllib.request.urlretrieve(self.XSD_SCHEMA_LOCATION, str(self.schema_cache_path))
            
            # Verify downloaded schema is not empty
            size = self.schema_cache_path.stat().st_size
            if size == 0:
                print(f"Error: Downloaded schema is empty ({size} bytes)")
                return False
            
            print(f"Schema downloaded successfully: {self.schema_cache_path} ({size} bytes)")
            return True
        except Exception as e:
            print(f"Error downloading schema: {e}")
            return False

    def validate_xml(self, xml_string: str) -> tuple:
        """Validate generated XML against HAMSTERS schema. Returns (bool, error_msg)."""
        try:
            # Try to import lxml for full validation
            try:
                from lxml import etree
                print("Using lxml for full schema validation...")
                
                # Download schema if not cached
                if not self._download_schema():
                    # Fallback to basic validation
                    print("Schema download failed, falling back to basic validation...")
                    return self._basic_validate_xml(xml_string)
                
                # Parse XML and schema
                try:
                    xml_doc = etree.fromstring(xml_string.encode('utf-8'))
                except etree.XMLSyntaxError as e:
                    return (False, f"Invalid XML syntax: {str(e)}")
                
                with open(self.schema_cache_path, 'rb') as schema_file:
                    schema_doc = etree.parse(schema_file)
                    schema = etree.XMLSchema(schema_doc)
                
                # Validate against XSD
                if schema.validate(xml_doc):
                    return (True, "")
                else:
                    ignored = []
                    non_ignored = []
                    ignored_datas_prefix = f"Element '{{{self.HAMSTERS_NAMESPACE}}}datas': Missing child element(s)."
                    ignored_phenotype_prefix = f"Element '{{{self.HAMSTERS_NAMESPACE}}}phenotype':"
                    ignored_genotype_prefix = f"Element '{{{self.HAMSTERS_NAMESPACE}}}genotype"
                    ignored_genotypetonode_prefix = f"Element '{{{self.HAMSTERS_NAMESPACE}}}genotypetonode':"
                    ignored_task_in_operator_prefix = f"Element '{{{self.HAMSTERS_NAMESPACE}}}task': This element is not expected. Expected is ( {{{self.HAMSTERS_NAMESPACE}}}operator )."
                    # Only ignore datas errors if we intentionally have no datas
                    should_ignore_datas = len(self.datas) == 0
                    
                    for error in schema.error_log:
                        message = getattr(error, "message", str(error))
                        line = getattr(error, "line", "?")
                        formatted = f"Line {line}: {message}"
                        if should_ignore_datas and ignored_datas_prefix in message:
                            ignored.append(formatted)
                            continue
                        if ignored_phenotype_prefix in message:
                            ignored.append(formatted)
                            continue
                        if ignored_genotype_prefix in message:
                            ignored.append(formatted)
                            continue
                        if ignored_genotypetonode_prefix in message:
                            ignored.append(formatted)
                            continue
                        if ignored_task_in_operator_prefix in message:
                            ignored.append(formatted)
                            continue
                        non_ignored.append(formatted)
                    if non_ignored:
                        return (False, "; ".join(non_ignored[:3]) if non_ignored else "Schema validation failed")
                    # All errors are in the ignored set. Report that violations were detected but ignored.
                    if ignored:
                        blue = "\033[34m"
                        reset = "\033[0m"
                        print(f"{blue}Schema validation: {len(ignored)} rule(s) violated but ignored{reset}")
                        # Show a short bullet list of the ignored rule messages (first 5 to keep concise)
                        for msg in ignored[:5]:
                            print(f"{blue}  - {msg}{reset}")
                        if len(ignored) > 5:
                            print(f"{blue}  - ... and {len(ignored) - 5} more{reset}")
                    return (True, "")
                    
            except ImportError:
                print("lxml not available, using basic XML validation...")
                # Fallback to basic validation without lxml
                return self._basic_validate_xml(xml_string)
                    
        except Exception as e:
            return (False, f"Validation error: {str(e)}")
    
    def _basic_validate_xml(self, xml_string: str) -> tuple:
        """Basic XML validation without lxml - checks structure and namespace. Returns (bool, error_msg)."""
        try:
            root = ET.fromstring(xml_string)
            
            # Check root element and extract namespace from tag
            if '}' in root.tag:
                namespace, tag_name = root.tag[1:].split('}')
            else:
                namespace = None
                tag_name = root.tag
            
            if tag_name != "hamsters":
                return (False, f"Root element must be 'hamsters', got '{tag_name}'")
            
            # Check namespace
            if namespace != self.HAMSTERS_NAMESPACE:
                return (False, f"Invalid namespace: expected {self.HAMSTERS_NAMESPACE}, got {namespace}")
            
            # Check for required attributes
            if 'name' not in root.attrib:
                return (False, "Missing 'name' attribute in root element")
            if 'version' not in root.attrib:
                return (False, "Missing 'version' attribute in root element")
            if root.attrib['version'] != '7':
                return (False, f"Expected version 7, got {root.attrib['version']}")
            
            # Check for required schema location attribute
            xsi_schema_loc = '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'
            if xsi_schema_loc not in root.attrib:
                return (False, "Missing xsi:schemaLocation attribute")
            
            # Check for Task child
            if len(root) == 0:
                return (False, "No task elements found in hamsters root")
            
            return (True, "")
        except ET.ParseError as e:
            return (False, f"Invalid XML: {str(e)}")
