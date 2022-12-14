#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import sys

reload(sys)
sys.setdefaultencoding('UTF-8')

import os
import re
import sqlite3
from contextlib import closing
from os.path import join, exists

import arrow
from flask import Flask, request, send_from_directory, g, render_template, abort, redirect, url_for
from werkzeug.utils import secure_filename

from xmind2zantao.xmind_parser import xmind_to_testcase
from xmind2zantao.zandao_helper import ZantaoHelper, build_catalog_tree
from xmind2zantao.zentao import xmind_to_zentao_csv_file

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = ['xmind']
DEBUG = True
DATABASE = join(os.getcwd(), 'data.db3')
HOST = '0.0.0.0'

# 禅道地址 http://192.168.103.38/zentao
ZANTAO_BASE_URL = os.getenv('ZANTAO_BASE_URL')
# 登录信息
ZANTAO_USERNAME = os.getenv('ZANTAO_USERNAME')
ZANTAO_PASSWD = os.getenv('ZANTAO_PASSWD')
# 产品ID。
ZANTAO_PRODUCT_ID = os.getenv('ZANTAO_PRODUCT_ID')

# 是否启用禅道附加功能，目前主要是对模块的检查
ENABLE_ZANTAO_API = ZANTAO_BASE_URL and ZANTAO_USERNAME and ZANTAO_PASSWD and ZANTAO_PRODUCT_ID

# 默认用例类型。
ZANTAO_DEFAULT_EXECUTION_TYPE = os.getenv('ZANTAO_DEFAULT_EXECUTION_TYPE')

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = os.urandom(32)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource(join(BASE_PATH, 'schema.sql'), mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def init():
    if not exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)

    if not exists(DATABASE):
        init_db()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


def insert_record(xmind_name, note=''):
    c = g.db.cursor()
    now = str(arrow.now())
    sql = "INSERT INTO records (name,create_on,note) VALUES (?,?,?)"
    c.execute(sql, (xmind_name, now, str(note)))
    g.db.commit()


def delete_record(filename, record_id):
    xmind_file = join(app.config['UPLOAD_FOLDER'], filename)
    zentao_file = join(app.config['UPLOAD_FOLDER'], filename[:-5] + 'csv')

    for f in [xmind_file, zentao_file]:
        if exists(f):
            os.remove(f)

    c = g.db.cursor()
    sql = 'UPDATE records SET is_deleted=1 WHERE id = ?'
    c.execute(sql, (record_id,))
    g.db.commit()


def delete_records(keep=20):
    """Clean up files on server and mark the record as deleted"""
    sql = "SELECT * from records where is_deleted<>1 ORDER BY id desc LIMIT -1 offset {}".format(keep)
    assert isinstance(g.db, sqlite3.Connection)
    c = g.db.cursor()
    c.execute(sql)
    rows = c.fetchall()
    for row in rows:
        name = row[1]
        xmind = join(app.config['UPLOAD_FOLDER'], name)
        csv = join(app.config['UPLOAD_FOLDER'], name[:-5] + 'csv')

        for f in [xmind, csv]:
            if exists(f):
                os.remove(f)

        sql = 'UPDATE records SET is_deleted=1 WHERE id = ?'
        c.execute(sql, (row[0],))
        g.db.commit()


def get_latest_record():
    found = list(get_records(1))
    if found:
        return found[0]


def get_records(limit=12):
    short_name_length = 120
    c = g.db.cursor()
    sql = "select * from records where is_deleted<>1 order by id desc limit {}".format(int(limit))
    c.execute(sql)
    rows = c.fetchall()

    for row in rows:
        name, short_name, create_on, note, record_id = row[1], row[1], row[2], row[3], row[0]

        # shorten the name for display
        if len(name) > short_name_length:
            short_name = name[:short_name_length] + '...'

        # more readable time format
        create_on = arrow.get(create_on).humanize()
        yield short_name, name, create_on, note, record_id


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def check_file_name(name):
    secured = secure_filename(name)
    if not secured:
        secured = re.sub('[^\w\d]+', '_', name)  # only keep letters and digits from file name
        assert secured, 'Unable to parse file name: {}!'.format(name)
    return secured + '.xmind'


