# JSON to HAMSTERS Converter

A Python parser that converts JSON task definitions to HAMSTERS v7 XML format (.hmst files) with integrated IR (Intermediate Representation) and schema validation.

## Features

- ✅ **JSON to HAMSTERS Conversion**: Converts JSON task definitions to HAMSTERS v7 XML format (.hmst)
- ✅ **JSON Schema Validation**: Validates input JSON against strict schema (prevents invalid/excessive elements)
- ✅ **Auto Task IDs**: Automatically generates lowercase task IDs (t0, t1, t2...) if not provided
- ✅ **Operator Nesting**: Operators nest their children tasks within the XML structure
- ✅ **Intermediate Representation**: Generates JSON IR with auto-filled default values
- ✅ **XML Schema Validation**: Validates against HAMSTERS v7 XSD schema (with lxml)
- ✅ **Empty datas Section**: Generates `<datas/>` (empty by design, validation error ignored)
- ✅ **Clean Output**: Minimal console output (OK/FAIL status only)

## Setup

### 1. Create and Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:

- `lxml` (6.0.0+) - For full XSD schema validation
- `jsonschema` (4.0.0+) - For input JSON schema validation

## Usage

### Convert JSON to HAMSTERS format (default)

```bash
python3 main.py ./in/Scenario1.json
# or explicitly
python3 main.py ./in/Scenario1.json --hmst
```

Output:

- **Console**: `OK - Output: generated/Scenario1.hmst` or `FAIL: <error message>`
- **File**: `generated/Scenario1.hmst` (HAMSTERS v7 XML format)

### Convert JSON to XML (legacy)

```bash
python3 main.py ./in/Scenario1.json --xml
```

Output: Same as `--hmst` (both produce `.hmst` files)

### Convert JSON to IR

```bash
python3 main.py ./in/Scenario2.json --ir
```

Output:

- **Console**: `OK - Output: generated/Scenario2_ir.json`
- **File**: `generated/Scenario2_ir.json`

## Validation

### JSON Schema Validation

All input JSON files are automatically validated against a strict schema before processing:

**Allowed properties:**

- `label` (required, string, 1-200 chars)
- `id` (optional, string, alphanumeric + underscore/hyphen)
- `type` (optional, enum: abstract, goal, user, system, cognitive, interaction, cooperative)
- `description` (optional, string, max 1000 chars)
- `operator` (optional, enum: sequence, choice, order-independent, concurrency, loop, optional, interrupt, suspend_resume)
- `duration` (optional, object: min/max 0-1000000, unit: ms/s/min/h)
- `loop` (optional, object: minIterations/maxIterations 0-10000)
- `optional` (optional, boolean)
- `children` (optional, array, max 100 items)
- `metadata` (optional, object, max 50 properties)
- `datas` (optional, array of data objects - DOD, max 100 items)

**Strict mode:** `additionalProperties: false` - No unknown properties allowed

**Example validation failure:**

```text
FAIL: JSON schema validation failed - root: Additional properties are not allowed ('invalid_field' was unexpected)
```

### XML Schema Validation

When running with `--hmst` or `--xml` format, XML validation is performed after generation:

1. **With lxml installed**: Full XSD schema validation against HAMSTERS v7
   - Downloads schema from: `https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd`
   - Schema cached in: `/tmp/hamsters_v7.xsd`
   - Shows detailed error messages
   - **Special handling**: Validation errors about empty `<datas/>` are ignored when no datas are provided

2. **Without lxml**: Basic XML structure validation
   - Checks root element, namespace, and required attributes
   - Checks for Task children

### Example Output

```text
Using lxml for full schema validation...
Using cached schema: /tmp/hamsters_v7.xsd (24461 bytes)
Schema validation warnings ignored for empty <datas /> block.
OK - Output: generated/Scenario1.hmst
```

Or on validation failure:

```text
Using lxml for full schema validation...
Downloading HAMSTERS schema from https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd...
Schema downloaded successfully: /tmp/hamsters_v7.xsd (24461 bytes)
FAIL: Line 12: Element 'task': Missing required attribute 'type'
```

## Testing

Run the full test suite:

```bash
source venv/bin/activate
python3 -m unittest test_validation -v
```

### Test Coverage

- **TestXMLValidation**: 9 tests
  - Valid XML, invalid root, missing attributes, wrong version, empty root, invalid syntax
  
- **TestJSONToParsing**: 3 tests
  - Parsing Scenario1 & 2, default value filling
  
