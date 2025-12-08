import json
import sys
from pathlib import Path
from JsonParser import JsonParser
from json_schema import validate_json_schema

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <input.json> [--hmst|--xml|--ir]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "--hmst"
    
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
        if output_format in ("--xml", "--hmst"):
            xml_output = parser.to_xml()
            
            # Validate by default
            is_valid, error_msg = parser.validate_xml(xml_output)
            
            # Always write HAMSTER XML with .hmst extension (HAMSTERS format)
            output_file = generated_dir / f"{input_filename}.hmst"
            with open(output_file, 'w') as f:
                f.write(xml_output)
            
            if is_valid:
                print(f"OK - Output: {output_file}")
            else:
                print(f"FAIL: {error_msg}")
                sys.exit(1)
        elif output_format == "--ir":
            ir_json = parser.to_json_ir()
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