# FinBox BankConnect Python Library

[![Build Status](https://travis-ci.org/finbox-in/bank-connect-python.svg?branch=master)](https://travis-ci.org/finbox-in/bank-connect-python)
[![Coverage Status](https://coveralls.io/repos/github/finbox-in/bank-connect-python/badge.svg?branch=master)](https://coveralls.io/github/finbox-in/bank-connect-python?branch=master)
[![PyPI](https://img.shields.io/pypi/v/finbox-bankconnect)](https://pypi.org/project/finbox-bankconnect/)


Python library to use [Finbox Bank Connect](https://finbox.in/products/bank-connect/)

## Installation
To use the package install using pip / pip3:

```sh
pip3 install finbox_bankconnect
```

## Quick Start
Sample code to upload a statement pdf and extract transactions from it

```python
import finbox_bankconnect as fbc

# set API Key
fbc.api_key = "YOUR_API_KEY"

# create an entity object
entity = fbc.Entity.create()

# upload a statement pdf
entity.upload_statement('path_to_file.pdf')

# fetch transactions for the entity
transactions = entity.get_transactions()

# printing the transaction objects by iterating using the transaction iterator
for transaction in transactions:
  print(transaction)
```

## Requirements
Python 3.4+

## License
Licensed under the MIT license, see LICENSE
