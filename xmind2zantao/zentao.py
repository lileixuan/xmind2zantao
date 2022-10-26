#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import csv
import logging
import os

"""
Convert XMind fie to Zentao testcase csv file 

Zentao official document about import CSV testcase file: https://www.zentao.net/book/zentaopmshelp/243.mhtml 
"""


def xmind_to_zentao_csv_file(testcases, csv_out):
    """Convert XMind file to a zentao csv file"""

    fileheader = ["所属模块", "用例标题", "前置条件", "步骤", "预期", "关键词", "优先级", "用例类型", "适用阶段"]
    zentao_testcase_rows = [fileheader]
    for testcase in testcases:
        row = gen_a_testcase_row(testcase)
        zentao_testcase_rows.append(row)

    if os.path.exists(csv_out):
        os.remove(csv_out)
        # logging.info('The zentao csv file already exists, return it directly: %s', zentao_file)
        # return zentao_file

    with open(csv_out, 'wb') as f:
        writer = csv.writer(f, dialect='excel', delimiter=',')
        writer.writerows(zentao_testcase_rows)
        logging.info('Convert XMind file to a zentao csv file(%s) successfully!', csv_out)

    return csv_out


def gen_a_testcase_row(testcase_dict):
    case_module = testcase_dict['category'].encode('utf-8')  # gen_case_module(testcase_dict['suite'])
    case_title = testcase_dict['name'].encode('utf-8')
    case_precontion = testcase_dict['preconditions'].encode('utf-8')
    case_step, case_expected_result = gen_case_step_and_expected_result(testcase_dict['steps'])
    case_keyword = ''
    case_priority = int(testcase_dict['importance'])
    case_type = gen_case_type(testcase_dict['execution_type'])
    case_apply_phase = gen_case_apply_phase(testcase_dict['apply_phase'])
    row = [case_module, case_title, case_precontion, case_step, case_expected_result, case_keyword, case_priority,
           case_type, case_apply_phase]
    return row


def gen_case_module(module_name):
    if module_name:
        module_name = module_name.replace('（', '(')
        module_name = module_name.replace('）', ')')
    else:
        module_name = '/'
    return module_name


def gen_case_step_and_expected_result(steps):
    case_step = ''
    case_expected_result = ''

    for step_dict in steps:
        case_step += str(step_dict['number']) + '. ' + step_dict['action'].strip('\n') + '\n'
        case_expected_result += str(step_dict['number']) + '. ' + \
                                step_dict['expected'].strip('\n') + '\n' \
            if step_dict.get('expected', '') else ''

    return case_step.encode('utf-8'), case_expected_result.encode('utf-8')


def gen_case_type(case_type):
    return case_type or ''


def gen_case_apply_phase(apply_phase):
    return apply_phase or ''
