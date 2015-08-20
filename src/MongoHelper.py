#Encoding=UTF8

import pymongo
import src.Config

conn = pymongo.MongoClient(src.Config.config['mongo_url'])

def get_unprocessed(num):
    images = []
    db = conn.VoiceImageDB
    coll = db.voice_images
    unpro = coll.find({'processed': False})
    for doc in unpro:
        images.append(doc)
    
    return images

def save_image(image):
    db = conn.VoiceImageDB
    coll = db.voice_images
    coll.save(image)
    
def save_person(person):
    db = conn.VoiceImageDB
    coll = db.person_list
    coll.create_index('user_id')
    coll.create_index('person_id')
    coll.save(person)
    
def get_train_person_groups(num):
    train = []
    db = conn.VoiceImageDB
    coll = db.traning_group
    coll.create_index('name', unique=True)
    unpro = coll.find().limit(num)
    for doc in unpro:
        train.append(doc)
        coll.remove(doc)
    
    return train

def add_train_person_groups(group_id):
    db = conn.VoiceImageDB
    coll = db.traning_group
    coll.create_index('name', unique=True)
    train = coll.find_one({'name': group_id})
    if not train:
        group = {'name': group_id}
        coll.save(group)
        