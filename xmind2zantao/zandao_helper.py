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
        return session

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


def build_catalog_tree(catalogs, check_dict=None):
    # catalogs = ['/A/B/C/D', '/A/B/C', '/A/B', '/A/C/D', '/A/C/D/E', '/A/D', '/B/C/D', '/B/D']
    root_object = {'path': '', 'name': '/', 'exist': True, 'children': []}
    catalog_dict = {'/': root_object, }
    for catalog in catalogs:
        obj_list = catalog.strip('/').split('/')
        parent = catalog_dict['/']
        for o in obj_list:
            now_path = parent['path'] + '/' + o
            if now_path in catalog_dict:
                now_obj = catalog_dict[now_path]
            else:
                now_obj = catalog_dict[now_path] = {'path': now_path, 'name': o,
                                                    'exist': now_path in check_dict if check_dict else False,
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
