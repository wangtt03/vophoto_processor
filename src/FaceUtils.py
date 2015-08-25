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
    
host = 'https://api.projectoxford.ai/asia/face/v0'

@asyncio.coroutine
def is_person_group_exists(user_id):
    res = False
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    try:
        url = host + '/persongroups/%s' % user_id
        response = yield from aiohttp.request('GET', url, headers=headers)
        res = response.status == 200
        response.close()
    finally:
        return res
        
    return res

@asyncio.coroutine
def create_person_group(user_id):
    res = False
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    body = {'name': user_id}
    
    try:
        url = host + "/persongroups/%s" % user_id
        response = yield from aiohttp.request('PUT', url, data=json.dumps(body), headers=headers)
        res = response.status == 200
        response.close()
    finally:
        return res
    
@asyncio.coroutine
def delete_person_group(user_id):
    res = False
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    try:
        url = host + "/persongroups/%s" % user_id
        response = yield from aiohttp.request('DELETE', url, headers=headers)
        res = response.status == 200
        response.close()
    finally:
        return res
    
@asyncio.coroutine
def detect_faces_in_photo(image):
    faces = []
    headers = {
        # Request headers
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    params = urllib.parse.urlencode({
        # Request parameters
        'analyzesFaceLandmarks': 'false',
        'analyzesAge': 'false',
        'analyzesGender': 'false',
        'analyzesHeadPose': 'false',
    })
    
    try:
        image_bin = open(image, 'rb')
        url = host + "/detections?%s" % params
        response = yield from aiohttp.request('POST', url, data=image_bin, headers=headers)

        if response.status == 200:
            data = yield from response.read()
            face_json = json.loads(data.decode())
            for face in face_json:
                faces.append(face['faceId'])
        response.close()
    except Exception as e:
        Logger.error("[Errno {0}] {1}".format(e.errno, e.strerror))
    finally:
        return faces
    
@asyncio.coroutine
def identify_faces(user_id, faces, max_candidata=1):
    faces_res = []
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    body = {'faceIds': faces, 'personGroupId': user_id, 'maxNumOfCandidatesReturned':max_candidata}
    
    try:
        url = host + "/identifications"
        response = yield from aiohttp.request('POST', url, data=json.dumps(body), headers=headers)
        data = yield from response.read()
        json_data = json.loads(data.decode())
        response.close()
        if response.status == 200:
            faces_res = json_data
            return faces_res
            
#         if response.status == 400:
#             result = json_data['code']
#             return result
            
    except Exception as e:
        Logger.error("[Errno {0}] {1}".format(e.errno, e.strerror))

    return faces_res

@asyncio.coroutine
def create_person(user_id, faces, name):
    person_id = ''
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    body = {'faceIds': faces, 'name': user_id, 'userData':""}
    try:
        url = host + "/persongroups/%s/persons" % user_id
        response = yield from aiohttp.request('POST', url, data=json.dumps(body), headers=headers)
        data = yield from response.read()
        response.close()
        
        if response.status == 200:
            json_str = json.loads(data.decode())
            person_id = json_str.get('personId', '')
    except Exception as e:
        Logger.error("[Errno {0}] {1}".format(e.errno, e.strerror))
    finally:
        return person_id
    
@asyncio.coroutine
def train_person_group(user_id):
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }

    try:
        url = host + "/persongroups/%s/training" % user_id
        response = yield from aiohttp.request('POST', url, data=None, headers=headers)
        data = yield from response.read()
        response.close()
    except Exception as e:
        Logger.error("[Errno {0}] {1}".format(e.errno, e.strerror))

@asyncio.coroutine
def train_person_group_wait(user_id):
    yield from train_person_group(user_id)
    status = yield from get_training_status(user_id)
    Logger.debug('train ' + user_id + " status: " + status)
    while status == 'running':
        yield from asyncio.sleep(0.1)
        status = yield from get_training_status(user_id)
        Logger.debug('train ' + user_id + " status: " + status)
    
@asyncio.coroutine
def get_training_status(user_id):
    status = ''
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    try:
        url = host + "/persongroups/%s/training" % user_id
        response = yield from aiohttp.request('GET', url, headers=headers)
        
        data = yield from response.read()
        stat_json = json.loads(data.decode())
        status = stat_json['status']
        response.close()
    except Exception as e:
        Logger.error("[Errno {0}] {1}".format(e.errno, e.strerror))
    finally:
        return status
    
@asyncio.coroutine    
def train_default(user_id):
    yield from create_person_group(user_id)
    faces = yield from detect_faces_in_photo(os.path.dirname(os.path.realpath(__file__)) + "/demo.jpg")
    person_id = yield from create_person(user_id, faces, uuid.uuid4())
    yield from train_person_group_wait(user_id)
    yield from delete_person(user_id, person_id)
   
