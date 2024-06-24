import gc

import pandas as pd
import torch
import yaml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
from transformers import (
    BertForSequenceClassification,
    BertTokenizer,
    Trainer,
    TrainingArguments,
)

# Assuming this is your MongoDB connection function
from mongodb_lib import connect_to_mongodb, read_object

# Load MongoDB connection configuration from YAML
config_infra = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config_infra)

# Run garbage collection to free up memory.
gc.collect()


def main():
    # Read data from MongoDB
    df = read_object(fs, "product_textual_lang_summarized_subcategories_walkway")
    df = pd.DataFrame(df)
    df = df[
        ["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED", "sub-categories-walkway"]
    ]

    # Filter out empty descriptions and categories
    df = df[df["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"] != ""]
    df = df[
        df["sub-categories-walkway"].apply(lambda x: len(x) > 0)
    ]  # Ensure categories are not empty

    # Explode categories into separate rows
    df = df.explode("sub-categories-walkway")

    # Remove duplicates
    df = df.drop_duplicates()

    # Group by text and aggregate categories into lists
    df = (
        df.groupby(["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"])[
            "sub-categories-walkway"
        ]
        .apply(list)
        .reset_index()
    )

    # Separate into texts and labels
    texts = df["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"].tolist()
    labels = df["sub-categories-walkway"].tolist()

    # Use MultiLabelBinarizer to encode labels
    mlb = MultiLabelBinarizer()
    labels_encoded = mlb.fit_transform(labels)

    # Split data into training and validation sets
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels_encoded, test_size=0.2, random_state=42
    )

    # Load BERT tokenizer
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

    # Tokenize inputs
    train_encodings = tokenizer(train_texts, truncation=True, padding=True)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True)

    # Define a function to create InputFeatures
    def create_input_features(input_ids, attention_mask, labels):
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }

    # Create input features for training and validation
    train_features = [
        create_input_features(
            train_encodings["input_ids"][i],
            train_encodings["attention_mask"][i],
            torch.tensor(train_labels[i]),
        )
        for i in range(len(train_texts))
    ]

    val_features = [
        create_input_features(
            val_encodings["input_ids"][i],
            val_encodings["attention_mask"][i],
            torch.tensor(val_labels[i]),
        )
        for i in range(len(val_texts))
    ]

    # Define BERT model for sequence classification (adjust num_labels as per your number of classes)
    model = BertForSequenceClassification.from_pretrained(
        "bert-base-uncased", num_labels=len(mlb.classes_)
    )

    # Define training arguments
    training_args = TrainingArguments(
        per_device_train_batch_size=2208,
        per_device_eval_batch_size=2208,
        num_train_epochs=3,
        logging_dir="./logs",
        logging_steps=100,
        output_dir="./output",
    )

    # Define Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_features,
        eval_dataset=val_features,
    )

    # Fine-tune the model
    trainer.train()

    # Save the fine-tuned model
    model.save_pretrained("fine_tuned_model_directory")

    # Save the tokenizer as well
    tokenizer.save_pretrained("fine_tuned_model_directory")

    # Optionally, save the MultiLabelBinarizer for future use
    import joblib

    joblib.dump(mlb, "mlb.pkl")

    print(df)


if __name__ == "__main__":
    main()
