# klines-5m

> Reads 5m klines from binance public API.

## Prerequisites

- Visual C++ Build Tools
- `pipenv`

## Build

```
# optionally
pipenv sync

pipenv run python .\src\setup.py build
```

## Usage

To retrieve saved values:

```
klines-5m SYMBOL TIME
```

For example:

```
klines-5m BUSD '2020-01-01 10:25'
```

To update price information:

```
klines-5m SYMBOL update
```
