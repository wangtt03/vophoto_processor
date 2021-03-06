#Encoding=UTF8

import Config
from hashlib import md5
import os
from pymemcache.client.base import Client
import pickle
import bmemcached

mc = bmemcached.Client((Config.config['memcached_host'],))

def get_user_photo_location_indexer(user_id):
    indexer = mc.get(user_id + '_location')
    if indexer is not None:
        return indexer
    
    filename = get_user_path(user_id) + "/" + "loc_indexer.dat"
    with open(filename,'rb') as fp:
        indexer = pickle.load(fp)
        
    mc.set(user_id, indexer)
    return indexer
    
def update_user_photo_indexer(user_id, location, image):
    filename = get_user_path(user_id) + "/" + "loc_indexer.dat"
    mckey = user_id + '_location'
    indexer = mc.get(mckey)
    if not indexer:
        if not os.path.exists(filename):
            indexer = [[],[]]
        else:
            with open(filename,'rb') as fp:
                indexer = pickle.load(fp)
    
    if indexer is None:
        return
    
    indexer[0].append(location)
    indexer[1].append(image)
    
    with open(filename,'wb') as fp:
        pickle.dump(indexer,fp)
    
    mc.set(mckey, indexer)
    return indexer

def get_meaningful_keywords(sentence):
    keys = set()
    key_words = sentence.split(' ')
    if not key_words:
        return keys;
    
    for k in key_words:
        pair = k.split('_')
        if pair is None or len(pair) < 2:
            continue
        
        if pair[1] in Config.config['meaningful_pos']:
            keys.add(pair[0])
        
    
    return keys

def get_user_path(user_id):
    md5ins = md5()
    md5ins.update(str(user_id).encode())
    md5str = md5ins.hexdigest()
    path = Config.config['photo_root'] + md5str[0:2] + "/" + md5str[2:4] + "/" + md5str[4:6] + "/" + user_id
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_human_names(raw):
    keys = []
    key_words = raw.split(' ')
    if key_words is None or len(key_words) == 0:
        return
    
    for k in key_words:
        pair = k.split('_')
        if pair is None or len(pair) < 2:
            continue
        
        if pair[1] in Config.config['human_name_pos']:
            keys.append(pair[0])
        
    return keys