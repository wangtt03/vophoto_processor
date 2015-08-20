#Encoding=UTF8

from src import Config
from hashlib import md5
import os

def get_user_path(user_id):
    md5ins = md5.new()
    md5ins.update(user_id)
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