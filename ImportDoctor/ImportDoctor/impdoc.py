import os
import sys
import inspect
from collections import defaultdict

py_modules = [
    u'string', u're', u'difflib', u'textwrap', u'unicodedata', u'stringprep', u'readline', 
    u'rlcompleter', u'struct', u'codecs', u'datetime', u'calendar', u'collections', 
    u'collections', u'heapq', u'bisect', u'array', u'weakref', u'types', u'copy', u'pprint', 
    u'reprlib', u'enum', u'numbers', u'math', u'cmath', u'decimal', u'fractions', u'random', 
    u'statistics', u'itertools', u'functools', u'operator', u'pathlib', u'os', u'fileinput', 
    u'stat', u'filecmp', u'tempfile', u'glob', u'fnmatch', u'linecache', u'shutil', u'macpath', 
    u'pickle', u'copyreg', u'shelve', u'marshal', u'dbm', u'sqlite', u'zlib', u'gzip', u'bz', 
    u'lzma', u'zipfile', u'tarfile', u'csv', u'configparser', u'netrc', u'xdrlib', u'plistlib', 
    u'hashlib', u'hmac', u'os', u'io', u'time', u'argparse', u'getopt', u'logging', u'logging', 
    u'logging', u'getpass', u'curses', u'curses', u'curses', u'curses', u'platform', u'errno', 
    u'ctypes', u'threading', u'multiprocessing', u'concurrent', u'subprocess', u'sched', u'queue', 
    u'dummy', u'socket', u'ssl', u'select', u'selectors', u'asyncio', u'asyncore', u'asynchat', 
    u'signal', u'mmap', u'email', u'json', u'mailcap', u'mailbox', u'mimetypes', u'base', 
    u'binhex', u'binascii', u'quopri', u'uu', u'html', u'html', u'html', u'xml', u'xml', 
    u'xml', u'xml', u'xml', u'xml', u'xml', u'xml', u'xml', u'webbrowser', u'cgi', u'cgitb', 
    u'wsgiref', u'urllib', u'urllib', u'urllib', u'urllib', u'urllib', u'urllib', u'http', 
    u'http', u'ftplib', u'poplib', u'imaplib', u'nntplib', u'smtplib', u'smtpd', u'telnetlib', 
    u'uuid', u'socketserver', u'http', u'http', u'http', u'xmlrpc', u'xmlrpc', u'xmlrpc', 
    u'ipaddress', u'audioop', u'aifc', u'sunau', u'wave', u'chunk', u'colorsys', u'imghdr', 
    u'sndhdr', u'ossaudiodev', u'gettext', u'locale', u'turtle', u'cmd', u'shlex', u'tkinter', 
    u'tkinter', u'tkinter', u'tkinter', u'typing', u'pydoc', u'doctest', u'unittest', u'unittest', 
    u'unittest', u'test', u'test', u'bdb', u'faulthandler', u'pdb', u'timeit', u'trace', 
    u'tracemalloc', u'distutils', u'ensurepip', u'venv', u'zipapp', u'sys', u'sysconfig', 
    u'builtins', u'warnings', u'contextlib', u'abc', u'atexit', u'traceback', u'gc', u'inspect', 
    u'site', u'fpectl', u'code', u'codeop', u'zipimport', u'pkgutil', u'modulefinder', u'runpy', 
    u'importlib', u'parser', u'ast', u'symtable', u'symbol', u'token', u'keyword', u'tokenize', 
    u'tabnanny', u'pyclbr', u'py', u'compileall', u'dis', u'pickletools', u'formatter', u'msilib', 
    u'msvcrt', u'winreg', u'winsound', u'posix', u'pwd', u'spwd', u'grp', u'crypt', u'termios', 
    u'tty', u'pty', u'fcntl', u'pipes', u'resource', u'nis', u'syslog', u'optparse', u'imp'
]

# Checks to see if a string matches any of the current system level modules
def is_sys_module(name):
    if name not in sys.modules.keys():
        return False
    pathname = os.path.dirname(inspect.getfile(sys.modules[name]))
    # System modules either come from standard python libraries or from venvs
    for path in sys.path:
        if pathname.startswith(path):
            return True
    return False
    
def is_py_module(name):
    return name in py_modules


# returns a word with a snippet cut out of it
# also returns true if the word was changed
def cut_word(source, snip):
    if not source or not snip:
        return source, False
    loc = source.find(snip)
    if loc == -1:
        return source, False
    return source[:loc] + source[loc+len(snip):], True

