#Encoding=UTF8

config = {
    'access_token': 'secret',
    'mongo_url':'mongodb://mongodb1:27017/',
    'photo_root': '/data/photos/',
    'servers': [{'name' : 'localhost', 'capacity': 100}],
    'image_process_batch': 10,
    'meaningful_pos':['ns','nt','n'],
    'human_name_pos':['nh'],
    'memcached_host': 'memcached1:11211',
    'face_api_key':'4e2bee77f4e74a5a89f725c44637b485',
    'supported_cv_tags': ['cat', 'dog', 'bird', 'fish','computer'] 
}