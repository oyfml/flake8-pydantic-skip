# flake8-pydantic-skip
flake8 plugin which checks for misuse of `Skip` in [Optional Key Pydantic Model](https://github.com/oyfml/test_modified_pydantic_model)

## Installation
`pip install flake8-pydantic-skip`

## flake8 codes

| Code   | Description                                            |
|--------|--------------------------------------------------------|
| SKP100 | Skip must not type wrapped                             |
| SKP101 | Invalid type argument in Skip definition               |
| SKP102 | Skip expects Optional type as argument                 |

## Run test
```
cd /path_to_repo/flake8_pydantic_skip
pip install -e .
cd tests
pytest flake8_pydantic_skip_test.py
```

## Build
```
python setup.py sdist
twine upload dist/*
```
