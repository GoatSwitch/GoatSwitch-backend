# Installation
    
```bash
cd tools/gs_common
pip install .
```

# fnTimer
A tool to time functions in python.

Add a decorator to any function you want to time and thats it.

## Usage
Base usage is simple. Just add the decorator to any function you want to time.

```python
from gs_common.time_decorator import timed

@timed(decimal_places=3, log_level="info")
def my_function():
    print("Hello World")
```
