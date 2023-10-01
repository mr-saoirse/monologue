from monologue.core.utils.ops import parse_fenced_code_blocks

def test_parse_fenced_code_blocks():
    
    S = """
    abs test
    ```json
    {"a": "b"}
    ```

    and json```{"c":"d"}```

    great
    adfasdf

    asfadsf 
    {"e"" : "f"}
    """


    result = parse_fenced_code_blocks(S) 
    #TODO dict hash
    assert len(result) == 2 and result[-1]['c'] == 'd'
    