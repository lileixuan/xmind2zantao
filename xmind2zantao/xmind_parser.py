#!/usr/bin/env python
# _*_ coding:utf-8 _*_
"""
Module to parse xmind file into test suite and test case objects.
"""

import re

from xmindparser import xmind_to_dict, config

from .datatype import TestCase, TestStep, cache

config['hideEmptyValue'] = False
_config = {
    'precondition_sep': '\n----\n',
}


def ignore_filter(topics):
    """filter topics starts with !"""
    result = [t for t in topics if t['title'] and not t['title'].startswith('!')]

    for topic in result:
        more_topics = topic.get('topics', [])
        topic['topics'] = ignore_filter(more_topics)

    return result


def open_and_cache_xmind(xmind_file):
    if not cache:
        cache['sheet'] = xmind_to_dict(xmind_file)
        cache['root'] = get_default_sheet(cache['sheet'])['topic']
        root_topics = cache['root'].get('topics', [])
        assert len(root_topics) > 0, "Invalid Xmind, should have at least 1 topic!"
        cache['root']['topics'] = ignore_filter(root_topics)
        cache['name'] = xmind_file

    get_logger().debug('Cached xmind: {}'.format(cache))


def get_default_sheet(sheets):
    """First sheet is the default sheet."""
    assert len(sheets) >= 0, 'Invalid xmind: should have at least 1 sheet!'
    return sheets[0]


def get_logger():
    from xmindparser import logger
    return logger


def get_priority(d):
    if isinstance(d['makers'], list):
        for m in d['makers']:
            if m.startswith('priority'):
                return int(m[-1])


def get_execution_type(d):
    """
    support testcase type by using "label"
    :param d: testcase topic
    :return: first label
    """
    # try to get automation flag "flag_green"
    if isinstance(d['labels'], list):
        if d['labels']:
            return d['labels'][0]
    return ''


def _filter_empty_value(values):
    result = [v for v in values if v]
    for r in result:
        if not isinstance(r, basestring):
            get_logger().error('Expected string but not: {}'.format(r))
    return [v.strip() for v in result]  # remove blank char in leading and trailing


def _filter_empty_comments(comment_values):
    """comment value like: [[{content:comment1},{content:comment2}],[...]]"""
    for comments in comment_values:
        for comment in comments:
            if comment.get('content'):
                yield comment['content']


def is_testcase_topic(d):
    """如果定义了优先级，或者以 N-/P- 开头，则认为是一个case开始"""
    priority = get_priority(d)

    if priority:
        return True

    if d['title'].startswith('N-') or d['title'].startswith('P-'):
        return True

    return False


def build_testcase_category(nodes):
    if re.match(r'(.*)\(\#\d{1,}\)$', nodes[-1]['title']):
        return nodes[-1]['title']
    else:
        values = [n['title'] for n in nodes]
        values = _filter_empty_value(values)
        return '/' + '/'.join(values)


def build_testcase_precondition(nodes):
    values = [n['note'] for n in nodes]
    values = _filter_empty_value(values)

    return _config['precondition_sep'].join(values)


def parse_step(step_dict):
    step = TestStep()
    step.action = step_dict['title']
    expected_node = step_dict.get('topics', None)

    if expected_node:
        step.expected = expected_node[0]['title']

    return step


def parse_steps(steps_dict):
    steps = []

    for step_number, step_node in enumerate(steps_dict, 1):
        step = parse_step(step_node)
        step.number = step_number
        steps.append(step)

    return steps


def parse_testcase(testcase_dict, parent=None):
    try:
        testcase = TestCase()
        nodes = parent + [testcase_dict] if parent else [testcase_dict]
        testcase.category = build_testcase_category(parent)
        testcase.name = testcase_dict['title']
        # testcase.summary = build_testcase_summary(nodes)
        testcase.preconditions = build_testcase_precondition(nodes)
        testcase.importance = get_priority(testcase_dict)

        testcase.execution_type = get_execution_type(testcase_dict)
        steps_node = testcase_dict.get('topics', None)

        if steps_node:
            testcase.steps = parse_steps(steps_node)

        return testcase
    except Exception as e:
        pass


def xmind_to_testcase(xmind_file):
    """Auto detect and parser xmind to test suite object."""
    cache.clear()
    open_and_cache_xmind(xmind_file)

    def parse_testcase_list(cases_dict, parent=None):
        if is_testcase_topic(cases_dict):
            yield parse_testcase(cases_dict, parent)

        else:
            if not parent:
                parent = []

            parent.append(cases_dict)
            topics = cases_dict['topics'] or []

            for child in topics:
                for _ in parse_testcase_list(child, parent):
                    yield _

            parent.pop()

    open_and_cache_xmind(xmind_file)
    xmind_root = cache['root']
    testcase_list = []
    testcase_topics = xmind_root.get('topics', [])

    for node in testcase_topics:
        for t in parse_testcase_list(node, [xmind_root]):
            testcase_list.append(t)

    return testcase_list
