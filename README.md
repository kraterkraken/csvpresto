# csvpresto

Program to read in a CSV file and perform statistical operations on various columns.


### Usage:

`csvpresto -f filename [-a] [-g <collist> -s <collist> -o <SUM|COUNT|AVG>]`

where

    -g specifies the list of columns to group by.  Ex: -g 1 2 3 4
    -s specifies the columns to gather stats on.  Ex: -s 5 6 7
    -o specifies the statistical operation to perform (SUM | COUNT | AVG)
    -f specifies the CSV file to use as input
    -a indicates that the program should spit out an analysis of the
       headers to help the user choose columns for grouping and stat
       operations.  Note that this option overrides all the others.
