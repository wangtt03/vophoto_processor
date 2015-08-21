#Encoding=UTF-8

import asyncio
import Config
import MongoHelper
import FaceUtils
import time
import uuid
import Utils
import Logger

@asyncio.coroutine
def process_images(image):
    process_location(image)
    process_voice(image)
    yield from process_faces(image)
    image['processed'] = True
    MongoHelper.save_image(image)

@asyncio.coroutine
def process_location(image):
    pass

@asyncio.coroutine
def process_voice(image):
    desc = image.get('desc', '')
    keys = Utils.get_meaningful_keywords(desc)
    tags = image.get('tags', set())
    tags = tags | keys
    image['tags'] = tags
    Logger.debug('tags: ' + str(tags))

@asyncio.coroutine
def process_faces(image):
    faces = yield from FaceUtils.detect_faces_in_photo(Utils.get_user_path(image['user_id']) + "/" + image['image_name'])
    Logger.debug('processing: ' + "e:/data/" + image['image_name'])
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
                
            train = MongoHelper.get_train_person_groups(10)
            tasks = []
            for tr in train:
                tasks.append(asyncio.async(train_person_group(tr['name'])))
            if len(tasks) > 0:
                loop.run_until_complete(asyncio.wait(tasks))
                
            time.sleep(1)
    finally:
        loop.close()
    
    
if __name__ == "__main__":
    main()