def save_file(file):
    if file and allowed_file(file.filename):
        filename = file.filename  # check_file_name(file.filename[:-6])
        filename = u'{}_{}.xmind'.format(filename[:-6], arrow.now().strftime('%Y%m%d_%H%M%S'))
        upload_to = join(app.config['UPLOAD_FOLDER'], filename)
        #
        # if exists(upload_to):
        #     filename = u'{}_{}.xmind'.format(filename[:-6], arrow.now().strftime('%Y%m%d_%H%M%S'))
        #     upload_to = join(app.config['UPLOAD_FOLDER'], filename)

        file.save(upload_to)
        insert_record(filename)
        g.is_success = True
        return filename

    elif file.filename == '':
        g.is_success = False
        g.error = "Please select a file!"

    else:
        g.is_success = False
        g.invalid_files.append(file.filename)


def verify_uploaded_files(files):
    # download the xml directly if only 1 file uploaded
    if len(files) == 1 and getattr(g, 'is_success', False):
        g.download_xml = get_latest_record()[1]

    if g.invalid_files:
        g.error = "Invalid file: {}".format(','.join(g.invalid_files))


def fix_cases_with_api(testcases):
    count = 0
    template_data = []
    catalog_tree = {}
    if ENABLE_ZANTAO_API:
        zantao = ZantaoHelper(ZANTAO_BASE_URL,
                              ZANTAO_USERNAME, ZANTAO_PASSWD,
                              )

        catalog_dict, catalog_set = zantao.get_catalogs(ZANTAO_PRODUCT_ID)
        temp = {}
        for s in testcases:
            category = s['category']
            if category in catalog_dict:
                s['category'] = catalog_dict.get(category)
                s['category_match'] = True
            elif category in catalog_set:
                s['category_match'] = True
            else:
                if category not in temp:
                    count += 1
                    temp[category] = 0
                else:
                    temp[category] += 1

            if ZANTAO_DEFAULT_EXECUTION_TYPE:
                execution_type = s['execution_type']
                s['execution_type'] = execution_type or ZANTAO_DEFAULT_EXECUTION_TYPE

        catalog_tree, template_data = build_catalog_tree(
            [s['category'][:s['category'].index('(')] if '(' in s['category'] else s['category'] for s in testcases],
            check_dict=catalog_dict)
    return count, catalog_tree, template_data


@app.route('/', methods=['GET', 'POST'])
def index(download_xml=None):
    g.invalid_files = []
    g.error = None
    g.download_xml = download_xml
    g.filename = None

    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        g.filename = save_file(file)
        verify_uploaded_files([file])
        delete_records()

    else:
        g.upload_form = True

    if g.filename:
        return redirect(url_for('preview_file', filename=g.filename))
    else:
        return render_template('index.html', records=list(get_records()))


@app.route('/<filename>/to/zantao')
def download_file(filename):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)

    if not exists(full_path):
        abort(404)

    csv_out = full_path[:-5] + 'csv'
    testcases = xmind_to_testcase(full_path)
    testcases = [t.to_dict() for t in testcases]

    fix_cases_with_api(testcases)

    xmind_to_zentao_csv_file(testcases, csv_out)

    filename = filename[:-5] + 'csv'
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/preview/<filename>')
def preview_file(filename):
    catalog_tree, count, suite_count, testcases, tree_template_data = preview_data(filename)
    return render_template('preview.html', name=filename, testcases=testcases, suite_count=suite_count,
                           tree_data=tree_template_data,
                           zantao_api=ENABLE_ZANTAO_API, catagory_nomatch=count)


@app.route('/preview_tree/<filename>')
def preview_tree_file(filename):
    catalog_tree, count, suite_count, testcases, tree_template_data = preview_data(filename)
    return render_template('preview_tree.html', name=filename, testcases=testcases, suite_count=suite_count,
                           tree_data=tree_template_data, catalog_tree=catalog_tree,
                           zantao_api=ENABLE_ZANTAO_API, catagory_nomatch=count)


def preview_data(filename):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)
    if not exists(full_path):
        abort(404)
    testcases = xmind_to_testcase(full_path)
    testcases = [t.to_dict() for t in testcases]
    suite_count = len(testcases)
    count, catalog_tree, tree_template_data = fix_cases_with_api(testcases)
    return catalog_tree, count, suite_count, testcases, tree_template_data


@app.route('/delete/<filename>/<int:record_id>')
def delete_file(filename, record_id):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)
    if not exists(full_path):
        abort(404)
    else:
        delete_record(filename, record_id)
    return redirect('/')


@app.errorhandler(Exception)
def app_error(e):
    return str(e)


init()

if __name__ == '__main__':
    app.run(HOST, debug=DEBUG, port=5001)
