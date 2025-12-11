import json
import sys
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from HmstParser import HmstParser
from json_schema import validate_json_schema

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert HAMSTERS v7 .hmst files back to JSON format",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", help="Input .hmst file path")
    parser.add_argument("-o", "--output", help="Output JSON file path (overrides default generated/ location)")
    parser.add_argument("--no-validate", action="store_true", help="Skip JSON schema validation")
    
    args = parser.parse_args()
    
    filepath = args.input
    custom_output = args.output
    skip_validation = args.no_validate
    
    # Ensure generated folder exists
    generated_dir = Path("generated")
    generated_dir.mkdir(exist_ok=True)
    
    try:
        # Parse HMST file
        hmst_parser = HmstParser(filepath)
        json_data = hmst_parser.parse()
        
        # Add refs from datas to tasks
        hmst_parser.add_refs_from_datas()
        
        # Validate JSON schema (unless skipped)
        if not skip_validation:
            is_valid, error_msg = validate_json_schema(json_data)
            if not is_valid:
                print(f"FAIL: JSON schema validation failed - {error_msg}")
                sys.exit(1)
        
        # Determine output file path
        if custom_output:
            output_file = Path(custom_output)
            # Create parent directories if needed
            output_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Default: write to generated/ with .json extension
            input_filename = Path(filepath).stem
            output_file = generated_dir / f"{input_filename}.json"
        
        # Write JSON output
        json_output = json.dumps(json_data, indent=2)
        with open(output_file, 'w') as f:
            f.write(json_output)
        
        green_bold = "\033[1;32m"
        reset = "\033[0m"
        print(f"{green_bold}OK - Output: {output_file}{reset}")
        
    except FileNotFoundError:
        print("FAIL: File not found")
        sys.exit(1)
    except ET.ParseError as e:
        print(f"FAIL: Invalid XML - {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
