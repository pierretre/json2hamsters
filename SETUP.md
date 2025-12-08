# Setup Instructions

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run tests to verify setup
python3 -m unittest test_validation -v

# 5. Convert a JSON file
python3 main.py ./in/Scenario1.json --xml
```

## What Was Set Up

✅ **Virtual Environment**: `venv/` directory with Python 3.12
✅ **lxml Installed**: Full XSD schema validation support
✅ **Schema Downloads**: Automatically cached at `/tmp/hamsters_v7.xsd`
✅ **Unit Tests**: All 18 tests passing
✅ **Documentation**: Complete README.md

## Validation Features

### Schema Download & Caching
- First run: Downloads schema (24461 bytes) from official source
- Subsequent runs: Uses cached version
- Validates before use: Reports if empty

### Error Messages
- Shows validation step (lxml vs basic validation)
- Shows schema cache info (size in bytes)
- Reports specific validation failures

### Example Output
```
Using lxml for full schema validation...
Using cached schema: /tmp/hamsters_v7.xsd (24461 bytes)
FAIL: Line 2: Element '{http://www.irit.fr/ICS/HAMSTERS/7.0}hamsters': No matching global declaration...
```

## Project Files

- `JsonParser.py` - Core parser and validator (240+ lines)
- `main.py` - CLI interface with validation
- `test_validation.py` - 18 comprehensive unit tests
- `requirements.txt` - Python dependencies
- `README.md` - Full documentation
- `SETUP.md` - This file
- `venv/` - Virtual environment with lxml installed

## Deactivate Virtual Environment

When done:
```bash
deactivate
```

## Troubleshooting

**Schema download fails?**
- Check internet connectivity
- Schema URL: https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd

**Tests failing?**
- Ensure venv is activated: `source venv/bin/activate`
- Ensure lxml installed: `pip install lxml`

**JSON conversion failing?**
- Ensure venv is activated
- Check JSON syntax in input files
- Run with `--xml` for validation output
