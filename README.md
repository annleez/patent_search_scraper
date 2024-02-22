# Google Patents web scraper

To install the necessary requirements run:
`pip3 install -r "requirements.txt"`

## scraper.py

This web scraper searches Google Patents and analyzes the results.
It will log total results and patent IDs for the top 20 results.
**Terms are separated by commas; each term can have 1 or multiple words.**

Given a *2-term query*, ex. "dslr, digital single lens reflex", it will
analyze Jaccard and Dice distances for the results of searching by term 1
("dslr"), term 2 ("digital single lens reflex"), and a Boolean combination
of terms ("dslr OR digital single lens reflex").

Given a *2-term query and acronym*, ex. "dslr camera, digital single lens reflex,
dslr", it will do all of the above to evaluate your terms as (acronym form,
expanded form), *using the given acronym to determine the Boolean query*.
Ex. term 1 ("dslr camera"), term 2 ("digital single lens reflex camera"), and a
Boolean combination of terms ("(dslr OR digital single lens reflex) AND camera")

Given a *single-term query*, the scraper will log results for that query, but
the rows corresponding to other terms and distance analysis will remain blank.

USAGE EXAMPLE 1
`python3 scraper.py example_terms.txt [output_file.csv]`
The program will log values for each query in a different row.
See example_terms.txt for intended formatting of 2-term queries.
Single-term queries are also acceptable. If no output file
is specified, default output goes to output.csv.

USAGE EXAMPLE 2
`python3 scraper.py`
The program will prompt user for query input. The user must input
1-2 comma-separated terms. Output will be saved to output.csv.
