#Encoding=UTF8

import Config
import json
import time
import os
import uuid
import aiohttp
import asyncio
import urllib
import Logger

host = 'http://localhost:5000'
@asyncio.coroutine
def get_computer_vision(path):
    cv_json = {}
    try:
        url = host + '/classify_upload?image=%s' % path
        response = yield from aiohttp.request('GET', url)
        if response.status == 200:
            data = yield from response.read()
            cv_json = json.loads(data.decode())
        response.close()
        
    finally:
        return cv_json