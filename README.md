# Google Patents web scraper

To install the necessary requirements run:
`pip3 install -r "requirements.txt"`

For me, all packages installed with python's 3.9 interpreter.
(So I replace "python" below with "python3.9")

## scraper.py

This web scraper searches Google Patents and analyzes the results.
It will log patent IDs for the top ten results.
**Terms are separated by commas; each term can have 1 or multiple words.**
If given a *2-term query*, ex. "dslr camera, digital single lens reflex camera",
it will analyze Jaccard and Dice distances for the results of searching by
term 1 ("dslr camera"), term 2 ("digital single lens reflex camera"), and both
terms ("dslr camera, digital single lens reflex camera").
If given a *single-term query*, the scraper will log results for that query, but
the rows corresponding to term 2 and distance analysis will remain blank.

USAGE EXAMPLE 1
`python scraper.py example_terms.txt [output_file.csv]`
The program will log values for each query in a different row.
See example_terms.txt for intended formatting of 2-term queries.
Single-term queries are also acceptable. If no output file
is specified, default output goes to output.csv.

USAGE EXAMPLE 2
`python scraper.py`
The program will prompt user for query input. The user must input
1-2 comma-separated terms. Output will be saved to output.csv.