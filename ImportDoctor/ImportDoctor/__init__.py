from collections import defaultdict
import doctor_base
import os, re

# Object to hold all of the settings for formatting imports, can be reused or
# modified on the fly. Supported by superclass
class ImportDoctor(doctor_base.ImportNurse):

    @classmethod
    def run(cls, filename, **kwargs):
        cls(**kwargs).fix(filename)

    def is_import_statement(self, line):
        if not self.ignore_indented:
            line = line.lstrip()
        return line.startswith('import ') or line.startswith('from ')

    def is_comment(self, line):
        if not self.ignore_indented:
            line = line.strip()
        return line.startswith('###')

    # Apply both of the regex expressions and return the best fit
    def apply_regex(self, line):
        # Find match in one of two patterns
        match = self._ImportNurse__from_statement.search(line)
        if not match or len(match.groups()) != 2:
            match = self._ImportNurse__import_statement.search(line)
            if not match:
                raise ValueError('Unparsable import: ' + line)
        return match

    # Parse a regex match into a list of groups. Split the last group on
    # any comma, then strip everything.
    def parse_match(self, match):
        if not match: return []
        groups = list(match.groups())
        for i in range(len(groups)):
            groups[i] = map(lambda n: n.replace(',', '').strip(), groups[i].split(','))
        return groups

    # Remove all imports in Q that have a name that exists in groups.
    # Take into account that 'as' renames a module
    def remove_duplicates(self, groups):
        def snip(n):
            loc = n.find(' as ')
            if loc >= 0:
                return n[loc + len(' as '):]
            return n
        def in_group(X, G):
            if X == '*':
                return False
            x = snip(X)
            for entry in G:
                if x == snip(entry):
                    return True
            return False
        for key in self.Q:
            self.Q[key] = set([x for x in self.Q[key] if not in_group(x, groups)])

    # Parse a single import line (newline & backslashes removed) into the Q
    def parse_import(self, line):
        match = self.apply_regex(line)

        groups = self.parse_match(match)
        base = 'import '
        if len(groups) == 2:
            base = 'from ' + ''.join(groups[0]) + ' import '
        groups = set(groups[-1])

        if self._ImportNurse__remove_overrides:
            self.remove_duplicates(groups)

        self.Q[base] |= groups

    # Read from a file and start the parsing process
    def analyze(self, filename):
        with open(filename) as f:
            doc = f.readlines()
        self.parse_source(doc)

    # Analyze a file line by line, pulling the import statements into Q and
    # pushing everything else into source
    def parse_source(self, doc):
        self.source = []
        self.Q = defaultdict(set) #if self.one_import_per_line else []

        while doc:
            line = doc.pop(0)
            if self.is_comment(line):
                continue
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
        self.parse_queue()

    def parse_queue(self):
        store = self.Q
        self.Q = []
        for base, parts in store.iteritems():
            parts = sorted(parts, key=self._filter, reverse=self.descending)
            if self._ImportNurse__one_import_per_line:
                for part in parts:
                    self.Q.append(base + part)
                continue
            if parts:
                self.Q.append(base + ', '.join(parts))

    def sort_imports(self):
        if not self.Q:
            print 'Queue is empty. Nothing to sort.'
            return

        # Used to sort by everything before the import statement
        def lamb(n, upto=' import'):
            loc = n.find(upto)
            if loc >= 0:
                return n[:loc + len(upto)]
            return n

        # choose sorting method
        if self.exclude_from:
            lam = lambda n: self._filter(lamb(n))
        else:
            lam = self._filter

        # sort
        self.Q = [
            doctor_base.wrap_word(line, self._ImportNurse__wrap_depth, self.wrap_strict)
            for line in sorted(self.Q, key=lam, reverse=self.descending)
        ]

        self.place_imports_ontop()
        futures = self.split_futures()
        self.isolate_modules_by_group(futures)

    def split_futures(self):
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
        return futures

    def place_imports_ontop(self):
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

    def isolate_modules_by_group(self, futures):
        # split on module categories
        if not self.group_by_module_type:
            futures.extend(self.Q)
            self.Q = futures
            return

        base = self.Q
        native = []
        index = 0
        py_native = []

        def lamb(n):
            if n[0].startswith('__REGEX__ '):
                return ('1' + n[0], n[1])
            return ('0' + n[0], n[1])
        # Must reverse search, so modules that extend other modules in this
        # list get processed first.
        iso_map = sorted([(self.str_or_pat(mod), self.try_pattern(mod)) for mod in self._ImportNurse__isolation], reverse=True, key=lamb)
        iso_names = [x[0] for x in iso_map]
        groups = { mod:[] for mod in iso_names }
        while index < len(base):
            module_name = base[index].split(' ')[1].strip(',')

            used = False
            for x, mod in iso_map:
                if isinstance(mod, str):
                    if module_name.startswith(mod):
                        groups[mod].append(base.pop(index))
                        used = True
                        break
                else:
                    if mod.search(module_name):
                        groups[self.str_or_pat(mod)].append(base.pop(index))
                        used = True
                        break
            if used:
                continue
            if module_name in doctor_base.builtin_python_modules:
                py_native.append(base.pop(index))
                continue
            if self.is_sys_module(module_name):
                native.append(base.pop(index))
                continue
            index += 1
        groups['futures'] = futures
        groups['python builtin'] = py_native
        groups['system native'] = native
        groups['all other'] = base
        group_names = ['futures', 'python builtin', 'system native']
        group_names.extend(iso_names)
        group_names.append('all other')

        # Merge all groups with a space inbetween each one
        self.Q = []
        for x, module_group in enumerate([name for name in group_names if groups[name]]):
            if self.comment_names and module_group is not 'futures':
                title = module_group
                if title in iso_names:
                    title = 'matching [{}]'.format(title)
                self.Q.append('### Imports from {} modules.'.format(title))
            self.Q.extend(groups[module_group])
            if x + 1 < len(groups):
                self.Q.append('')

    def remap(self, filename):
        if 'source' not in self.__vars__() or self.source is None:
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
                    if count > self._ImportNurse__newline_padding:
                        self.source.pop(index)
                    else:
                        index += 1
                else:
                    break
            for line in self.source:
                f.write(line)

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

def main(*args):
    ImportDoctor().fix(filename)
