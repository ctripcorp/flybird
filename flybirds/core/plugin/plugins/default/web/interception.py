# -*- coding: utf-8 -*-
# @Time : 2022/5/16 17:05
# @Author : hyx
# @File : interception.py
# @desc :web request interception related operations
import json
import os
import re
from urllib.parse import parse_qs

from deepdiff import DeepDiff
from jsonpath_ng import parse as parse_path

import flybirds.core.global_resource as gr
import flybirds.utils.flybirds_log as log
from flybirds.core.exceptions import FlybirdsException

__open__ = ["Interception"]

from flybirds.utils import file_helper
from flybirds.utils.file_helper import read_json_data


class Interception:
    """
    web interception impl
    """
    name = "web_interception"

    # -------------------------------------------------------------------------
    # request interception
    # -------------------------------------------------------------------------
    @staticmethod
    def add_some_interception_request_body(service_str):
        if service_str is None:
            log.error(
                '[addSomeInterceptionRequestBody] param can not be none.')
            return
        service_list = service_str.strip().split(',')
        interception_request = gr.get_value('interceptionRequest')

        for service in service_list:
            interception_request[service.strip()] = {}
        gr.set_value('interceptionRequest', interception_request)

    @staticmethod
    def remove_some_interception_request_body(service_str):
        service_list = service_str.strip().split(',')
        interception_request = gr.get_value('interceptionRequest')

        try:
            for service in service_list:
                request_body = interception_request.pop(service.strip())
                log.info(
                    f'remove data cached by request [{service.strip()}]: '
                    f'{request_body}')
        except Exception as e:
            message = f'[removeSomeInterceptionRequestBody]  ' \
                      f'has KeyError! error key: {str(e)}'
            raise FlybirdsException(message)
        gr.set_value('interceptionRequest', interception_request)

    @staticmethod
    def clear_interception_request_body():
        interception_request = gr.get_value('interceptionRequest')
        interception_request.clear()
        gr.set_value('interceptionRequest', interception_request)

    # -------------------------------------------------------------------------
    # request service listening
    # -------------------------------------------------------------------------
    @staticmethod
    def add_some_interception_mock(service_str, mock_case_id_str):
        if service_str is None or mock_case_id_str is None:
            log.error('[addSomeInterceptionMock] param can not be none. ')
            return

        service_list = service_str.strip().split(',')
        mock_case_id_list = mock_case_id_str.strip().split(',')
        if len(service_list) != len(mock_case_id_list):
            message = f"serviceCount[{service_str}] not equal " \
                      f"mockCaseCount[{mock_case_id_str}]"
            raise FlybirdsException(message)

        interception_values = gr.get_value('interceptionValues')
        for i, service in enumerate(service_list):
            interception_values[service.strip()] = mock_case_id_list[i].strip()

        gr.set_value('interceptionValues', interception_values)

    @staticmethod
    def remove_some_interception_mock(service_str):
        service_list = service_str.strip().split(',')
        interception_values = gr.get_value('interceptionValues')

        try:
            for service in service_list:
                case_id = interception_values.pop(service.strip())
                log.info(f'remove mock data [{case_id}] from request '
                         f'[{service.strip()}]')
        except Exception as e:
            message = f'[removeSomeInterceptionMock]  ' \
                      f'has KeyError! error key: {str(e)}'
            raise FlybirdsException(message)
        gr.set_value('interceptionValues', interception_values)

    @staticmethod
    def clear_interception_mock():
        interception_values = gr.get_value('interceptionValues')
        interception_values.clear()
        gr.set_value('interceptionValues', interception_values)

    # -------------------------------------------------------------------------
    # compare service requests
    # -------------------------------------------------------------------------
    @staticmethod
    def request_compare(operation, target_data_path):
        # 调用 get_server_request_body() 函数获取服务器请求信息，返回一个字典对象
        request_info = get_server_request_body(operation)
        actual_request_obj = None

        # 如果返回的请求信息不为 None，并且有 postData 属性，则将 postData 赋值给 actual_request_obj 变量
        if request_info is not None and request_info.get('postData'):
            actual_request_obj = request_info.get('postData')

        # 在日志中输出 actual_request_obj 的信息
        log.info(f'[request_compare] actualObj:{actual_request_obj}')

        # 如果 actual_request_obj 为 None，则抛出异常
        if actual_request_obj is None:
            message = f'[request_compare] not get listener data for ' \
                      f'[{operation}]'
            raise FlybirdsException(message)

        # 将 actual_request_obj 反序列化成 Python 对象
        if actual_request_obj.startswith('<?xml') or actual_request_obj.startswith('<'):
            actual_request_obj = xmltodict.parse(actual_request_obj)
        else:
            actual_request_obj = json.loads(actual_request_obj)

        log.info(f'[request_compare] actualObj dict:{actual_request_obj}')

        # 获取文件路径
        file_path = os.path.join(os.getcwd(), target_data_path)

        expect_request_obj = None

        # 如果文件路径存在，则从该文件中读取数据并将其赋值给 expect_request_obj
        if os.path.exists(file_path):

            expect_request_obj = file_helper.read_file_from_path(file_path);
            if expect_request_obj.startswith('<?xml') or expect_request_obj.startswith('<'):
                expect_request_obj = xmltodict.parse(expect_request_obj)
                # 将 expect_request_obj 解析为 字典
            else:
                expect_request_obj = file_helper.get_json_from_file_path(file_path)
        else:
            message = f'[request_compare] expect_request_obj not get file from' \
                      f'[{file_path}]'
            raise FlybirdsException(message)

        # 在日志中输出 expect_request_obj 的信息
        log.info(f'[request_compare] expectObj dict:{expect_request_obj}')

        # 如果 expect_request_obj 为 None，则抛出异常
        if expect_request_obj is None:
            message = f'[request_compare] cannot get data form path' \
                      f'[{target_data_path}]]'
            raise FlybirdsException(message)

        # 实例xml文件，多了root根目录
        if 'root' in expect_request_obj:
            expect_request_obj = expect_request_obj['root']

            # 调用 convert_values() 函数，转换数字和布尔值
            expect_request_obj = delete_values(expect_request_obj)
            expect_request_obj = convert_values(expect_request_obj)
            log.info(f'[request_compare] expectObj dict after deal:{expect_request_obj}')

        # 调用 handle_diff() 函数，比较实际请求对象和期望请求对象之间的差异，并输出日志
        handle_diff(actual_request_obj, expect_request_obj, operation,
                    target_data_path)

    @staticmethod
    def request_query_string_compare(operation, target_data_path):
        # 定义函数 request_query_string_compare，接收两个参数 operation 和 target_data_path
        request_info = get_server_request_body(operation)
        # 调用 get_server_request_body 函数获取服务端请求信息，存储在 request_info 中
        actual_request_obj = None
        # 初始化 actual_request_obj 为 None
        if request_info is not None and request_info.get('postData'):
            # 如果 request_info 不为 None，且 request_info 包含 postData 字段
            actual_request_obj = request_info.get('postData')
            # 将 request_info 中的 postData 赋值给 actual_request_obj
        if actual_request_obj is None:
            # 如果 actual_request_obj 为 None
            message = f'[requestQuerystringCompare] not get listener data ' \
                      f'for [{operation}]'
            raise FlybirdsException(message)
            # 抛出异常，提示未获取到监听器数据

        # 判断数据格式
        if actual_request_obj.startswith('<?xml') or actual_request_obj.startswith('<'):
            actual_request_obj = xmltodict.parse(actual_request_obj)
            # 将 actual_request_obj 解析为 字典
        else:
            actual_request_obj = parse_qs(actual_request_obj)
            # 将 actual_request_obj 解析为字典，存储在 actual_request_obj 中

        file_path = os.path.join(os.getcwd(), target_data_path)
        # 获取目标数据文件的路径，存储在 file_path 中
        expect_request_obj = None
        # 初始化 expect_request_obj 为 None
        if os.path.exists(file_path):
            # 如果文件路径存在
            expect_request_obj = file_helper.read_file_from_path(file_path)
            # 读取目标数据文件，存储在 expect_request_obj 中
        if expect_request_obj is None:
            # 如果 expect_request_obj 为 None
            message = f'[requestQuerystringCompare] cannot get data form ' \
                      f'path [{target_data_path}]'
            raise FlybirdsException(message)
            # 抛出异常，提示无法从指定路径获取数据

        # 判断数据格式
        if expect_request_obj.startswith('<?xml') or expect_request_obj.startswith('<'):
             expect_request_obj = xmltodict.parse(expect_request_obj)
            # 将 expect_request_obj 解析为 字典
        else:
             expect_request_obj = parse_qs(expect_request_obj)
             # 将 expect_request_obj 解析为字典，存储在 expect_request_obj 中


        handle_diff(actual_request_obj, expect_request_obj, operation,
                    target_data_path)
        # 调用 handle_diff 函数，比较实际请求对象和期望请求对象之间的差异，并传递参数 operation 和 target_data_path

    @staticmethod
    def request_compare_value(operation, target_path, expect_value):
        # 调用 get_server_request_body 方法获取 request_info 信息
        request_info = get_server_request_body(operation)

        data = None
        # 获取 postData 数据
        if request_info and request_info.get('postData'):
            data = request_info.get('postData')
        # 如果没有获取到 postData 数据则抛出异常
        if data is None:
            message = f'[requestCompareValue] not get listener data for ' \
                      f'[{operation}]'
            raise FlybirdsException(message)
        # 判断数据格式
        if data.startswith('<?xml') or data.startswith('<'):
            # 如果是 XML 格式，则解析 XML
            root = ET.fromstring(data)
            # 解析 XML 路径表达式
            xml_path_expr = ET.XPath(target_path)
            # 从 XML 中获取目标数据
            target_values = [elem.text for elem in xml_path_expr(root)]
            # 打印日志
            log.info(f'[requestCompareValue] get xmlPathData: {target_values}')
        else:
            # 否则默认为 JSON 格式，解析 JSON
            # 将 data 解析成字典类型
            json_data = json.loads(data)
            # 解析 JSON 路径表达式
            json_path_expr = parse_path(target_path)
            # 从 JSON 中获取目标数据
            target_values = [match.value for match in json_path_expr.find(json_data)]
            # 打印日志
            log.info(f'[requestCompareValue] get jsonPathData: {target_values}')
        # 如果目标数据不存在则抛出异常
        if len(target_values) == 0:
            message = f'[requestCompareValue] cannot get the value from ' \
                      f'path [{target_path}] of [{operation}]'
            raise FlybirdsException(message)

        if str(target_values[0]) != expect_value:
            message = f'value not equal, service [{operation}] request ' \
                      f'parameter [{target_json_path}] actual value:' \
                      f'[{target_values[0]}], but expect value:' \
                      f'[{expect_value}]'
            raise FlybirdsException(message)


