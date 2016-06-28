import re

class ImportNurse(object):
    ignore_indented = True      # Grabs indented imports
    alpha_order = False         # Sorts by alphabetical instead of length
    group_by_module_type = True # Separates system modules from local ones
    descending = True           # Primary order on sort: True => BIG to small
    one_import_per_line = True  # Separates grouped imports onto their own lines
    exclude_from = True         # Sort on string before 'import' for 'from' imports
    import_ontop = True         # Place all 'from' imports below standard imports
    wrap_strict = False         # If true, wrap_depth will be strictly enforced
    
    # These variables are controlled through getters and setters.
    _newline_padding = 1        # How many empty lines after end of imports
    _isolation = []             # Groups of imports to separate by name
    _wrap_depth = 0             # The character count at which line wrapping begins
    
    def __init__(self, **kwargs):
        if not set(kwargs.keys()) <= self.__vars__():
            raise ValueError('Unexpected arguements passed.')
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
    
    def __vars__(self):
        return set([x for x in dir(self) if not x.startswith('__') 
                    and not callable(getattr(self, x))])
    
    @property
    def wrap_depth(self):
        return self._wrap_depth
    
    @wrap_depth.setter
    def wrap_depth(self, value):
        if type(value) is not int:
            raise ValueError('wrap_depth must be integer')
        if value < 25:
            raise ValueError('There is no reason to wrap code at 25 characters or less')
        self._wrap_depth = value
       
    @property
    def newline_padding(self):
        return self._newline_padding
    
    @newline_padding.setter
    def newline_padding(self, value):
        if type(value) is not int:
            raise ValueError('newline_padding must be an integer')
        if value < 0:
            raise ValueError('Padding must be a positive value')
        self._newline_padding = value
        
    @property
    def isolated_groups(self):
        return self._isolation[:]
    
    @isolated_groups.setter
    def isolated_groups(self, value):
        if type(value) is not list:
            raise ValueError('isolated_groups must be a list of module names')
        self._isolation = value[:]

builtin_python_modules = [
    'string', 're', 'difflib', 'textwrap', 'unicodedata', 'stringprep', 'readline', 
    'rlcompleter', 'struct', 'codecs', 'datetime', 'calendar', 'collections', 
    'collections', 'heapq', 'bisect', 'array', 'weakref', 'types', 'copy', 'pprint', 
    'reprlib', 'enum', 'numbers', 'math', 'cmath', 'decimal', 'fractions', 'random', 
    'statistics', 'itertools', 'functools', 'operator', 'pathlib', 'os', 'fileinput', 
    'stat', 'filecmp', 'tempfile', 'glob', 'fnmatch', 'linecache', 'shutil', 'macpath', 
    'pickle', 'copyreg', 'shelve', 'marshal', 'dbm', 'sqlite', 'zlib', 'gzip', 'bz', 
    'lzma', 'zipfile', 'tarfile', 'csv', 'configparser', 'netrc', 'xdrlib', 'plistlib', 
    'hashlib', 'hmac', 'os', 'io', 'time', 'argparse', 'getopt', 'logging', 'logging', 
    'logging', 'getpass', 'curses', 'curses', 'curses', 'curses', 'platform', 'errno', 
    'ctypes', 'threading', 'multiprocessing', 'concurrent', 'subprocess', 'sched', 'queue', 
    'dummy', 'socket', 'ssl', 'select', 'selectors', 'asyncio', 'asyncore', 'asynchat', 
    'signal', 'mmap', 'email', 'json', 'mailcap', 'mailbox', 'mimetypes', 'base', 
    'binhex', 'binascii', 'quopri', 'uu', 'html', 'html', 'html', 'xml', 'xml', 
    'xml', 'xml', 'xml', 'xml', 'xml', 'xml', 'xml', 'webbrowser', 'cgi', 'cgitb', 
    'wsgiref', 'urllib', 'urllib', 'urllib', 'urllib', 'urllib', 'urllib', 'http', 
    'http', 'ftplib', 'poplib', 'imaplib', 'nntplib', 'smtplib', 'smtpd', 'telnetlib', 
    'uuid', 'socketserver', 'http', 'http', 'http', 'xmlrpc', 'xmlrpc', 'xmlrpc', 
    'ipaddress', 'audioop', 'aifc', 'sunau', 'wave', 'chunk', 'colorsys', 'imghdr', 
    'sndhdr', 'ossaudiodev', 'gettext', 'locale', 'turtle', 'cmd', 'shlex', 'tkinter', 
    'tkinter', 'tkinter', 'tkinter', 'typing', 'pydoc', 'doctest', 'unittest', 'unittest', 
    'unittest', 'test', 'test', 'bdb', 'faulthandler', 'pdb', 'timeit', 'trace', 
    'tracemalloc', 'distutils', 'ensurepip', 'venv', 'zipapp', 'sys', 'sysconfig', 
    'builtins', 'warnings', 'contextlib', 'abc', 'atexit', 'traceback', 'gc', 'inspect', 
    'site', 'fpectl', 'code', 'codeop', 'zipimport', 'pkgutil', 'modulefinder', 'runpy', 
    'importlib', 'parser', 'ast', 'symtable', 'symbol', 'token', 'keyword', 'tokenize', 
    'tabnanny', 'pyclbr', 'py', 'compileall', 'dis', 'pickletools', 'formatter', 'msilib', 
    'msvcrt', 'winreg', 'winsound', 'posix', 'pwd', 'spwd', 'grp', 'crypt', 'termios', 
    'tty', 'pty', 'fcntl', 'pipes', 'resource', 'nis', 'syslog', 'optparse', 'imp'
]