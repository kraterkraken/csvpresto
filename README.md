# csvpresto

Program to read in a CSV file and perform statistical operations on various columns.


### Usage:

`csvpresto.py operation filename
              [-h]
              [-g col [col ...]] [-s col [col ...]]


positional arguments:
  operation         The operation to perform. Valid choices are: SUM, AVG,
                    COUNT, and HEADERS. SUM and AVG calculate the sum and
                    average of the data in the columns specified by -s,
                    grouping by the columns specified by -g. COUNT counts the
                    number of records for each distinct group specified by -g.
                    HEADERS displays all of the headers and their column
                    numbers as an aid in determining what values to use for
                    the -g and -s arguments.
  filename          The CSV (comma-separated-value) file to use as input

optional arguments:
  -h, --help        show this help message and exit
  -g col [col ...]  The list of columns to group by. Ex: -g 1 2 3 4
  -s col [col ...]  The list of columns to perform stats on. Ex: -s 5 6 7`
