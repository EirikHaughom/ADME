# API Specification Fetcher

This utility downloads the ADME API specifications listed in `fetchSpecs.py`,
normalises them to JSON, and stores the resulting files on disk.

## Prerequisites

Install the dependencies into your Python environment:

```pwsh
python -m pip install -r requirements.txt
```

## Usage

Fetch every specification into the default `downloads` folder:

```pwsh
python fetchSpecs.py
```

Fetch a subset of specifications or choose a different output directory:

```pwsh
python fetchSpecs.py --only dataset_v1 search_v2 --output-dir .\my-specs
```

List the available specification keys without downloading them:

```pwsh
python fetchSpecs.py --list
```

Use `--overwrite` to replace existing files and `--verbose` for detailed logs.
