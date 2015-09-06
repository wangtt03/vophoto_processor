#Encoding=UTF-8

import asyncio
import Config
import MongoHelper
import FaceUtils
import time
import uuid
import Utils
import Logger
import ComputerVision

@asyncio.coroutine
def process_images(image):
    yield from process_location(image)
    yield from process_voice(image)
    yield from process_face_groups(image)
    yield from process_computor_vision(image)
    image['processed'] = True
    Logger.debug('final image: ' + str(image))
    MongoHelper.save_image(image)

@asyncio.coroutine
def process_computor_vision(image):
    path = Utils.get_user_path(image['user_id']) + "/" + image['image_name']
#     path = "/data/photos/" + image['image_name']
    cv_dict = yield from ComputerVision.get_computer_vision(path)
    Logger.debug(cv_dict)
    rkeys = cv_dict.keys()
    key_set = set()
    for key in rkeys:
        key_set |= set(key.split(' '))
        
    Logger.debug('key set: ' + str(key_set))
    tags = image.get('tags', [])
    for key in key_set:
        if key in Config.config['supported_cv_tags']:
            tags.append(key)
    
    Logger.debug('tags: ' + str(tags))
    image['tags'] = tags
    
    
@asyncio.coroutine
def process_location(image):
    location = image.get('location','0,0')
    name = image['image_name']
    user_id = image['user_id']
    loc = []
    loc.append(location['longitude'])
    loc.append(location['latitude'])
    # loc = [float(i) for i in location.split(',')]
    # Utils.update_user_photo_indexer(user_id, loc, name)
    

@asyncio.coroutine
def process_voice(image):
    desc = image.get('desc', '')
    keys = Utils.get_meaningful_keywords(desc)
    tags = image.get('tags', [])
    for key in keys:
        if not key in tags:
            tags.append(key)
    image['tags'] = tags
    Logger.debug('tags: ' + str(tags))

@asyncio.coroutine
def process_face_groups(image):
    faces = yield from FaceUtils.detect_faces_in_photo(Utils.get_user_path(image['user_id']) + "/" + image['image_name'])
    Logger.debug('processing: ' + Utils.get_user_path(image['user_id']) + "/"  + image['image_name'])
#     faces = yield from FaceUtils.detect_faces_in_photo("e:/data/images/" + image['image_name'])
#     Logger.debug('processing: ' + "e:/data/images/" + image['image_name'])
    if len(faces) == 0 or len(faces) > 10:
        return
    
    names = Utils.get_human_names(image.get('desc', ''))
    names.reverse()
    tags = image.get('tags', [])
    for face in faces:
        face_id = ''
        similars = yield from FaceUtils.find_similar_faces(image['user_id'], face)
        Logger.debug('similars: ' + str(similars))
        
        for simi in similars:
            conf = simi['confidence']
            if conf >= 0.9:
                face_id = simi['faceId']
                break
            
        if not face_id:
            Logger.debug('no face id detected')
            face_id = face
            yield from FaceUtils.add_face_to_group(image['user_id'], face)
            try:
                name = names.pop()
            except:
                name = ''
                
            face_info = {'user_id':image['user_id'], 'face_id':face, 'name':name, 'candidates': similars}
            for simi in similars:
                fid = simi['faceId']
                sm = MongoHelper.get_person(image['user_id'], fid)
                smcd = [i['faceId'] for i in sm['candidates']]
                if not fid in smcd:
                    sm['candidates'].append({'faceId': face, 'confidence': simi['confidence']})
                MongoHelper.save_person(sm)
                
            MongoHelper.save_person(face_info)

        if not face_id in tags:
            tags.append(face_id)
        
    image['tags'] = tags
    Logger.debug('tags: ' + str(tags))
            
    
@asyncio.coroutine
def process_faces(image):
    faces = yield from FaceUtils.detect_faces_in_photo(Utils.get_user_path(image['user_id']) + "/" + image['image_name'])
    Logger.debug('processing: ' + Utils.get_user_path(image['user_id']) + "/" + image['image_name'])
    if len(faces) == 0 or len(faces) > 10:
        return
    
    names = Utils.get_human_names(image.get('desc', ''))
    names.reverse()
    for face in faces:
        candidates = []
        person_id = ''
        identify_res = yield from FaceUtils.identify_faces(image['user_id'], [face], 3)
        if len(identify_res) > 0:
            result = identify_res[0]
            candidates = result['candidates']
            for cand in candidates:
                if cand['confidence'] > 0.9:
                    person_id = cand['personId']
                    break
        
        if not person_id:
            person_id = yield from FaceUtils.create_person(image['user_id'], [face], uuid.uuid4())
            Logger.debug('person created: ' + person_id)
            name = ''
            try:
                name = names.pop()
            except:
                pass
            person = {'user_id':image['user_id'], 'person_id':person_id, 'name':name, 'candidates': candidates} 
            MongoHelper.save_person(person)
            MongoHelper.add_train_person_groups(image['user_id'])
        
        tags = image.get('tags', set())
        tags.add(person_id)
        image['tags'] = tags
        Logger.debug('tags: ' + str(tags))

@asyncio.coroutine
def train_person_group(group_id):
    Logger.debug('start training: ' + group_id)
    yield from FaceUtils.train_person_group_wait(group_id)

def main():
#     start_training_thread()
    loop = asyncio.get_event_loop()
    try:
        while True:
            images = MongoHelper.get_unprocessed(Config.config['image_process_batch'])
            tasks = []
            for img in images:
                tasks.append(asyncio.async(process_images(img)))
            if len(tasks) > 0:
                loop.run_until_complete(asyncio.wait(tasks))
                
#             train = MongoHelper.get_train_person_groups(10)
#             tasks = []
#             for tr in train:
#                 tasks.append(asyncio.async(train_person_group(tr['name'])))
#             if len(tasks) > 0:
#                 loop.run_until_complete(asyncio.wait(tasks))
                
            time.sleep(1)
    finally:
        loop.close()
    
    
if __name__ == "__main__":
    main()