- **TestXMLGeneration**: 4 tests
  - Namespace, schemaLocation, version, Task element
  
- **TestIRGeneration**: 2 tests
  - JSON validity, required fields

Total: **18 tests** ✅

## File Structure

```text
json2hamsters/
├── JsonParser.py               # Main parser and validator
├── json_schema.py              # JSON schema definition and validator
├── hamsters-task.schema.json  # JSON Schema for IDE autocomplete
├── main.py                     # CLI entry point
├── test_validation.py          # Unit tests (18 tests)
├── requirements.txt            # Python dependencies
├── in/                         # Primary scenario files
│   ├── Scenario1.json          # Consult incidents (with statistics & history)
│   └── Scenario2.json          # Define new incident rule
├── examples/                   # Additional examples and test cases
│   ├── scenario.json           # Copy of Scenario2
│   ├── with_datas.json         # Example with data objects (DOD)
│   ├── with_errors.json        # Example with error model
│   ├── valid_children.json     # Example with nested children
│   ├── invalid_schema.json     # Test case: extra properties (rejected)
│   └── invalid_duration.json   # Test case: invalid values (rejected)
├── generated/                  # Output files (.hmst, IR JSON)
│   ├── Scenario1.hmst
│   └── Scenario2.hmst
└── venv/                       # Virtual environment
```

## HAMSTERS Model

The parser supports the following HAMSTERS task model elements:

### Task Properties

- **Task Types**: abstract, goal, user, system, cognitive, interaction, cooperative
  - Root task defaults to `goal` if type not specified
  - Child tasks default to `abstract` if type not specified
- **Auto IDs**: Task IDs are auto-generated (t0, t1, t2...) if not provided in JSON
- **Labels**: Task labels (required, used as `name` in hamsters root)
- **Description**: Task descriptions (optional)
- **Optional**: Tasks can be marked as optional

### Operators and Structure

- **Temporal Operators**: sequence, choice, order-independent, loop (operators nest children)
- **Operator Nesting**: When a task has operator + children, the operator wraps the children in XML
- **Duration**: min, max, unit (default: 0, 0, s)
- **Loop Configuration**: minIterations, maxIterations

### Generated XML Structure

- **Namespace**: `https://www.irit.fr/ICS/HAMSTERS/7.0`
- **Root Elements**: nodes, datas (populated if provided), errors, security, parameters, instancevalues, parametersdefinitions, mainproperties
- **Core Properties**: simulation, authority, criticality categories with default values
- **Graphics**: Position elements (x=0, y=0) for all tasks and operators

### Data Objects (DOD - Description of Data)

Optional `datas` array allows modeling data manipulated by tasks:

- **Data Types**:
  - `objectdod` - Domain objects (e.g., "City DT", "User Profile")
  - `informationdod` - Information elements (e.g., "Status", "Message")
  - `deviceouputdod` - Output devices (e.g., "Screen", "Speaker")
  - `deviceinputdod` - Input devices (e.g., "Keyboard", "Mouse")

- **Links to Tasks**: Define how tasks interact with data
  - `ACCESS_TYPE` - Task reads/accesses the data
  - `STORE_TYPE` - Task writes/stores the data
  - `USES_TYPE` - Task uses a device
  - `MODIFY_TYPE` - Task modifies the data

- **Properties**:
  - `id` (auto-generated as a0, a1, a2... if not provided)
  - `type` (required)
  - `description` (required)
  - `links` (array of {taskId, linkType})
  - `position` (x, y coordinates for graphical layout)

**Example:**

```json
"datas": [
  {
    "id": "a1",
    "type": "objectdod",
    "description": "City DT",
    "links": [{"taskId": "t1", "linkType": "ACCESS_TYPE"}],
    "position": {"x": 950, "y": 61}
  }
]
```

### Error Model (Errorconnectors, Phenotypes, Genotypes)

Optional `errors` object allows modeling error analysis per HAMSTERS methodology:

**Error Connectors** - Logic gates combining errors:

- `id` (auto-generated as e0, e1, e2... if not provided)
- `name` (connector name)
- `type` (enum: "OR", "AND")
- `position` (x, y coordinates)

**Phenotypes** - Observable error manifestations:

- `id` (unique identifier)
- `name` (phenotype name)
- `type` (enum: "humanerror", "systemerror", "designerror")
- `position` (x, y coordinates)
- `links` (array of {connectorId} - connections to error connectors)

