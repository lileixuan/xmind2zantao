#!/usr/bin/env python
# _*_ coding:utf-8 _*_

class TestSuite(object):
    sub_suites = None
    name = ''
    details = ''
    testcase_list = None

    def to_dict(self):
        me = {'name': self.name,
              'details': self.details,
              'testcase_list': [],
              'sub_suites': []}

        if self.sub_suites:
            for s in self.sub_suites:
                me['sub_suites'].append(s.to_dict())

        if self.testcase_list:
            for t in self.testcase_list:
                me['testcase_list'].append(t.to_dict())

        return me


class TestCase(object):
    name = ''
    summary = ''
    preconditions = ''
    importance = 2
    execution_type = ''
    steps = None
    category = ''
    category_match = False
    apply_phase = ''

    def to_dict(self):
        me = {'name': self.name,
              'summary': self.summary,
              'preconditions': self.preconditions,
              'importance': self.importance or 2,
              'execution_type': self.execution_type,
              'category': self.category,
              'category_match': self.category_match,
              'apply_phase': self.apply_phase,
              'steps': []}

        if self.steps:
            for s in self.steps:
                me['steps'].append(s.to_dict())

        return me


class TestStep(object):
    number = 1
    action = ''
    expected = ''
    execution_type = ''

    def to_dict(self):
        me = {'number': self.number,
              'action': self.action,
              'expected': self.expected,
              'execution_type': self.execution_type}
        return me


cache = {}
