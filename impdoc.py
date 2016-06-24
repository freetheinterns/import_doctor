import os
import sys
import inspect
import pkgutil
from collections import defaultdict

# Checks to see if a string matches any of the current system level modules
def is_sys_module(name):
    print name, name in sys.modules.keys()
    if name not in sys.modules.keys():
        return False
    pathname = os.path.dirname(inspect.getfile(sys.modules[name]))
    # System modules either come from standard python libraries or from venvs
    return pathname.startswith('/System/Library/Frameworks') \
        or pathname.startswith('/Users/tedtenedorio/venvs/lib/python2.7')

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
        self.imports = []
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
                self.imports[-1] += ' ' + focus
                continue
            if state == 2:
                focus = line.strip()
                focus, res = cut_word(focus, ')')
                if res:
                    state = 0
                self.imports[-1] += ' ' + focus
                continue
            if self.is_import_statement(line):
                focus = line.strip()
                focus, state = test_backslash(focus)
                if not state and '(' in focus:
                    state = 2
                    focus, res = cut_word(focus, '(')
                    focus, res = cut_word(focus, ')')
                    if res:
                        state = 0
                self.imports.append(focus)
                continue
            self.source.append(line)
            
        # one line import split
        if not self.one_import_one_line:
            return
        
        store = defaultdict(set)
        cap = len(self.imports)
        index = 0
        # analyze each import line
        while index < cap:
            index += 1
            line = self.imports.pop(0)
            parts = filter(bool, line.split(','))
            base = ' '.join(filter(bool, parts.pop(0).split(' ')))
            
            # catch single reference and skip splitter
            if len(parts) == 1:
                self.imports.append(base)
                continue
            # create base import, and a list of all imported modules
            base, x = base.rsplit(' ', 1)
            parts.append(x)
            store[base] |= set(parts)
        
        # choose sorting method
        lam = lambda n: n if self.alpha_order else lambda n: len(n)
        for base, parts in store.iteritems():
            for part in sorted(parts, key=lam):
                self.imports.append(' '.join([base.strip(), part.strip()]))

    def sort_imports(self):
        if not self.imports:
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
        self.Q = sorted(self.imports, key=lam, reverse=self.descending)
        
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
        while index < len(base):
            parts = base[index].split(' ')
            
            if not is_sys_module(parts[1]):
                index += 1
                continue
            native.append(base.pop(index))
        native.append('')
        self.Q = native
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
