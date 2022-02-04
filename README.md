# flake8-pydantic-skip
flake8 plugin which checks for misuse of `Skip` in [Optional Key Pydantic Model](https://github.com/oyfml/test_modified_pydantic_model)

## Installation
`pip install flake8-pydantic-skip`

## flake8 codes

| Code   | Description                                            |
|--------|--------------------------------------------------------|
| TCS100 | Skip must not type wrapped                             |
| TCS101 | Invalid type argument in Skip definition               |
| TCS102 | Skip expects Optional type as argument                 |
