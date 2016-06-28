import os
import sys
import inspect
from collections import defaultdict

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

# returns a long line with \\\n inserted after a space
# segmenting the line into depth sized chunks
def wrap_word(line, depth, strict):
    line = line.strip()
    if depth < 30:
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
        
                
# Object to hold all of the settings for formatting imports
class ImportDoctor(ImportNurse):
    
    # groups as follows: from [AModule] import ([A, B, C])
    from_statement = re.compile('from +([a-zA-Z._]+) +import +\\(?([ a-zA-Z.,_]+)\\)? *')
    # groups as follows: import ([AModule, BModule])
    import_statement = re.compile('import \\(?([ a-zA-Z.,_]+)\\)?')
    
    # primary filtering function
    alpha_filter = lambda n: n
        
    @classmethod
    def run(cls, filename, **kwargs):
        cls(**kwargs).fix(filename)
    
    def is_import_statement(self, line):
        if not self.ignore_indented:
            line = line.lstrip()
        return line.startswith('import ') or line.startswith('from ')
    
    def parse_import(self, line):
        # Find match in one of two patterns
        match = self.from_statement.search(line)
        if not match or len(match.groups()) != 2:
            match = self.import_statement.search(line)
            if not match:
                raise ValueError('Unparsable import: ' + line)
        
        
        groups = list(match.groups())
        base = 'import '
        pure_import = True
        if len(groups) == 2:
            pure_import = False
            base = 'from ' + groups[0] + ' import '
            groups = [groups[1]]
        groups = map(lambda n: n.replace(',', '').strip(), groups[0].split(','))
        
        if not self.one_import_per_line:
            self.Q.append(base + ', '.join(groups))
            return
        
        self.Q[base] |= set(groups)
            
    
    def analyze(self, filename):
        with open(filename) as f:
            doc = f.readlines()
        self.source = []
        self.Q = defaultdict(set) if self.one_import_per_line else []
        self.alpha_filter = (lambda n: n) if self.alpha_order else (lambda n: len(n))
        
        while doc:
            line = doc.pop(0)
            if not self.is_import_statement(line):
                self.source.append(line)
                continue
            line = line.strip()
            while line.endswith('\\'):
                line = line.replace('\\', ' ') + doc.pop(0).strip()
            bracket = line.find('(')
            if bracket > 0:
                while line.find(')', bracket) == -1:
                    line = ' '.join([line, doc.pop(0).strip()])
            self.parse_import(line)
            
            
        # one line import split
        if not self.one_import_per_line:
            return
        
        store = self.Q
        self.Q = []
        for base, parts in store.iteritems():
            for part in sorted(parts, key=self.alpha_filter, reverse=self.descending):
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
        if self.exclude_from:
            lam = lambda n: self.alpha_filter(lamb(n))
        else:
            lam = self.alpha_filter
        
        # sort
        self.Q = [
            wrap_word(line, self._wrap_depth, self.wrap_strict) 
            for line in sorted(self.Q, key=lam, reverse=self.descending)
        ]
    
        # Must reverse search, so modules that extend other modules in this list get processed first.
        self._isolation = sorted(self._isolation, reverse=True)
        
        # __future__ imports must be on top
        futures = []
        others = []
        for line in self.Q:
            module = line.split(' ')[1]
            if module.startswith('__future__'):
                if len(module) == 10 or module[10] == '.':
                    futures.append(line)
                    continue
            others.append(line)
        self.Q = others
        futures.sort()
        
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
        
        # split on module categories
        if not self.group_by_module_type:
            futures.extend(self.Q)
            self.Q = futures
            return
        
        base = self.Q
        native = []
        index = 0
        py_native = []
        buckets = [[]]*len(self._isolation)
        while index < len(base):
            module_name = base[index].split(' ')[1]
           
            used = False
            for x, mod in enumerate(self._isolation):
                if module_name.startswith(mod):
                    buckets[x].append(base.pop(index))
                    used = True
                    break
            if used:
                continue
            if module_name in builtin_python_modules:
                py_native.append(base.pop(index))
                continue 
            if is_sys_module(module_name):
                native.append(base.pop(index))
                continue
            index += 1
        groups = [futures, py_native]
        groups.extend(buckets)
        groups.append(native)
        groups.append(base)
        groups = [g for g in groups if g]
        self.Q = []
        for x, module_group in enumerate(groups):
            self.Q.extend(module_group)
            if x + 1 < len(groups):
                self.Q.append('')
            
    def remap(self, filename):
        if 'source' not in self.__vars__():
            raise ValueError('A file has not been loaded yet.')
        if not self.Q:
            return
        with open(filename, 'w+') as f:
            for line in self.Q:
                f.write(line + '\n')
            index = 0
            count = 0
            while index < len(self.source):
                if not self.source[index].strip():
                    count += 1
                    if count > self._newline_padding:
                        self.source.pop(index)
                    else:
                        index += 1
                else:
                    break
            for line in self.source:
                f.write(line)
    
    def __str__(self):
        if not self.Q:
            return 'Uninitialized'
        rep = ''
        for line in self.Q:
            rep += line + '\n'
        return rep[:-2]
    
    def fix_folder(self, foldername):
        for dirpath, folders, files in os.walk(foldername): 
            for filename in files:
                if '.py' not in filename[-3:]:
                    continue
                self.fix(os.path.join(dirpath, filename))
    
    def fix(self, filename):
        if os.path.isdir(filename):
            return self.fix_folder(filename)
        self.analyze(filename)
        self.sort_imports()
        self.remap(filename)
