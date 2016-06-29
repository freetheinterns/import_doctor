# This is a script used to test the integrity of ImportDoctor
from ImportDoctor import ImportDoctor
import re

class Comp(object):
    reverse = False
    main_hook = None
    def is_ordered(self, source):
        if not main_hook:
            raise ValueError('Must set comparator method.')
        if len(source) < 2:
            return True
        last = source[0]
        for elem in source[1:]:
            if not main_hook(last, elem):
                return False
            last = elem
        return True

def test_regex(line, doctor, res):
    print 'Testing regex on line: ' + line
    match = doctor.apply_regex(line)
    if not match and not res:
        return
    groups = doctor.parse_match(match)
    try:
        for x, y in zip(res, groups):
            try:
                assert x == y
            except:
                print 'ASSERTION FAILURE'
                print '{} != {}'.format(x, y)
                raise
    except:
        print 'Expected Results: {}'.format(res)
        print 'Found Results: {}'.format(groups)
        raise
    print 'PASSED'

def test_all_regex():
    print 'TESTING ALL REGULAR EXPRESSION CASES'
    doc = ImportDoctor()
    
    regex = [
        ('import animal.cat.mycat ', [['animal.cat.mycat']]),
        ('import   animal, automobile ', [['animal', 'automobile']]),
        ('from animal  import  cat, dog as d, rat #nopep8', [['animal'], ['cat', 'dog as d', 'rat']]),
        ('from animal import   (  cat as c, dog as d, rat  ) #nopep8', [['animal'], ['cat as c', 'dog as d', 'rat']]),
        ('from animal  import (cat, dog, rat  ) ', [['animal'], ['cat', 'dog', 'rat']]),
        ('from animal.phyla import   (cat, dog, rat)', [['animal.phyla'], ['cat', 'dog', 'rat']]),
        ('from animal.phyla  import (cat, dog, rat) ', [['animal.phyla'], ['cat', 'dog', 'rat']]),
    ]
    
    for line, res in regex:
        test_regex(line, doc, res)
    print 'PASSED'

def test_all_sorting():
    print 'TESTING ALL SORTING METHODS'
    print 'Nothing actually tested here yet'
    unsorted = [
        'from notsys import cat',
        'from notsys import rat, cat',
        'from notsys import battery, t',
        'from sys import cat as r',
        'from sys import rat, cat as t',
        'from sys import battery',
        'from __future__ import cat',
        'from __future__ import rat, cat',
        'from __future__ import battery',
    ]
    
    doc = ImportDoctor()
    doc.parse_source(unsorted[:])
    doc.sort_imports()
    print doc
    print '\nnext\n'
    doc.one_import_per_line = False
    doc.parse_source(unsorted[:])
    doc.sort_imports()
    print doc
    print 'PASSED'

def run():
    test_all_regex()
    test_all_sorting()
