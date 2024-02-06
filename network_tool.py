# coding=utf-8
import requests
from loguru import logger
HTTP_STATUS_CODE_200 = 200


def get_request(uri):
    try:
        response = requests.get(uri)
        if response.status_code == HTTP_STATUS_CODE_200:
            return response
        else:
            logger.error("HttpRequestStatusError:response={}".format(response))
            raise requests.exceptions.RequestException
    except Exception as e:
        # 异常处理
        raise Exception("HttpRequestException：uri={}, exception={}".format(uri, e))