@asyncio.coroutine 
def delete_person(user_id, person_id):
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    try:
        url = host + "/persongroups/%s/persons/%s" % (user_id, person_id)
        response = yield from aiohttp.request('DELETE', url, data='', headers=headers)
        
        data = yield from response.read()
        response.close()
    except Exception as e:
        Logger.error("[Errno {0}] {1}".format(e.errno, e.strerror))
        

@asyncio.coroutine
def create_face_group(user_id):
    res = False
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    body = {'name': user_id}
    
    try:
        url = host + "/facegroups/%s" % user_id
        response = yield from aiohttp.request('PUT', url, data=json.dumps(body), headers=headers)
        res = response.status == 200
        response.close()
    finally:
        return res

@asyncio.coroutine
def find_similar_faces(user_id, face):
    faces_res = []
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }

    body = {'faceId': face, 'faceGroupId': user_id, 'maxNumOfCandidatesReturned':3}
    try:
        url = host + "/findsimilars"
        response = yield from aiohttp.request('POST', url, data=json.dumps(body), headers=headers)
        data = yield from response.read()
        json_data = json.loads(data.decode())
        response.close()
        if response.status == 200:
            faces_res = json_data
            return faces_res
        
    except Exception as e:
        Logger.error("[Errno {0}] {1}".format(e.errno, e.strerror))
        
    return faces_res

@asyncio.coroutine
def add_face_to_group(user_id, face):
    res = False
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    body = {'faces': [{'faceId':face}]}
    
    try:
        url = host + "/facegroups/%s/faces" % user_id
        response = yield from aiohttp.request('PUT', url, data=json.dumps(body), headers=headers)
        res = response.status == 200
        response.close()
    finally:
        return res
  
@asyncio.coroutine
def delete_face_group(user_id):
    res = False
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    try:
        url = host + "/facegroups/%s" % user_id
        response = yield from aiohttp.request('DELETE', url, headers=headers)
        res = response.status == 200
        response.close()
    finally:
        return res

@asyncio.coroutine
def get_face_group(user_id):
    stat_json = None
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': Config.config['face_api_key'],
    }
    
    try:
        url = host + "/facegroups/%s" % user_id
        response = yield from aiohttp.request('GET', url, headers=headers)
        data = yield from response.read()
        stat_json = json.loads(data.decode())
        response.close()
    except Exception as e:
        Logger.error("[Errno {0}] {1}".format(e.errno, e.strerror))
    finally:
        return stat_json
    
@asyncio.coroutine
def test():
    user_id = 'wang'
    try:
#         res = yield from get_face_group(user_id)
#         print(res)

        yield from delete_face_group(user_id)
        yield from create_face_group(user_id)
# #         
#         faces = yield from detect_faces_in_photo('e:/data/1.jpg')
#         print(faces)
#  
#         similars = yield from find_similar_faces(user_id, faces[0])
#         if not similars:
#             yield from add_face_to_group(user_id, faces[0])
#         else:
#             print(similars)  
#              
#          
#         faces = yield from detect_faces_in_photo('e:/data/2.jpg')
#         print(faces)
#  
#         similars = yield from find_similar_faces(user_id, faces[0])
#         if not similars:
#             yield from add_face_to_group(user_id, faces[0])
#         else:
#             print(similars)  
#              
#          
#         faces = yield from detect_faces_in_photo('e:/data/3.jpg')
#         print(faces)
#  
#         similars = yield from find_similar_faces(user_id, faces[0])
#         if not similars:
#             yield from add_face_to_group(user_id, faces[0])
#         else:
#             print(similars)  
             
#         faces = yield from detect_faces_in_photo('e:/data/6.jpg')
#         print(faces)
#   
#         similars = yield from find_similar_faces(user_id, faces[0])
#         if not similars:
#             yield from add_face_to_group(user_id, faces[0])
#         else:
#             print(similars)    
            
        
#         faces = yield from detect_faces_in_photo('e:/data/1.jpg')
#         print(faces)
#         yield from create_person(user_id, faces, '1')
#         
#         faces = yield from detect_faces_in_photo('e:/data/2.jpg')
#         print(faces)
#         yield from create_person(user_id, faces, '2')
#         
#         faces = yield from detect_faces_in_photo('e:/data/3.jpg')
#         print(faces)
#         yield from create_person(user_id, faces, '3')
#         
#         faces = yield from detect_faces_in_photo('e:/data/4.jpg')
#         print(faces)
#         yield from create_person(user_id, faces, '4')
#         
#         yield from train_person_group_wait(user_id)
        
#         faces = yield from detect_faces_in_photo('e:/data/2.jpg')
#         print(faces)
#         faces = yield from identify_faces(user_id, faces, 1)
#         print(faces)
    finally:
        pass
    
def main():
    loop = asyncio.get_event_loop()
    try:
        tasks = [asyncio.async(test())]
        loop.run_until_complete(asyncio.wait(tasks))
    finally:
        loop.close()
    
    
if __name__ == "__main__":
    main()
    