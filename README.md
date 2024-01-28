# A Number Processing
This project provides a Python script for replacing A-numbers with unique IDs in `txt` and `xlsx` files. To maintain the correspondence between A-numbers and unique IDs between uses of the script a file is write to disk the first time, that is then loaded subsequent times. The script provides options for specifying the filepath of this serialization file, so that different A-number-to-unique-ID maps can be used when processing different files. See the scripts help instructions for details (`a_number_processing -h`).

## Set-up
To set-up a system for running this program:
- Install Python 3
- (Optional) create a Python environment: `python3 -m venv .venv`
    - Activate the python environment: `source ./.venv/bin/activate`
- Install the processing script: `pip install git+https://github.com/ellienorton/a_number_processing.git`

## Using the Python script
The above installation process makes the global command, `a_number_processing` avaiable. To get details on using the command one can use:

`a_number_processing -h`

An example usage of the command is:

`a_number_processing.py ./excel_file_to_process.xlsx`

To specify the path the the serialized "A-number-to-unique-ID" map when using the script one can use it as follows:

`a_number_processing ./excel_file_to_process.xlsx -s ./path/to/a_number_processing.pkl`
