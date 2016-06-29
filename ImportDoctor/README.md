# Installation
pip install ImportDoctor
# Usage
`from ImportDoctor import ImportDoctor`
### Basic
`ImportDoctor.run(filename)`
### Advanced
This example creates a doctor and changes the settings to be pep8 compliant [*read* ugly].
Then it analyzes a file, pulling all information into the class. Finally we sort the imports and write all of the data to a destination file.
```
doc = ImportDoctor()
doc.order_alphabetically = True
doc.wrap_depth = 79
doc.wrap_strict = True
doc.comment_names = False
doc.analyze(filename)
doc.sort_imports()
doc.remap(destination_filename)
```
### Controls
The following is a list of all controls meant to be used externally.
I have included their default values (see code for regex patterns) as well as a brief description. More to come eventually.
```
ignore_indented = True      # Grabs indented imports if false
group_by_module_type = True # Separates system modules from local ones
descending = True           # Primary order on sort: True => BIG to small
one_import_per_line = True  # Separates grouped imports onto their own lines
exclude_from = True         # Sort on string before 'import' for 'from' imports
import_ontop = True         # Place all 'from' imports below standard imports
wrap_strict = False         # If true, wrap_depth will be strictly enforced
wrap_depth = 0              # If > 25, lines will be wrapped using a backslash
comment_names = True        # If true, groups will be named in comments above group
order_alphabetically = False# If true, imports are sortend alphabetically, not on length
regex_find_import = ...     # The compiled regular expression for finding lines like 'import A'
regex_find_from = ...       # The compiled regular expression for finding like 'from A import B'
isolated_groups = []        # A list of modules that will be grouped and sorted separately from other imports
```