def get_server_request_body(service):
    interception_request = gr.get_value('interceptionRequest')
    if interception_request:
        return interception_request.get(service)
    return None


def handle_ignore_node(service):
    exclude_paths = []
    exclude_regex_paths = []
    service_ignore_nodes = gr.get_service_ignore_nodes(service)
    if service_ignore_nodes is None:
        return exclude_paths, exclude_regex_paths
    for item in service_ignore_nodes:
        if 'regex' in item:
            regex_item = item.split('regex:')[-1].strip()
            exclude_regex_paths.append(regex_item)
        else:
            path = 'root'
            for level_item in item.split('.'):
                # identifies whether the item is an array
                level_item = level_item.strip()
                item_is_array = re.search(r"([^\[\]]+)\[(\d+)\]",
                                          level_item) is not None
                item_str = ''
                if item_is_array:
                    property_name = "['" + re.search(r"([^\[\]]+)\[(\d+)\]",
                                                     level_item).group(
                        1) + "']"
                    array_index = ''.join(
                        list(map(
                            lambda x: "[" + x + "]",
                            re.findall(r"\[(\d+)\]", level_item))
                        )
                    )
                    item_str = property_name + array_index
                else:
                    item_str = "['" + level_item + "']"
                path += item_str
            exclude_paths.append(path.strip())
    return exclude_paths, exclude_regex_paths


