import base64
import json
import logging

from gridfs import GridFS
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)


def connect_to_mongodb(config):
    try:
        # Decoding base64 encoded credentials
        mongodb_username = base64.b64decode(
            config.get("mongodbUsernameBase64", "")
        ).decode("utf-8")
        mongodb_password = base64.b64decode(
            config.get("mongodbPasswordBase64", "")
        ).decode("utf-8")

        # Connecting to MongoDB
        client = MongoClient(
            f"mongodb://{mongodb_username}:{mongodb_password}@{config['mongoDbExternalIp']}:{config['mongoDbPort']}/?authSource=admin"
        )
        db = client[config["mongoDbDatabase"]]
        fs = GridFS(db)

        logging.info("Successfully connected to MongoDB.")

        return db, fs, client

    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise


def save_object(fs, object, object_name):
    try:
        # Serializing object to JSON
        if "embeddings" in object_name and "product_similarities" not in object_name:
            model_bytes = json.dumps(object.tolist()).encode()
        elif "product_similarities" in object_name:
            model_bytes = json.dumps(object).encode()
        else:
            model_bytes = object.to_json().encode()

        # Saving object to GridFS
        fs.put(model_bytes, filename=object_name)
        logging.info(f"Successfully saved '{object_name}' to MongoDB GridFS.")

    except Exception as e:
        logging.error(f"Failed to save '{obj_name}' to MongoDB: {e}")


def read_object(fs, obj_name):
    try:
        # Finding object by name
        file_cursor = fs.find_one({"filename": obj_name})

        if file_cursor is None:
            logging.error(f"Object '{obj_name}' not found in MongoDB GridFS.")
            return None

        # Reading and deserializing object
        model_bytes = file_cursor.read()
        obj = json.loads(model_bytes.decode())

        return obj

    except Exception as e:
        logging.error(f"Failed to read '{obj_name}' from MongoDB: {e}")
        return None


def remove_object(fs, obj_name):
    try:
        # Finding and deleting object by name
        file = fs.find_one({"filename": obj_name})
        if file:
            fs.delete(file._id)
            logging.info(f"Successfully deleted '{obj_name}' from MongoDB GridFS.")
        else:
            logging.warning(
                f"No object found with name '{obj_name}' in MongoDB GridFS."
            )

    except Exception as e:
        logging.error(f"Failed to delete '{obj_name}' from MongoDB: {e}")


def copy_object(fs, source_name, destination_name):
    """
    Copy an object in MongoDB GridFS from source name to destination name.

    Parameters:
    fs (GridFS): The GridFS object.
    source_name (str): The filename of the object to copy.
    destination_name (str): The filename to copy the object to.

    Returns:
    bool: True if the copy operation was successful, False otherwise.
    """
    try:
        # Find the source file
        source_file = fs.find_one({"filename": source_name})
        if not source_file:
            print(f"Source file '{source_name}' not found.")
            return False

        # Read the source file's content
        source_content = source_file.read()

        # Write the content to the destination file
        fs.put(source_content, filename=destination_name)
        print(f"Object copied from '{source_name}' to '{destination_name}'")
        return True

    except Exception as e:
        print(
            f"Failed to copy object from '{source_name}' to '{destination_name}': {e}"
        )
        return False
