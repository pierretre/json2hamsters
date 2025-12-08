import json
import sys
import argparse
from pathlib import Path
from JsonParser import JsonParser
from json_schema import validate_json_schema

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert JSON task definitions to HAMSTERS v7 format",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", help="Input JSON file path")
    parser.add_argument("format", nargs="?", default="hmst",
                        choices=["hmst", "xml", "ir", "--hmst", "--xml", "--ir"],
                        help="Output format: hmst, xml, or ir (default: hmst)")
    parser.add_argument("-o", "--output", help="Output file path (overrides default generated/ location)")
    
    args = parser.parse_args()
    
    filepath = args.input
    # Normalize format (remove -- prefix if present)
    output_format = args.format.lstrip("-") if args.format else "hmst"
    custom_output = args.output
    
    # Ensure generated folder exists
    generated_dir = Path("generated")
    generated_dir.mkdir(exist_ok=True)
    
    try:
        # Read and parse JSON
        with open(filepath, 'r') as file:
            json_data = json.load(file)
        
        # Validate JSON schema
        is_valid, error_msg = validate_json_schema(json_data)
        if not is_valid:
            print(f"FAIL: JSON schema validation failed - {error_msg}")
            sys.exit(1)
        
        # Create parser and convert to IR
        parser = JsonParser(json_data)
        task_ir = parser.parse()
        
        # Get filename without extension for output
        input_filename = Path(filepath).stem
        
        # Output based on format
        if output_format in ("xml", "hmst"):
            xml_output = parser.to_xml()
            
            # Validate by default
            is_valid, error_msg = parser.validate_xml(xml_output)
            
            # Determine output file path
            if custom_output:
                output_file = Path(custom_output)
                # Create parent directories if needed
                output_file.parent.mkdir(parents=True, exist_ok=True)
            else:
                # Always write HAMSTER XML with .hmst extension (HAMSTERS format)
                output_file = generated_dir / f"{input_filename}.hmst"
            
            with open(output_file, 'w') as f:
                f.write(xml_output)
            
            if is_valid:
                print(f"OK - Output: {output_file}")
            else:
                print(f"FAIL: {error_msg}")
                sys.exit(1)
        elif output_format == "ir":
            ir_json = parser.to_json_ir()
            
            # Determine output file path
            if custom_output:
                output_file = Path(custom_output)
                # Create parent directories if needed
                output_file.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_file = generated_dir / f"{input_filename}_ir.json"
            
            with open(output_file, 'w') as f:
                f.write(ir_json)
            print(f"OK - Output: {output_file}")
        else:
            print("FAIL: Unknown format")
            sys.exit(1)
            
    except FileNotFoundError:
        print("FAIL: File not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON - {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: {str(e)}")
        sys.exit(1)