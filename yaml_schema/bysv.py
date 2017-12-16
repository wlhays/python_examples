'''
Basic YAML Schema Validation (via JSON)
load schema.yml
convert to json 
load config.yml
convert to json, then validate and pass through or raise exception

'''
import json
import yaml
import jsonschema, jsonschema.exceptions
import sys

def is_valid_config(schema, config):
    
    try:    
        jsonschema.Draft4Validator.check_schema(schema)    
    except jsonschema.exceptions.SchemaError as e:
        print(e) 
        return False
    print('schema is valid')

    try:
        jsonschema.validate(config, schema)
    except jsonschema.exceptions.ValidationError as e:
        print(e) 
        return False
    except Exception as e2:
        print('e2: ', e2)
        return False    

    return True
    
    
def main(schema_file_path, config_file_path):

    try:
        with open(schema_file_path) as f_schema:
            schema = yaml.safe_load(f_schema)
        with open(config_file_path) as f_config:
            config = yaml.safe_load(f_config)                
    except OSError as e:  
        print(e)  

    print('loaded schema.yml and config.yml')
    
    if is_valid_config(schema, config):
        print('config is valid')
            
        
if __name__ == "__main__":
    if len(sys.argv) == 3:            
        main(sys.argv[1], sys.argv[2])        
    else:    
        print('Usage:  bysv <schema.yml> <config.yml>')
 