def handle_diff(actual_request_obj, expect_request_obj, operation,
                target_file_name):
    exclude_paths, exclude_regex_paths = handle_ignore_node(operation)
    ignore_order = gr.get_web_info_value("ignore_order", False)
    # diffs with jsons
    diff = DeepDiff(actual_request_obj, expect_request_obj,
                    ignore_order=ignore_order, verbose_level=2,
                    exclude_paths=exclude_paths,
                    exclude_regex_paths=exclude_regex_paths)
    if diff:
        format_diff = json.dumps(diff, indent=2)
        message = f'Difference when comparing service request ' \
                  f'[{operation}] with [{target_file_name}]. ' \
                  f'\n Difference node:\n {format_diff} \n'
        raise FlybirdsException(message)
    log.info(f'compare the service request [{operation}] with '
             f'[{target_file_name}], the result is the same.')


def get_case_response_body(case_id):
    operation_module = gr.get_value("projectScript").custom_operation
    get_mock_case_body = getattr(operation_module, "get_mock_case_body")
    mock_case_body = get_mock_case_body(case_id)
    if mock_case_body is not None:
        log.info('[get_case_response_body] successfully get mockCaseBody '
                 'from custom operation')
        return mock_case_body
    log.warn('[get_case_response_body] cannot get mockCaseBody from custom '
             'operation. Now try to get from the folder mockCaseData.')
    # read from folder mockCaseData
    mock_data_path = os.path.join(os.getcwd(), "mockCaseData")
    all_mock_data = read_json_data(mock_data_path)
    if all_mock_data.get(case_id):
        log.info('[get_case_response_body] successfully get mockCaseBody '
                 'from folder mockCaseData')
        return all_mock_data.get(case_id)
    log.warn('[get_case_response_body] cannot get mockCaseBody from folder '
             'mockCaseData.')
    return


# 定义函数 convert_values()，将值为数字或布尔类型的字符串转换为对应的数字或布尔值
def convert_values(data):
    for key, value in data.items():
        if key !='head' and value is not None:
            if isinstance(value, dict):
                convert_values(value)
            elif isinstance(value, str):
                if value.lower() == 'true':
                    data[key] = True
                elif value.lower() == 'false':
                    data[key] = False
                elif value.isdigit():
                    data[key] = int(value)
    return  data


# 定义函数 convert_values()，将值为None转为''
def delete_values(data):
    for key, value in data.items():
        if value is None:
            data[key]=''
        elif isinstance(value, dict):
            delete_values(value)
        elif isinstance(value, str):
            log.info("String dict value",value)
    return  data