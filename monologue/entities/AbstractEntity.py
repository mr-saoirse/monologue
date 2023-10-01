from typing import Union, List, Optional
from pydantic import Field, BaseModel
import json
import numpy as np
 

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        dtypes = (np.datetime64, np.complexfloating)
        if isinstance(obj, dtypes):
            return str(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            if any([np.issubdtype(obj.dtype, i) for i in dtypes]):
                return obj.astype(str).tolist()
            return obj.tolist()
        return super(NpEncoder, self).default(obj)
    
class AbstractEntity(BaseModel):
    
    def get_namespace(cls):
        #TODO: simple convention for now - we can introduce other stuff including config
        parts = cls.__module__.split('.')
        return parts[-2] if len(parts) > 2 else None
    
    def get_entity_name(cls):
        #TODO: we will want to fully qualify these names
        s = cls.schema()
        return s['title']
    
    def get_key_field(cls):
        s = cls.schema()
        key_props = [k  for k,v in s['properties'].items() if v.get('is_key')]
        #TODO: assume one key for now
        if len(key_props):
            return   key_props[0] 
        
    def get_fields(cls):
        s = cls.schema()
        key_props = [k  for k,v in s['properties'].items() ]
        return key_props
    
    def get_about_text(cls):
        if hasattr(cls,'config'):
            c = cls.config
            return getattr(c, 'about', '')
            
    def large_text_dict(cls):
        return cls.dict()
        
    def __repr__(cls):
        """
        For the purposes of testing some logging with types
        the idea of using markdown and fenced objects is explored
        """
        
        d = cls.dict()
        d['__type__'] = cls.get_entity_name()
        d['__key__'] = cls.get_key_field()
        d['__namespace__'] = cls.get_namespace()
        d = json.dumps(d,cls=NpEncoder,default=str)       
        return f"""```json{d}```"""

    