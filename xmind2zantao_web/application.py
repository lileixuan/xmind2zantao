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
from flask import Flask, request, send_from_directory, g, render_template, abort, redirect, url_for, session, flash
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
# 指定可以使用对产品ID范围，逗号分割。
id_list = os.getenv('ZANTAO_PRODUCT_ID')
ZANTAO_PRODUCT_IDS = id_list.split(',') if id_list else None

# 是否启用禅道附加功能，目前主要是对模块的检查
ENABLE_ZANTAO_API = ZANTAO_BASE_URL

# 默认用例类型。
ZANTAO_DEFAULT_EXECUTION_TYPE = os.getenv('ZANTAO_DEFAULT_EXECUTION_TYPE')

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'xmind2zantao')


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
    if not ENABLE_ZANTAO_API:
        return
    if request.path in ['/login', '/logout'] or request.path.startswith('/static'):
        print '特殊路径%s 不验证' % request.path
        return None
    user = session.get('logged_in')  # 获取用户登录信息
    if not user:
        print '未登录 跳转'
        return redirect(url_for('login'))
    return None


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
    csv_file = join(app.config['UPLOAD_FOLDER'], filename[:-5] + 'csv')

    for f in [xmind_file, csv_file]:
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


def fix_cases_with_api(testcases, product):
    count = 0
    template_data = []
    catalog_tree = {}
    if ENABLE_ZANTAO_API and product:
        username = session.get('username')
        password = session.get('password')
        zantao = ZantaoHelper(ZANTAO_BASE_URL,
                              username, password,
                              )

        catalog_dict, catalog_set = zantao.get_catalogs(product)
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

        catalog_tree, template_data = build_catalog_tree(
            [s['category'][:s['category'].index('(')] if '(' in s['category'] else s['category'] for s in testcases],
            check_dict=catalog_dict)
    return count, catalog_tree, template_data


def get_zantao_products(product):
    if ENABLE_ZANTAO_API:
        products = session.get('products')
        p_list = []
        sp_id = None
        if ZANTAO_PRODUCT_IDS:
            for k in ZANTAO_PRODUCT_IDS:
                p_list.append({'product_id': k, 'product_name': products[k]})
                if product == k:
                    sp_id = product
        else:
            p_list = [{'product_id': k, 'product_name': v} for k, v in products.iteritems()]
        return p_list, sp_id or p_list[0]['product_id'] if p_list else None
    else:
        return None, None


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        try:

            password = request.form['password']
            username = request.form['username']

            z = ZantaoHelper(ZANTAO_BASE_URL, username, password)
            products = z.get_products()

            session['products'] = products
            session['password'] = password
            session['username'] = username
            session['logged_in'] = True

        except Exception as e:
            flash('用户名或密码错误')
            # return render_template('login.html')
        return redirect(url_for('login'))
    else:
        if not session.get('logged_in'):
            return render_template('login.html')
        else:
            return redirect(url_for('index'))


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index(download_xml=None):
    return render_template('index.html', zantao_api=ENABLE_ZANTAO_API, records=list(get_records()))


@app.route('/upload', methods=['POST'])
def upload_xmind(download_xml=None):
    g.invalid_files = []
    g.error = None
    g.download_xml = download_xml
    g.filename = None

    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('index'))

    g.filename = save_file(file)
    verify_uploaded_files([file])
    delete_records()

    if g.filename:
        return redirect(url_for('preview_file', filename=g.filename))


@app.route('/<product>/<filename>/to/zantao')
@app.route('/<filename>/to/zantao')
def download_csv_file(filename, product=None):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)

    if not exists(full_path):
        abort(404)

    csv_out = full_path[:-5] + 'csv'
    testcases = xmind_to_testcase(full_path)
    testcases = [t.to_dict({'execution_type': ZANTAO_DEFAULT_EXECUTION_TYPE}) for t in testcases]

    fix_cases_with_api(testcases, product)

    xmind_to_zentao_csv_file(testcases, csv_out)

    filename = filename[:-5] + 'csv'
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/uploads/<filename>')
def download_xmind_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/preview/<product>/<filename>')
@app.route('/preview/<filename>')
def preview_file(filename, product=None):
    products, selected_product = get_zantao_products(product)
    if not product and selected_product:
        return redirect(url_for('preview_file', product=selected_product, filename=filename))

    catalog_tree, count, suite_count, testcases, tree_template_data = preview_data(filename, selected_product)
    return render_template('preview.html', name=filename, products=products, selected_product=selected_product,
                           testcases=testcases, suite_count=suite_count,
                           tree_data=tree_template_data,
                           zantao_api=ENABLE_ZANTAO_API, catagory_nomatch=count)


@app.route('/create_tree/<product>/<filename>')
def create_catalogs(filename, product):
    catalog_tree, count, suite_count, testcases, tree_template_data = preview_data(filename, product)

    if ENABLE_ZANTAO_API and product:
        username = session.get('username')
        password = session.get('password')
        zantao = ZantaoHelper(ZANTAO_BASE_URL,
                              username, password,
                              )
        zantao.create_catalogs(catalog_tree, product)
    return redirect(url_for('preview_tree_file', product=product, filename=filename))


@app.route('/preview_tree/<product>/<filename>')
def preview_tree_file(filename, product):
    products = session.get('products', {})
    product_name = products.get(product, '')
    catalog_tree, count, suite_count, testcases, tree_template_data = preview_data(filename, product)
    return render_template('preview_tree.html', name=filename, selected_product=product, product_name=product_name,
                           testcases=testcases, suite_count=suite_count,
                           tree_data=tree_template_data, catalog_tree=catalog_tree,
                           zantao_api=ENABLE_ZANTAO_API, catagory_nomatch=count)


def preview_data(filename, product):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)
    if not exists(full_path):
        abort(404)
    testcases = xmind_to_testcase(full_path)
    testcases = [t.to_dict({'execution_type': ZANTAO_DEFAULT_EXECUTION_TYPE}) for t in testcases]
    suite_count = len(testcases)
    count, catalog_tree, tree_template_data = fix_cases_with_api(testcases, product)
    return catalog_tree, count, suite_count, testcases, tree_template_data


@app.route('/delete/<filename>/<int:record_id>')
def delete_file(filename, record_id):
    delete_record(filename, record_id)
    return redirect('/')


@app.errorhandler(Exception)
def app_error(e):
    return str(e)


init()

if __name__ == '__main__':
    app.run(HOST, debug=DEBUG, port=5001)