# Object to hold all of the settings for formatting imports
class ImportDoctor(object):
    deep_check = False    # Grabs indented imports
    alpha_order = False   # Sorts by alphabetical instead of length
    native_split = True   # Separates system modules from local ones
    descending = True     # Primary order on sort BIG => small
    one_import_one_line = True # Separates grouped imports onto their own lines
    exclude_from = True   # Sort on string before 'import' for 'from' imports
    import_ontop = True   # Place all 'from' imports below standard imports
    
    def __init__(self, **kwargs):
        if not set(kwargs.keys()) <= self.__vars__():
            raise ValueError('Unexpected arguements passed.')
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
        
    @classmethod
    def run(cls, filename, **kwargs):
        cls(**kwargs).fix(filename)
    
    def __vars__(self):
        return set([x for x in dir(self) if not x.startswith('__') 
                    and not callable(getattr(self, x))])
    
    def is_import_statement(self, line):
        if self.deep_check:
            line = line.lstrip()
        return line.startswith('import ') or line.startswith('from ')
    
    def analyze(self, filename):
        with open(filename) as f:
            doc = f.readlines()
        self.source = []
        self.Q = []
        chars = 0
        state = 0
        
        # stupid helper function
        def test_backslash(statement):
            statement, res = cut_word(statement, '\\')
            x = 0
            if res:
                x = 1
            return statement, x
        
        for line in doc:
            if state == 1:
                focus = line.strip()
                focus, state = test_backslash(focus)
                self.Q[-1] += ' ' + focus
                continue
            elif state == 2:
                focus = line.strip()
                focus, res = cut_word(focus, ')')
                if res:
                    state = 0
                self.Q[-1] += ' ' + focus
                continue
            elif self.is_import_statement(line):
                focus = line.strip()
                focus, state = test_backslash(focus)
                if not state and '(' in focus:
                    state = 2
                    focus, res = cut_word(focus, '(')
                    focus, res = cut_word(focus, ')')
                    if res:
                        state = 0
                self.Q.append(focus)
                continue
            self.source.append(line)
            
        # one line import split
        if not self.one_import_one_line:
            return
        
        store = defaultdict(set)
        cap = len(self.Q)
        index = 0
        # analyze each import line
        while index < cap:
            index += 1
            line = self.Q.pop(0)
            parts = filter(bool, line.split(','))
            base = ' '.join(filter(bool, parts.pop(0).split(' ')))
            
            # create base import, and a list of all imported modules
            base, x = base.rsplit(' ', 1)
            parts.append(x)
            store[base] |= set(parts)
        
        # choose sorting method
        lam = lambda n: n if self.alpha_order else lambda n: len(n)
        for base, parts in store.iteritems():
            for part in sorted(parts, key=lam):
                self.Q.append(' '.join([base.strip(), part.strip()]))

    def sort_imports(self):
        if not self.Q:
            return
        
        def lamb(n, upto=' import'):
            loc = n.find(upto)
            if loc >= 0:
                return n[:loc + len(upto)]
            return n
        
        # choose method
        if self.alpha_order and not self.exclude_from:
            lam = lambda n: n
        elif self.alpha_order and self.exclude_from:
            lam = lamb
        elif self.exclude_from:
            lam = lambda n: len(lamb(n))
        else:
            lam = lambda n: len(n)
        
        # sort
        self.Q = sorted(self.Q, key=lam, reverse=self.descending)
        
        # split on import first
        if self.import_ontop:
            base = self.Q
            native = []
            index = 0
            while index < len(base):
                if base[index].startswith('import '):
                    native.append(base.pop(index))
                    continue
                index += 1
            self.Q = native
            self.Q.extend(base)
        
        # split on sys modules
        if not self.native_split:
            return
        base = self.Q
        native = []
        index = 0
        py_native = []
        while index < len(base):
            parts = base[index].split(' ')
           
            if is_py_module(parts[1]):
                py_native.append(base.pop(index))
                continue 
            if not is_sys_module(parts[1]):
                index += 1
                continue
            native.append(base.pop(index))
        native.append('')
        py_native.append('')
        self.Q = py_native
        self.Q.extend(native)
        self.Q.extend(base)
            
    def remap(self, filename):
        if 'source' not in self.__vars__():
            raise ValueError('A file has not been loaded yet.')
        if not self.Q:
            return
        with open(filename, 'w+') as f:
            for line in self.Q:
                f.write(line + '\n')
            f.write('\n')
            index = 0
            count = 1
            while index < len(self.source):
                if not self.source[index].strip():
                    count += 1
                    if count > 3:
                        self.source.pop(index)
                    else:
                        index += 1
                else:
                    break
                    
                    continue
            for line in self.source:
                f.write(line)
        pass
    
    def __str__(self):
        if not self.Q:
            return 'Uninitialized'
        rep = ''
        for line in self.Q:
            rep += line + '\n'
        return rep
    
    def fix(self, filename):
        self.analyze(filename)
        self.sort_imports()
        self.remap(filename)
        
if __name__ == "__main__":
    args = sys.argv
    args.pop(0)
    filename = args.pop(0)
    if not os.path.isfile(filename):
        raise ValueError('Only supports single file execution.'
                         ' must pass path to python script file.')
    try:
        doc = ImportDoctor(**{k.strip():v.strip() 
            for k, v in [s.split('=') for s in args]})
    except Exception as e:
        print 'Expected Format: $ python auto_formatter.py '\
            + 'path/to/local/script.py argname=argvalue'
        print 'Recieved:'
        print ' '.join([filename]+args)
        raise e
    
    doc.fix(filename)
