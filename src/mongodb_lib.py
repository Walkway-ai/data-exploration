import base64
import json
import logging

from gridfs import GridFS
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)


def connect_to_mongodb(config):
    try:
        mongodb_username = base64.b64decode(config["mongodbUsernameBase64"]).decode(
            "utf-8"
        )
        mongodb_password = base64.b64decode(config["mongodbPasswordBase64"]).decode(
            "utf-8"
        )
        mongoDbExternalIp = str(config["mongoDbExternalIp"])
        mongoDbPort = str(config["mongoDbPort"])
        client = MongoClient(
            f"mongodb://{mongodb_username}:{mongodb_password}@{mongoDbExternalIp}:{mongoDbPort}/?authSource=admin"
        )
        db = client[config["mongoDbDatabase"]]

        fs = GridFS(db)

        return db, fs, client

    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")

        raise


def save_object(fs, object, object_name):
    try:

        if "embeddings" in object_name:
            model_bytes = json.dumps(object.tolist()).encode()
        else:
            model_bytes = object.to_json().encode()

        fs.put(model_bytes, filename=object_name)

    except Exception as e:
        logging.error(f"Failed to save object '{object_name}' to MongoDB: {e}")


def read_object(fs, object_name):
    try:
        file_cursor = fs.find_one({"filename": object_name})

        if file_cursor is None:
            logging.error(f"Object '{object_name}' not found.")
            return None

        model_bytes = file_cursor.read()

        model_json = model_bytes.decode()

        object = json.loads(model_json)

        return object

    except Exception as e:
        logging.error(f"Failed to read object '{object_name}' from MongoDB: {e}")
        return None


def remove_object(fs, object_name):
    try:
        # Find the file by its name
        file = fs.find_one({"filename": object_name})
        if file:
            # Delete the file using its ID
            fs.delete(file._id)
            logging.info(f"Successfully deleted '{object_name}' from MongoDB GridFS")
        else:
            logging.warning(
                f"No file found with name '{object_name}' in MongoDB GridFS"
            )
    except Exception as e:
        logging.error(f"Failed to delete object '{object_name}' from MongoDB: {e}")
