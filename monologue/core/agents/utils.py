import openai
import json
import typing


def summarize_data(records: typing.List[dict]):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are the guy that summarizes tabular data, focus on text fields and perhaps using an rank, distance of rating fields to emphasize specific parts",
            },
            {
                "role": "user",
                "content": f"Summarize with emphasis the data in: {records}",
            },
            {"role": "user", "content": f"output a summary"},
        ],
    )
    data = response["choices"][0]["message"]["content"]
    return data


def pydantic_type_generator(d: dict, file_out=None):
    """

    This one is opinionated about child dictionaries. We can improve it with more examples of interest
    In my case Im generally not going to have data with a single nested type.
    This is easy to improve by saying creating a black or white list or whatever per attribute and passing this in to the method

    example:

        d = [{
            "key": 134,
            "kust": [1,2,3],
            "value": 1,
            "value_b": 22,
            "other_value": {"b": "asf"},
            "athign" :[{"b": "asf"}]

        },
            {
            "key": 134,
            "kust": [1,2,3],
            "value": None,
            "value_b": 1355,
            "other_value": {"a":1},
            "athign" :[{"b": "asf"}]
        }]

    """

    from monologue.core.utils.ops import parse_fenced_code_blocks

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": """You are a helpful assistant that generates Pydantic python types given example data in Json format.
                If an object in the sample data has an attribute that is a dictionary, you should annotate the Pydantic type simply as a dict without any extra typing information to allow for a bag of attributes. 
                but if the data have properties that are lists of dictionaries you should define this lists of typed objects.""",
            },
            {
                "role": "user",
                "content": f"Generate multiple search queries related to: {json.dumps(d)}",
            },
            {"role": "user", "content": "OUTPUT Pydantic Python Class:"},
        ],
    )

    data = response["choices"][0]["message"]["content"]
    python_objs = parse_fenced_code_blocks(data, select_type="python")
    if file_out:
        with open(file_out, "w") as f:
            for python_obj in python_objs:
                f.write(python_obj)
    return response


def diverse_query_generator(q, n):
    """
    Example:
    q, n = "Who is iron man from the avengers and what does the data say about its interesting in bananas?", 5

    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are the guy that generates multiple queries given a single query",
            },
            {"role": "user", "content": f"Generate multiple queries related to: {q}"},
            {"role": "user", "content": f"OUTPUT ({n} queries):"},
        ],
    )
    return response
