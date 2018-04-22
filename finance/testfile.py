def logged(func):
    def with_logging(*args, **kwargs):
        print (func.__name__ + " was called")
        return func(*args, **kwargs)
    return with_logging

@logged
def f(x):
   """does some math"""
   return x + x * x



print(f(2))