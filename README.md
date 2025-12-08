# JSON to HAMSTERS Converter

A Python parser that converts JSON task definitions to HAMSTERS v7 XML format with integrated IR (Intermediate Representation) and schema validation.

## Features

- ✅ **JSON to XML Conversion**: Converts JSON task definitions to HAMSTERS v7 XML format
- ✅ **Intermediate Representation**: Generates JSON IR with auto-filled default values
- ✅ **XML Schema Validation**: Validates against HAMSTERS v7 XSD schema (with lxml)
- ✅ **Comprehensive Testing**: 18 unit tests covering all major functionality
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

## Usage

### Convert JSON to XML (with validation)

```bash
python3 main.py ./in/Scenario1.json --xml
```

Output:

- **Console**: `OK` or `FAIL: <error message>`
- **File**: `generated/Scenario1.xml`

### Convert JSON to IR

```bash
python3 main.py ./in/Scenario2.json --ir
```

Output:

- **Console**: `OK`
- **File**: `generated/Scenario2_ir.json`

## Validation

When running with `--xml` format, validation is performed by default:

1. **With lxml installed**: Full XSD schema validation against HAMSTERS v7
   - Downloads schema from: `https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd`
   - Schema cached in: `/tmp/hamsters_v7.xsd`
   - Shows detailed error messages

2. **Without lxml**: Basic XML structure validation
   - Checks root element, namespace, and required attributes
   - Checks for Task children

### Example Output

```
Using lxml for full schema validation...
Using cached schema: /tmp/hamsters_v7.xsd (24461 bytes)
OK
```

Or on validation failure:

```
Using lxml for full schema validation...
Downloading HAMSTERS schema from https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd...
Schema downloaded successfully: /tmp/hamsters_v7.xsd (24461 bytes)
FAIL: Line 2: Element 'hamsters': No matching global declaration available for the validation root.
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

```
json2hamsters/
├── JsonParser.py          # Main parser and validator
├── main.py                # CLI entry point
├── test_validation.py     # Unit tests (18 tests)
├── requirements.txt       # Python dependencies
├── in/                    # Input JSON files
│   ├── Scenario1.json
│   └── Scenario2.json
├── generated/             # Output files (XML, IR JSON)
└── venv/                  # Virtual environment
```

## HAMSTERS Model

The parser supports the following HAMSTERS task model elements:

- **Task Types**: abstract, user, system, cognitive, interaction, cooperative
- **Temporal Operators**: sequence, choice, concurrency, order-independent, loop, optional, interrupt, suspend_resume
- **Duration**: min, max, unit (ms, s, min, h)
- **Children**: Nested task hierarchies
- **Loop Configuration**: minIterations, maxIterations
- **Metadata**: Free-form additional attributes

## Example Input (JSON)

```json
{
  "id": "root_task",
  "label": "Make Coffee",
  "type": "user",
  "operator": "sequence",
  "duration": {
    "min": 5,
    "max": 10,
    "unit": "min"
  },
  "children": [
    {
      "id": "boil_water",
      "label": "Boil Water",
      "type": "system"
    }
  ]
}
```

## Example Output (XML)

```xml
<?xml version="1.0"?>
<hamsters xmlns="http://www.irit.fr/ICS/HAMSTERS/7.0" 
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          name="Make Coffee"
          version="7"
          xsi:schemaLocation="http://www.irit.fr/ICS/HAMSTERS/7.0 https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd">
  <Task id="root_task" type="user">
    <Label>Make Coffee</Label>
    <Duration unit="min">
      <Min>5</Min>
      <Max>10</Max>
    </Duration>
    <Operator>sequence</Operator>
    <Children>
      <Task id="boil_water" type="system">
        <Label>Boil Water</Label>
        <Duration unit="s">
          <Min>0</Min>
          <Max>0</Max>
        </Duration>
      </Task>
    </Children>
  </Task>
</hamsters>
```

## Schema Information

- **Version**: HAMSTERS v7
- **Namespace**: `http://www.irit.fr/ICS/HAMSTERS/7.0`
- **Schema URL**: `https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd`
- **Cache Location**: `/tmp/hamsters_v7.xsd`

## License

MIT
