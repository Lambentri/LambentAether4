from functools import wraps

def docupub(topics: [], shapes: {}):
    def _docpub(f):
         @wraps(f)
         def wrapper(*args, **kwds):
             return f(*args, **kwds)
         wrapper._publisher = True
         wrapper._doc =f.__doc__
         wrapper._topics = topics
         wrapper._shapes = shapes
         return wrapper
    return _docpub