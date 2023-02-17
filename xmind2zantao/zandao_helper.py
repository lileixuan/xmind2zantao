# -*- coding=utf8 -*-
import sys

reload(sys)
sys.setdefaultencoding('UTF-8')
import requests
import json
import urllib


class ZantaoHelper(object):
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.session = self.get_session()

    def get_session(self):
        session = requests.session()
        resp = session.get(url=self.host + '/api-getsessionid.json')
        zentaosid = json.loads(json.loads(resp.text)['data'])['sessionID']
        session.headers['Cookie'] = 'zentaosid=%s;' % zentaosid
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=utf-8'

        resp = session.post(
            url=self.host + '/user-login.json?m=user&f=login&t=json&zentaosid%s&account=%s&password=%s' % (
                zentaosid, self.username, self.password))
        info = json.loads(resp.text)
        if info['status'] != 'success':
            raise Exception('登录失败')
        return session

    def get_products(self):
        print '读取产品集合开始'
        resp = self.session.get(url=self.host + '/product-all.json')
        products = json.loads(json.loads(resp.text)['data'])['products']
        print '读取产品集合结束'
        return products

    def get_catalogs(self, product_id):
        print '读取远程目录开始'
        resp = self.session.get(url=self.host + '/testcase-browse-%s-0-all.json' % product_id)
        modules = json.loads(json.loads(resp.text)['data'])['modules']
        data = {v: '%s(#%s)' % (v, k) for k, v in modules.iteritems()}
        data2 = {'%s(#%s)' % (v, k) for k, v in modules.iteritems()}
        print '读取远程目录结束'
        return data, data2

    def add_catalog(self, catalog_name, parent_id, product_id):
        payload = [
            ("modules[]", catalog_name),
            ("branch[]", 0),
            ("shorts[]", ''),
            # ("modules[]", 'bb'),
            # ("branch[]", 0),
            # ("shorts[]", ''),
            # ("modules[]", ''),
            # ("branch[]", 0),
            # ("shorts[]", ''),
            ("parentModuleID", parent_id),
            ("maxOrder", 0),
        ]
        payload = urllib.urlencode(payload)

        self.session.headers['Referer'] = self.host + '/tree-browse-%s-case-0.html' % product_id
        resp = self.session.post(self.host + '/tree-manageChild-%s-case.json' % product_id,
                                 data=payload)
        datas = json.loads(resp.text)
        if 'idList' in datas:
            catalog_id = datas['idList'][0]
            return True, catalog_id
        else:
            return False, json.loads(datas['data'])['message']

    def create_catalogs(self, root, product_id):
        """创建模块树"""
        if root == None:
            return
        queue = []
        queue.append((None, root))
        while queue:
            pid, node = queue.pop(0)
            if not node['exist']:
                # 调用创建
                re, node_id = self.add_catalog(node['name'], pid, product_id)
                if not re:
                    return
            else:
                node_id = node.get('catalog_id')
            if node.get('children'):
                queue.extend([(node_id, n) for n in node['children']])

    def create_case(self, product, title, pri, steps, module, precondition=None, case_type='feature'):
        datas = [
            ("precondition", precondition or ''),
            ("product", product),
            ("title", title),
            ("pri", pri),
            ("type", case_type),
            ("module", module)
        ]
        for i, vv in enumerate(steps):
            datas.append(('steps[%s]' % (i + 1), vv[0]))
            datas.append(('expects[%s]' % (i + 1), vv[1]))
            datas.append(('stepType[%s]' % (i + 1), 'item'))

        payload = urllib.urlencode(datas, True)

        self.session.headers['Referer'] = self.host + '/testcase-create-%s-0-0.html' % product

        resp = self.session.post(url=self.host + '/testcase-create-%s-0-0.json' % product,
                                 data=payload)
        res = json.loads(resp.text)
        print res
        pass


def build_catalog_tree(catalogs, check_dict=None):
    # catalogs = ['/A/B/C/D', '/A/B/C', '/A/B', '/A/C/D', '/A/C/D/E', '/A/D', '/B/C/D', '/B/D']
    root_object = {'path': '', 'name': '/', 'exist': True, 'catalog_id': '0', 'children': []}
    catalog_dict = {'/': root_object, }
    for catalog in catalogs:
        obj_list = catalog.strip('/').split('/')
        parent = catalog_dict['/']
        for o in obj_list:
            now_path = parent['path'] + '/' + o
            if now_path in catalog_dict:
                now_obj = catalog_dict[now_path]
            else:

                if check_dict and now_path in check_dict:
                    exist = True
                    _path = check_dict[now_path]
                    pos = _path.index('(')
                    catalog_id = _path[pos + 2:-1]
                else:
                    exist = False
                    catalog_id = None

                now_obj = catalog_dict[now_path] = {'path': now_path, 'name': o,
                                                    'exist': exist,
                                                    'catalog_id': catalog_id,
                                                    'children': []}
                parent['children'].append(now_obj)
            parent = now_obj

    root_object['path'] = '/'

    template_data = []

    def depth_tree(root_node):

        template_data.append({'wtype': 'liin'})
        template_data.append({'content': root_node['name'], 'exist': root_node['exist'], 'path': root_node['path']})

        if root_node['children']:
            template_data.append({'wtype': 'ulin'})
            for node in root_node['children']:
                depth_tree(node)
            template_data.append({'wtype': 'ulout'})

        template_data.append({'wtype': 'liout'})

    depth_tree(root_object)
    return root_object, template_data