**Genotypes** - Root causes of errors:

- `id` (unique identifier)
- `name` (genotype name)
- `type` (enum: "slip", "lapse", "mistake", "rbm")
- `gemstype` (enum: "Undefined", "Routine", "Familiar", "Unfamiliar")
- `position` (x, y coordinates)
- `phenotypeLinks` (array of {phenotypeId} - connections to phenotypes)
- `taskLinks` (array of {taskId} - affected tasks)

**Example:**

```json
"errors": {
  "errorconnectors": [
    {"id": "e3", "name": "", "type": "OR", "position": {"x": -56, "y": 808}}
  ],
  "phenotypes": [
    {"id": "e2", "name": "Type in wrong postalcode", "type": "humanerror", "position": {"x": -248, "y": 732}, "links": [{"connectorId": "e3"}]}
  ],
  "genotypes": [
    {"id": "e4", "name": "Typing Slip", "type": "slip", "gemstype": "Undefined", "position": {"x": -177, "y": 1116}, "phenotypeLinks": [{"phenotypeId": "e2"}], "taskLinks": [{"taskId": "t15"}]}
  ]
}
```

## Example Input (JSON)

```json
{
  "label": "Login Procedure",
  "description": "User authentication workflow",
  "operator": "sequence"
}
```

Note:

- No explicit `id` → Auto-generated as `t0`
- No explicit `type` → Defaults to `goal` (root task)
- No `children` → Single task scenario
- `operator` is specified but has no children (valid)

## Example Output (.hmst / HAMSTERS XML)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<hamsters xmlns="https://www.irit.fr/ICS/HAMSTERS/7.0" 
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
          name="Login Procedure" 
          version="7" 
          xsi:schemaLocation="https://www.irit.fr/ICS/HAMSTERS/7.0 https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd">
    <nodes>
        <task id="t0" type="goal" copy="false" knowledgeproceduraltype="">
            <graphics>
                <graphic folded="false">
                    <position x="0" y="0"/>
                </graphic>
            </graphics>
            <description>User authentication workflow</description>
            <xlproperties/>
            <coreproperties>
                <categories>
                    <category name="simulation">
                        <property name="duration" value="false"/>
                        <property name="iterative" value="0"/>
                        <property name="optional" value="false"/>
                        <property name="minexectime" value="0"/>
                        <property name="maxexectime" value="0"/>
                    </category>
                    <category name="authority">
                        <property name="responsibility" type="java.lang.Boolean" value="false"/>
                        <property name="authority" type="java.lang.Boolean" value="false"/>
                    </category>
                    <category name="criticality">
                        <property name="criticality" type="java.lang.Integer" value="0"/>
                    </category>
                </categories>
            </coreproperties>
        </task>
    </nodes>
    <datas/>
    <errors/>
    <security/>
    <parameters/>
    <instancevalues/>
    <parametersdefinitions/>
    <mainproperties>
        <property name="timemanagement" type="fr.irit.ics.circus.hamsters.api.TimeManagement" value="NORMAL"/>
    </mainproperties>
</hamsters>
```

## Schema Information

- **Version**: HAMSTERS v7
- **Namespace**: `https://www.irit.fr/ICS/HAMSTERS/7.0` (HTTPS)
- **Schema URL**: `https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd`
- **Cache Location**: `/tmp/hamsters_v7.xsd`
- **Output Extension**: `.hmst` (HAMSTERS format)

## Implementation Notes

- **JSON Schema Validation**: Input JSON is validated before parsing; unknown properties and invalid values are rejected
- **Data Objects (DOD)**: Optional `datas` array in JSON generates HAMSTERS data elements with types (objectdod, informationdod, deviceouputdod, deviceinputdod), links to tasks (ACCESS_TYPE, STORE_TYPE, USES_TYPE, MODIFY_TYPE), and graphical positions
- **Empty datas**: When no `datas` are provided, `<datas/>` is empty and XSD validation errors are suppressed
- **Operator nesting**: When a task has both an `operator` and `children`, the operator element contains the child tasks
- **Default types**: Root tasks default to `goal`, all other tasks default to `abstract` (unless explicitly specified)
- **Auto-generated IDs**: Task and operator IDs are generated sequentially (t0, t1..., o0, o1...) in lowercase
- **Limits**: Max 100 children per task, max 50 metadata properties, durations 0-1000000, iterations 0-10000

## License

MIT
