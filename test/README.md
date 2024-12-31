# How to test goat_service

```
# install py dependencies
pip install -r requirements.txt

# set PYTHONPATH
export PYTHONPATH="."

# run tests
pytest test/goat_service/
```

# How to test code_executor

```
# same installs as goat_service
# install all dependencies in src/code_executor/README.md
# run tests
pytest test/code_executor/
```

# How to test integration tests

```
# same installs as goat_service
# same installs as code_executor
# install all dependencies in README.md (dapr, etc.)
# install this:
pip install pytest-parallel py signalrcore

# set GS_API_KEY as env var
export GS_API_KEY="your_api_key"

# run tests
python test/test_workflow_convert.py
```

# How to test with docker

```
# build linux images
bash build_linux_dockers.sh
# run tests
bash test/test_docker_linux.sh

# build windows images
.\build_windows_dockers.ps1
# run tests
.\test\test_docker_windows.ps1
```

# Error: OSError: [WinError 1314] A required privilege is not held by the client

- Enable the creation of symbolic links for your user. To do this, you need to adjust the local security policy. Here's how to do it:
- Open the Local Security Policy editor (secpol.msc).
- Navigate to Local Policies -> User Rights Assignment.
- Find the policy named "Create symbolic links".
- Add your user to the policy.
