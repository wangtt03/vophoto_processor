#Encoding=UTF-8

import asyncio
from src import Config
from src import MongoHelper
from src import FaceUtils
import time

@asyncio.coroutine
def process_images(image):
    process_location(image)
    process_voice(image)
    yield from process_faces(image)
    MongoHelper.save_image(image)

@asyncio.coroutine
def process_location(image):
    pass

@asyncio.coroutine
def process_voice(image):
    pass

@asyncio.coroutine
def process_faces(image):
    yield from FaceUtils.is_person_group_exists(image['user_id'])

def main():
    loop = asyncio.get_event_loop()
    try:
        while True:
            images = MongoHelper.get_unprocessed(Config.config['image_process_batch'])
            tasks = []
            for img in images:
                tasks.append(asyncio.async(process_images(img)))
            loop.run_until_complete(asyncio.wait(tasks))
            time.sleep(1)
    finally:
        loop.close()
    
    
if __name__ == "__main__":
    main()