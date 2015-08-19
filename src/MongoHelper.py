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