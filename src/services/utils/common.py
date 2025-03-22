import re
import json
from typing import List, Dict, Optional,Union







# Helper functions
def clean_json_string(json_str: str) -> str:
    json_str = re.sub(r'```(?:json)?\s*|\s*```', '', json_str)
    fixed_str = ''
    in_string = False
    escape_next = False
    
    for char in json_str:
        fixed_str += char
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
        elif char == '"' and not escape_next:
            in_string = not in_string
    
    if in_string:
        fixed_str += '"'
    
    open_braces = fixed_str.count('{')
    close_braces = fixed_str.count('}')
    open_brackets = fixed_str.count('[')
    close_brackets = fixed_str.count(']')
    
    fixed_str += '}' * (open_braces - close_braces)
    fixed_str += ']' * (open_brackets - close_brackets)
    
    return fixed_str

def extract_and_parse_json(json_str: str) -> Dict:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        cleaned_json = clean_json_string(json_str)
        try:
            return json.loads(cleaned_json)
        except json.JSONDecodeError:
            match = re.search(r'({.*})', json_str, re.DOTALL)
            if match:
                try:
                    extracted_json = match.group(1)
                    cleaned_extracted = clean_json_string(extracted_json)
                    return json.loads(cleaned_extracted)
                except json.JSONDecodeError:
                    raise
            else:
                raise