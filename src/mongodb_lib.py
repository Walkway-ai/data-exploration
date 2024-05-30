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
        cluster_node_id = str(config["clusterNodeId"])
        mongodb_nodeport_port = str(config["mongoDbNodeportPort"])
        client = MongoClient(
            f"mongodb://{mongodb_username}:{mongodb_password}@{cluster_node_id}:{mongodb_nodeport_port}/?authSource=admin"
        )
        db = client[config["mongoDbDatabase"]]

        fs = GridFS(db)

        return db, fs, client

    except Exception as e:

        logging.error(f"Failed to connect to MongoDB: {e}")

        raise


def save_object(fs, object, object_name):
    try:
        # Check if object with the same name already exists
        existing_file = fs.find_one({"filename": object_name})

        if existing_file:
            # If exists, delete the existing object before saving the new one
            fs.delete(existing_file._id)

        if "embeddings" in object_name:
            model_bytes = json.dumps(object.tolist()).encode()
        else:
            model_bytes = object.to_json().encode()

        fs.put(model_bytes, filename=object_name)
        logging.info(f"Object '{object_name}' saved successfully.")
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
