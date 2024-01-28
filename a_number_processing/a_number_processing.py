from copy import copy
import argparse
import re
import pickle
import pathlib
import pandas as pd

A_NUMBER_PATTERN = r'[aA]?((?<=[aA])[-\t ])?#?((?<=#)[-\t ])?[0-9]{2,3}[- ]?[0-9]{3}[- ]?[0-9]{3}\b'
A_NUMBER_PATTERN_SIMPLE = r'[0-9]{2,3}[- ]?[0-9]{3}[- ]?[0-9]{3}\b'
A_NUMBER_REGEX = re.compile(A_NUMBER_PATTERN)
MODIFIED_FILE_SUFFIX = '_redacted'
DEFAULT_SERIALIZATION_PATH = './a_number_to_uid.pkl'
REPLACEMENT_UID_PREFIX = 'UID-'
READ_ALL_SHEETS=None
ALL_COLUMN_NUMBERS = slice(None)


class UIDGenerator:
    def __init__(self, current_largest_uid = -1):
        self.next_uid = current_largest_uid + 1
    
    def get_next_uid(self):
        next_uid = copy(self.next_uid)
        self.next_uid += 1
        return next_uid

def retrieve_a_number_to_uid_map(serialization_path):
    try:
        with open(serialization_path, 'rb') as f:
            a_number_to_uid = pickle.load(f)
            return a_number_to_uid
    except FileNotFoundError:
        print(f"Couldn't open serialization file, {serialization_path}. Creating a new a-number to UID map.")
        return {}

def store_a_number_to_uid_map(serialization_path, a_number_to_uid):
    with open(serialization_path, 'wb') as f:
        pickle.dump(a_number_to_uid, f)

def canonicalize(a_number):
    result = a_number.lower()
    result = re.sub(r'[a\-# ]', '', result)
    if len(result) == 8:
        result = '0' + result
    return result

def replace_text_a_numbers(a_number_to_uid, uid_generator, text):
    def replace(raw_match):
        a_number = canonicalize(raw_match.group(0))
        assert(len(a_number) == 9)
        if a_number not in a_number_to_uid:
            a_number_to_uid[a_number] = uid_generator.get_next_uid()
        return REPLACEMENT_UID_PREFIX + str(a_number_to_uid[a_number])

    return A_NUMBER_REGEX.sub(replace, text)

def replace_document_a_numbers(a_number_to_uid, uid_generator, input_file_path, selected_column_numbers):
    assert(selected_column_numbers is None or len(selected_column_numbers) > 0)
    input_file_extension = input_file_path.suffix
    output_file_path = f"{input_file_path.stem}{MODIFIED_FILE_SUFFIX}{input_file_extension}"

    if input_file_extension == '.txt':
        with open(input_file_path, 'r') as f:
            text = f.read()

        modified_text = replace_text_a_numbers(a_number_to_uid, uid_generator, text)

        with open(output_file_path, 'w') as f:
            f.write(modified_text)

    elif input_file_extension == '.xlsx':
        sheets = pd.read_excel(input_file_path, sheet_name=READ_ALL_SHEETS, header=None)
        
        for (sheet_name, sheet) in sheets.items():

            columns_to_select = ALL_COLUMN_NUMBERS if selected_column_numbers is None else selected_column_numbers
            selected_columns = sheet.loc[:, columns_to_select]

            for (column_name, column_data) in selected_columns.items():
                for (row_number, cell_contents) in column_data.items():
                    if isinstance(cell_contents, str):
                        sheet.at[row_number, column_name] = replace_text_a_numbers(a_number_to_uid, uid_generator, cell_contents)
                    elif isinstance(cell_contents, int):
                        sheet.at[row_number, column_name] = replace_text_a_numbers(a_number_to_uid, uid_generator, str(cell_contents))
        
        with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
            for (sheet_name, sheet) in sheets.items():
                sheet.to_excel(writer, sheet_name=sheet_name, index=False, header=None)
        
    else:
        print("ERROR: file format not supported")


def main():
    parser = argparse.ArgumentParser(prog='a_number_processing',
                                     description='Replaces A-numbers with unique IDs.')
    parser.add_argument('file_to_process', type=pathlib.Path, help='The file path of a \'txt\' or \'xlsx\' to process.')
    parser.add_argument('-s', '--serialization_path', type=pathlib.Path, default=DEFAULT_SERIALIZATION_PATH, help=f'The file path to serialized a-number-to-uid map, without this option the default is {DEFAULT_SERIALIZATION_PATH}')
    parser.add_argument('-cn', '--column_numbers', nargs='+', type=int, default=None, help='Select the column numbers that should be processed. Columns are counted starting from 0 for the first column. If this option is not provided then the program processes all columns.')
    args = parser.parse_args()

    a_number_to_uid = retrieve_a_number_to_uid_map(args.serialization_path)

    current_largest_uid = -1 if not a_number_to_uid else max(a_number_to_uid.values())
    uid_generator = UIDGenerator(current_largest_uid)

    replace_document_a_numbers(a_number_to_uid, uid_generator, args.file_to_process, args.column_numbers)

    store_a_number_to_uid_map(args.serialization_path, a_number_to_uid)
