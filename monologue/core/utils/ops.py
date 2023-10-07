"""
bits and bobs
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from langchain.chat_models import ChatOpenAI

# deprecate as a dep
import pandas as pd
import hashlib
import uuid
from multiprocessing import Pool, cpu_count


def counter(i):
    import time

    time.sleep(1)
    print("done")


def map_parallel(f, data, cpus=cpu_count() - 1):
    """
    n the number of works to process the function f over the the data
    """
    with Pool(cpus) as pool:
        return pool.map(f, data)


def scrape_html_paragraphs(uri):
    """
    util - we dont care about errors - this is a try or ignore for test data
    """
    try:
        response = requests.get(uri)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # title = soup.title.string
            paragraphs = soup.find_all("p")
            text_paragraphs = [p.get_text() for p in paragraphs]
            cleaned_text = "\n".join(text_paragraphs)
            return cleaned_text
        else:
            return None
    except Exception as e:
        return None


def parse_fenced_code_blocks(input_string, try_parse=True, select_type="json"):
    """
    extract code from fenced blocks - will try to parse into python dicts if option set
    """
    pattern = r"```(.*?)```|~~~(.*?)~~~"
    matches = re.finditer(pattern, input_string, re.DOTALL)
    code_blocks = []
    for match in matches:
        code_block = match.group(1) if match.group(1) else match.group(2)
        if code_block[:4] == select_type:
            code_block = code_block[4:]
        code_block.strip()
        if try_parse and select_type == "json":
            code_block = json.loads(code_block)
        code_blocks.append(code_block)
    return code_blocks


def pydantic_type_generator(obj, name=None, use_sample_row_count=None):
    extra_hint = " Try to infer the primary key attribute and add a Field with is_key=True for the primary key field. For all other fields omit the pydantic Field value"
    name = "MyModel" if name == None else name
    if isinstance(obj, list):
        q = f"Generate a Pydantic object called {name} from the fields {obj} using snake casing field names and infer the types. {extra_hint} "
        return generator(q)
    if isinstance(obj, dict):
        q = f"Generate a Pydantic object called {name} from the fields {obj} using snake casing for field names. {extra_hint}"
        return generator(q)
    if isinstance(obj, pd.DataFrame):
        if use_sample_row_count:
            q = f"Generate a Pydantic object called {name} from the sample data {obj.head(use_sample_row_count).to_dict('records')} using snake casing for field names. {extra_hint}"
        else:
            q = f"Generate a Pydantic object called {name} from the pandas fields and data types {obj.dtypes} using snake casing for field names. {extra_hint}"
        return generator(q)

    if isinstance(obj, str):
        return generator(obj)
    # why not....
    return generator(str(obj))


def generator(question, llm_model="gpt-4"):
    """
    handy and sometimes clever generator of code to save time
    open ai key expected in env
    """
    llm = ChatOpenAI(model_name=llm_model, temperature=0.0)
    prompt = f"""You are a code generating agent. Generate python code as asked. Return only the python code without explanation.
                Question: {question} """
    return llm.predict(prompt)


def str_hash(s=None, m=5, prefix="mon"):
    s = (s or str(uuid.uuid1())).encode()
    h = hashlib.shake_256(s).hexdigest(m).upper()
    return f"{prefix}{h}"
