#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from sklearn.model_selection import train_test_split
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from transformers import DataCollatorWithPadding
import torch
import yaml
import gc
from mongodb_lib import *

config_infra = yaml.load(open("infra-config-pipeline.yaml"), Loader=yaml.FullLoader)
db, fs, client = connect_to_mongodb(config_infra)

# Run garbage collection to free up memory.
gc.collect()

def main():
        
    df = read_object(fs, "product_textual_lang_summarized_subcategories")
    df = pd.DataFrame(df)
    df = df[["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED", "sub_categories_gpt4o"]]

    # Ensuring labels are in the correct format
    # Create a mapping for the labels to integers
    unique_labels = set(label for sublist in df['sub_categories_gpt4o'] for label in sublist)
    label2id = {label: idx for idx, label in enumerate(unique_labels)}
    id2label = {idx: label for label, idx in label2id.items()}

    # Convert labels to integers
    df['labels'] = df['sub_categories_gpt4o'].apply(lambda x: [label2id[label] for label in x])

    # Split the dataset into training, validation, and test sets
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    train_df, val_df = train_test_split(train_df, test_size=0.1, random_state=42)

    # Convert to Hugging Face Dataset
    train_dataset = Dataset.from_pandas(train_df)
    val_dataset = Dataset.from_pandas(val_df)
    test_dataset = Dataset.from_pandas(test_df)

    # Load a pre-trained model and tokenizer
    model_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Determine the number of unique labels
    num_labels = len(label2id)

    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)

    # Tokenize the datasets
    def tokenize_function(examples):
        return tokenizer(examples["pdt_product_detail_PRODUCTDESCRIPTION_SUMMARIZED"], padding="max_length", truncation=True)

    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)
    test_dataset = test_dataset.map(tokenize_function, batched=True)

    # Set the format of the dataset for PyTorch
    def format_dataset(dataset):
        dataset = dataset.map(lambda examples: {'labels': torch.tensor(examples['labels'], dtype=torch.float)})
        dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])
        return dataset

    train_dataset = format_dataset(train_dataset)
    val_dataset = format_dataset(val_dataset)
    test_dataset = format_dataset(test_dataset)

    # Create a data collator
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # Define the training arguments
    training_args = TrainingArguments(
        output_dir="./results",
        eval_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
    )

    # Define a custom trainer to handle multi-label classification
    class MultiLabelTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            logits = outputs.logits
            loss = torch.nn.BCEWithLogitsLoss()(logits, labels.float())
            return (loss, outputs) if return_outputs else loss

    # Initialize the Trainer
    trainer = MultiLabelTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    # Train the model
    trainer.train()

    # Evaluate the model
    trainer.evaluate()

    # Save the model and tokenizer
    model.save_pretrained("./finetuned_model")
    tokenizer.save_pretrained("./finetuned_model")

    # Make predictions on new data
    def predict(texts):
        inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        outputs = model(**inputs)
        return torch.sigmoid(outputs.logits)

    # Example usage
    texts = ["Example text to classify"]
    predictions = predict(texts)
    print(predictions)

if __name__ == "__main__":
    main()
