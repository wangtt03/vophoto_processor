#Encoding=UTF8

from src import Config
import json
import time
import os
import uuid
import aiohttp
import asyncio
    
@asyncio.coroutine
def is_person_group_exists(user_id):
    res = False
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    try:
        url = "https://api.projectoxford.ai/face/v0/persongroups/%s" % user_id
        response = yield from aiohttp.request('GET', url, headers=headers)
        res = response.status == 200
        response.close()
    finally:
        return res
        
    return res
