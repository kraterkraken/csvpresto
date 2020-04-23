# csvpresto

Program to read in a CSV file and perform statistical operations on various columns.


### Usage:

```
csvpresto.py operation [filename] [options]

Program to read in a CSV file and perform statistical operations on various
columns.

Arguments:
  operation         The operation to perform. Valid choices are: SUM, AVG,
                    MIN, MAX, COUNT, and HEADERS. SUM, AVG, MIN, and MAX
                    calculate the relevant stat in the columns specified by
                    -s, grouping by the columns specified by -g. COUNT counts
                    the number of records for each distinct group specified by
                    -g. HEADERS displays all of the headers and their column
                    numbers as an aid in determining what values to use for
                    the -g and -s arguments.
  filename          The CSV (comma-separated-value) file to use as input. If
                    omitted or '-', will read from standard input.

Options:
  -h                Show this help message and exit.
  -g col [col ...]  The list of columns to group by. If omitted, will display
                    one set of stats for the entire file. Output is sorted by
                    these columns by default. Ex: -g 1 2 3 4
  -s col [col ...]  The list of columns to perform stats on. Required for SUM
                    and AVG. Ex: -s 5 6 7
  -c                Causes the output to be in CSV format. Useful for piping
                    to other commands or redirecting to a file.
  -a col [col ...]  The list of columns to sort by (ascending).
  -d col [col ...]  The list of columns to sort by (descending).
  -r N              Display at most N rows of results. Can be used in
                    conjunction with the -d/-a sorting options to show the
                    top/bottom N rows.
  ```
