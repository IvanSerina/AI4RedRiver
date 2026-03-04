import re
from datetime import datetime
from unified_planning.shortcuts import Object
class StringHelper(object):
    """StringHelper it is a utility class to help with the string representation"""
    
    @staticmethod
    def replace_scientific_notation_decimal(file_path : str):
        with open(file_path, 'r') as file:
            file_content = file.read()
        # Define pattern to match floats in scientific notation
        float_pattern = r'\b\d+(\.\d+)?[Ee][+-]?\d+\b'
        # Find all floats in scientific notation and replace them with their decimal representation
        modified_text = re.sub(float_pattern, lambda match : '{:.20f}'.format(float(match.group(0))), file_content)
        with open(file_path, 'w') as file:
            file.write(modified_text)
    
    @staticmethod
    def replace_regex_in_text_file(file_path, target_regex, replacement_string):
        with open(file_path, 'r') as file:
            file_content = file.read()
        pattern = re.compile(target_regex)
        modified_content = pattern.sub(replacement_string, file_content)
        with open(file_path, 'w') as file:
            file.write(modified_content)
    
    @staticmethod
    def convert_PDDL_date_object_into_datetime(date_object : Object):
        time_step_regex = re.compile(r"(day|month|week)_(\d{4}_\d{2}_\d{2})")
        date_str = time_step_regex.search(date_object.name).group(2) # We check which is the last day
        date = datetime.strptime(date_str, '%Y_%m_%d')
        return date