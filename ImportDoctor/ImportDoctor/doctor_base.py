import re, sys, os, inspect

class ImportNurse(object):
    Q = []                      # Holds imports during sorting
    source = []                 # Holds remainder of code during sorting
    ignore_indented = True      # Grabs indented imports
    group_by_module_type = True # Separates system modules from local ones
    descending = True           # Primary order on sort: True => BIG to small
    exclude_from = True         # Sort on string before 'import' for 'from' imports
    import_ontop = True         # Place all 'from' imports below standard imports
    wrap_strict = False         # If true, wrap_depth will be strictly enforced
    comment_names = True        # If true, groups will be named in comments above group

    # These variables are controlled through getters and setters.
    __alpha_order = False        # Sorts by alphabetical instead of length
    __newline_padding = 1        # How many empty lines after end of imports
    __isolation = []             # Groups of imports to separate by name
    __wrap_depth = 0             # The character count at which line wrapping begins
    __one_import_per_line = True # Separates grouped imports onto their own lines
    __remove_overrides = True    # removes imports that are overridden by others

    # groups as follows: from [AModule] import ([A, B, C])
    __from_statement = re.compile('from +([0-9a-zA-Z._]+) +import +\\(?([ 0-9a-zA-Z.,_*]+)\\)? *')
    # groups as follows: import ([AModule, BModule])
    __import_statement = re.compile('import +\\(?([ 0-9a-zA-Z.,_]+)\\)? *')

    def __init__(self, **kwargs):
        self.load_prefs()
        if not set(kwargs.keys()) <= self.__vars__():
            raise ValueError('Unexpected arguements passed.')
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
        self._filter = (lambda n: n) if self.__alpha_order else (lambda n: len(n))
        pathpat = re.compile('/python[0-3]\.[0-9.]+/')
        self.__sys_paths = [p for p in sys.path if pathpat.search(p)]
        self.save_prefs()

    def load_prefs(self):
        pref_file = os.path.join(os.path.dirname(__file__), 'prefs/prefs.txt')
        if not os.path.isfile(pref_file):
            return
        with open(pref_file) as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip().split('=')
            setattr(self, line[0], eval('='.join(line[1:])))

    def save_prefs(self):
        pref_file = os.path.join(os.path.dirname(__file__), 'prefs')
        if not os.path.isdir(pref_file):
            os.mkdir(pref_file)
        pref_file = os.path.join(pref_file, 'prefs.txt')
        saveable = [
            'ignore_indented',
            'group_by_module_type',
            'descending',
            'exclude_from',
            'import_ontop',
            'wrap_strict',
            'comment_names',
            '_ImportNurse__alpha_order',
            '_ImportNurse__newline_padding',
            'isolated_groups',
            '_ImportNurse__wrap_depth',
            '_ImportNurse__one_import_per_line',
            '_ImportNurse__remove_overrides',
        ]
        with open(pref_file, 'w') as f:
            for var in saveable:
                f.write('{}={}\n'.format(var, getattr(self, var)))

    def __vars__(self):
        return set([x for x in dir(self) if not x.startswith('__') 
            and not x.startswith('_ImportNurse__') and not callable(getattr(self, x))])

    def __str__(self):
        if not self.Q:
            return 'Uninitialized'
        rep = ''
        for line in self.Q:
            rep += line + '\n'
        return rep[:-1]
    
    def iteritems(self):
        return [(var, getattr(self, var)) for var in self.__vars__()]

    # This function defines a decorator that resets the data parsed if a
    # function decorated with this is called.
    def _purge_state(func):
        def oncall(self, *args, **kwargs):
            func(self, *args, **kwargs)
            if self.Q or self.source:
                print 'Critical variable ({}) modified. Resetting Queue.'.format(func.__name__)
            self.Q = []
            self.source = []
        return oncall

    @property
    def one_import_per_line(self):
        return self.__one_import_per_line

    @one_import_per_line.setter
    @_purge_state
    def one_import_per_line(self, value):
        self.__one_import_per_line = bool(value)
        if not self.__one_import_per_line and self.__wrap_depth < 26:
            print 'One import per line has been disabled. Setting default line wrapping at 100 characters'
            self.__wrap_depth = 100

    @property
    def remove_overrides(self):
        return self.__remove_overrides

    @remove_overrides.setter
    @_purge_state
    def remove_overrides(self, value):
        self.__remove_overrides = bool(value)

    @property
    def regex_find_import(self):
        return self.__import_statement

    @regex_find_import.setter
    @_purge_state
    def regex_find_import(self, value):
        if isinstance(value, basestring):
            self.__import_statement = re.compile(str(value))
        elif isinstance(value, type(self.__import_statement)):
            self.__import_statement = value
        else:
            raise ValueError('Value must be a string or compiled regex search object.')

    @property
    def regex_find_from(self):
        return self.__from_statement

    @regex_find_from.setter
    @_purge_state
    def regex_find_from(self, value):
        if isinstance(value, basestring):
            self.__from_statement = re.compile(str(value))
        elif isinstance(value, type(self.__from_statement)):
            self.__from_statement = value
        else:
            raise ValueError('Value must be a string or compiled regex search object.')

    @property
    def order_alphabetically(self):
        return self.__alpha_order

    @order_alphabetically.setter
    @_purge_state
    def order_alphabetically(self, value):
        value = bool(value)
        self.__alpha_order = value
        self._filter = (lambda n: n) if value else (lambda n: len(n))

    @property
    def wrap_depth(self):
        return self.__wrap_depth

    @wrap_depth.setter
    def wrap_depth(self, value):
        if type(value) is not int:
            raise ValueError('wrap_depth must be integer')
        if value < 25:
            value = 0
        self.__wrap_depth = value

    @property
    def newline_padding(self):
        return self.__newline_padding

    @newline_padding.setter
    def newline_padding(self, value):
        if type(value) is not int:
            raise ValueError('newline_padding must be an integer')
        if value < 0:
            raise ValueError('Padding must be a positive value')
        self.__newline_padding = value

    @property
    def isolated_groups(self):
        return [name if isinstance(name, basestring) else self.str_or_pat(name) for name in self.__isolation]

    @isolated_groups.setter
    def isolated_groups(self, value):
        if type(value) is not list:
            raise ValueError('isolated_groups must be a list of module names')
        self.__isolation = []
        for item in value:
            if isinstance(item, basestring):
                item = str(item)
                if item.startswith('__REGEX__ '):
                    item = re.compile(item[10:])
                self.__isolation.append(item)
            elif isinstance(item, type(self.__from_statement)):
                self.__isolation.append(value)
            else:
                raise ValueError('isolated_groups must contain strings or compiled regex objects')
        self.__isolation = value[:]

    # Checks to see if a string matches any of the current system level modules
    def is_sys_module(self, name):
        if name not in sys.modules.keys():
            return False
        pathname = os.path.dirname(inspect.getfile(sys.modules[name]))
        # System modules either come from standard python libraries or from venvs
        for path in self.__sys_paths:
            if pathname.startswith(path):
                return True
        return False

    str_or_pat = staticmethod(lambda n: n if isinstance(n, str) else '__REGEX__ {}'.format(re.sub('\\\\\\\\', '\\\\', n.pattern)))


# returns a long line with \\\n inserted after a space
# segmenting the line into depth sized chunks
def wrap_word(line, depth, strict):
    line = line.strip()
    if depth < 26:
        return line
    result = ''
    split_point = line.find(' ')
    while len(line) > depth:
        if split_point == -1:
            break
        next_blank = split_point
        while next_blank <= depth:
            split_point = next_blank
            next_blank = line.find(' ', next_blank + 1)
            if next_blank == -1:
                if strict:
                    result += line[:split_point + 1] + '\\\n'
                    line = '    ' + line[split_point + 1:]
                return result + line
        result += line[:split_point + 1] + '\\\n'
        line = '    ' + line[split_point + 1:]
        split_point = line.find(' ', 5)
    return result + line

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