import gc

from openai import OpenAI

# Run garbage collection to free up memory.
gc.collect()


def query_gpt(apikey, system_role, prompt):

    client = OpenAI(api_key=apikey)

    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": prompt},
        ],
    )

    return result

def query_gpt_with_history(apikey, prompt, conversation_history):

    client = OpenAI(api_key=apikey)

    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation_history + [
            {"role": "user", "content": prompt},
        ],
    )

    return result
