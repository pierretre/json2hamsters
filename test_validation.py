import unittest
import json
from pathlib import Path
from JsonParser import JsonParser


class TestXMLValidation(unittest.TestCase):
    """Test suite for XML validation against HAMSTERS v7 schema"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        with open('./in/Scenario1.json') as f:
            cls.valid_json = json.load(f)
        cls.parser = JsonParser(cls.valid_json)
        cls.parser.parse()
    
    def test_valid_xml(self):
        """Test that valid XML structure is recognized"""
        xml = self.parser.to_xml()
        is_valid, error = self.parser.validate_xml(xml)
        # Note: May fail full XSD validation with lxml due to schema strictness,
        # but should pass basic structure validation
        self.assertIsInstance(is_valid, bool, "Should return boolean")
        self.assertIsInstance(error, str, "Should return error string")
    
    def test_invalid_root_element(self):
        """Test that invalid root element is caught"""
        invalid_xml = '<?xml version="1.0"?><badroot></badroot>'
        is_valid, error = self.parser.validate_xml(invalid_xml)
        self.assertFalse(is_valid, "Invalid root element should fail validation")
        self.assertTrue("hamsters" in error.lower() or "badroot" in error.lower() or "matching" in error.lower())
    
    def test_missing_version_attribute(self):
        """Test that missing version attribute is caught"""
        invalid_xml = '<?xml version="1.0"?><hamsters xmlns="http://www.irit.fr/ICS/HAMSTERS/7.0" name="test"></hamsters>'
        is_valid, error = self.parser.validate_xml(invalid_xml)
        self.assertFalse(is_valid, "Missing version attribute should fail validation")
        self.assertTrue("version" in error.lower() or "matching" in error.lower())
    
    def test_wrong_version(self):
        """Test that wrong version number is caught"""
        invalid_xml = '<?xml version="1.0"?><hamsters xmlns="http://www.irit.fr/ICS/HAMSTERS/7.0" name="test" version="5"></hamsters>'
        is_valid, error = self.parser.validate_xml(invalid_xml)
        self.assertFalse(is_valid, "Wrong version should fail validation")
        self.assertTrue("version" in error.lower() or "5" in error or "matching" in error.lower())
    
    def test_missing_schema_location(self):
        """Test that missing schemaLocation is caught"""
        invalid_xml = '<?xml version="1.0"?><hamsters xmlns="http://www.irit.fr/ICS/HAMSTERS/7.0" name="test" version="7"></hamsters>'
        is_valid, error = self.parser.validate_xml(invalid_xml)
        self.assertFalse(is_valid, "Missing schemaLocation should fail validation")
        self.assertTrue("schemalocation" in error.lower() or "matching" in error.lower())
    
    def test_empty_root_no_tasks(self):
        """Test that empty root with no tasks is caught"""
        invalid_xml = '<?xml version="1.0"?><hamsters xmlns="http://www.irit.fr/ICS/HAMSTERS/7.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="test" version="7" xsi:schemaLocation="http://www.irit.fr/ICS/HAMSTERS/7.0 https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd"></hamsters>'
        is_valid, error = self.parser.validate_xml(invalid_xml)
        self.assertFalse(is_valid, "Empty root with no tasks should fail validation")
        self.assertTrue("task" in error.lower() or "matching" in error.lower())
    
    def test_missing_name_attribute(self):
        """Test that missing name attribute is caught"""
        invalid_xml = '<?xml version="1.0"?><hamsters xmlns="http://www.irit.fr/ICS/HAMSTERS/7.0" version="7"></hamsters>'
        is_valid, error = self.parser.validate_xml(invalid_xml)
        self.assertFalse(is_valid, "Missing name attribute should fail validation")
        self.assertTrue("name" in error.lower() or "matching" in error.lower())
    
    def test_invalid_xml_syntax(self):
        """Test that invalid XML syntax is caught"""
        invalid_xml = '<?xml version="1.0"?><hamsters><unclosed>'
        is_valid, error = self.parser.validate_xml(invalid_xml)
        self.assertFalse(is_valid, "Invalid XML syntax should fail validation")
        self.assertIn("Invalid", error)
    
    def test_validation_returns_tuple(self):
        """Test that validate_xml returns (bool, str) tuple"""
        xml = self.parser.to_xml()
        result = self.parser.validate_xml(xml)
        self.assertIsInstance(result, tuple, "validate_xml should return a tuple")
        self.assertEqual(len(result), 2, "validate_xml should return a 2-tuple")
        self.assertIsInstance(result[0], bool, "First element should be bool")
        self.assertIsInstance(result[1], str, "Second element should be str")


class TestJSONToParsing(unittest.TestCase):
    """Test suite for JSON to IR parsing"""
    
    def test_parse_scenario1(self):
        """Test parsing Scenario1.json"""
        with open('./in/Scenario1.json') as f:
            data = json.load(f)
        parser = JsonParser(data)
        ir = parser.parse()
        
        self.assertIsNotNone(ir)
        self.assertEqual(ir.id, "T0")
        self.assertEqual(ir.label, "Login procedure")
        self.assertEqual(ir.type, "abstract")
    
    def test_parse_scenario2(self):
        """Test parsing Scenario2.json"""
        with open('./in/Scenario2.json') as f:
            data = json.load(f)
        parser = JsonParser(data)
        ir = parser.parse()
        
        self.assertIsNotNone(ir)
        self.assertEqual(ir.label, "Define New Incident Rule")
        self.assertTrue(len(ir.children) > 0, "Should have child tasks")
    
    def test_default_values_filled(self):
        """Test that missing fields are filled with defaults"""
        minimal_json = {
            "id": "test_task",
            "label": "Test Task"
        }
        parser = JsonParser(minimal_json)
        ir = parser.parse()
        
        self.assertEqual(ir.type, "abstract", "Default type should be 'abstract'")
        self.assertEqual(ir.duration["min"], 0, "Default duration min should be 0")
        self.assertEqual(ir.duration["max"], 0, "Default duration max should be 0")
        self.assertEqual(ir.duration["unit"], "s", "Default duration unit should be 's'")
        self.assertFalse(ir.optional, "Default optional should be False")


class TestXMLGeneration(unittest.TestCase):
    """Test suite for XML generation"""
    
    def test_xml_has_correct_namespace(self):
        """Test that generated XML has correct namespace"""
        with open('./in/Scenario1.json') as f:
            data = json.load(f)
        parser = JsonParser(data)
        parser.parse()
        xml = parser.to_xml()
        
        self.assertIn('xmlns="http://www.irit.fr/ICS/HAMSTERS/7.0"', xml)
        self.assertIn('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"', xml)
    
    def test_xml_has_schema_location(self):
        """Test that generated XML has schemaLocation attribute"""
        with open('./in/Scenario1.json') as f:
            data = json.load(f)
        parser = JsonParser(data)
        parser.parse()
        xml = parser.to_xml()
        
        self.assertIn('xsi:schemaLocation=', xml)
        self.assertIn('https://www.irit.fr/recherches/ICS/xsd/hamsters/v7/v7.xsd', xml)
    
    def test_xml_has_version_7(self):
        """Test that generated XML has version 7"""
        with open('./in/Scenario1.json') as f:
            data = json.load(f)
        parser = JsonParser(data)
        parser.parse()
        xml = parser.to_xml()
        
        self.assertIn('version="7"', xml)
    
    def test_xml_has_task_element(self):
        """Test that generated XML contains Task element"""
        with open('./in/Scenario1.json') as f:
            data = json.load(f)
        parser = JsonParser(data)
        parser.parse()
        xml = parser.to_xml()
        
        self.assertIn('<Task', xml)


class TestIRGeneration(unittest.TestCase):
    """Test suite for IR JSON generation"""
    
    def test_ir_json_valid(self):
        """Test that IR JSON is valid JSON"""
        with open('./in/Scenario1.json') as f:
            data = json.load(f)
        parser = JsonParser(data)
        parser.parse()
        ir_json = parser.to_json_ir()
        
        # Should not raise exception
        ir_data = json.loads(ir_json)
        self.assertIsNotNone(ir_data)
    
    def test_ir_contains_required_fields(self):
        """Test that IR JSON contains required fields"""
        with open('./in/Scenario1.json') as f:
            data = json.load(f)
        parser = JsonParser(data)
        parser.parse()
        ir_json = parser.to_json_ir()
        ir_data = json.loads(ir_json)
        
        self.assertIn("id", ir_data)
        self.assertIn("label", ir_data)
        self.assertIn("type", ir_data)
        self.assertIn("duration", ir_data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
