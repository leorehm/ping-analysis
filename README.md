## Ping Analyzer
A simple script to analyze and display ping statistics from one or more ping transcripts. Examplary PowerShell ping transcripts included. Linux currently not supported. 

# Usage
    $ python .\ping-analysis.py -h
    usage: ping-analysis.py [-h] [-p {single,mult,both}] [-o OUT [OUT ...]] [--ma-window MA_WINDOW]
                            file [file ...]

    positional arguments:
    file                  one or more files to be read

    options:
    -h, --help            show this help message and exit
    -p {single,mult,both}, --plot {single,mult,both}
                            plot type: (single|mult|both); default = single
    -o OUT [OUT ...], --out OUT [OUT ...]
                            save plot to file; enter two paths when using "-p both"
    --ma-window MA_WINDOW
                            moving-average window in seconds; default = 20


# Ping Transcipt in PowerShell
    Start-Transcript -path .\ping-log.txt -Append; ping -t <host> | % {"{0} - {1}" -f (Get-Date),$_}

- add `-S <ip>` to use via a specific interface in windows
- Exit the ping with `<Ctrl-C>`#
- Stop the transcript with `Stop-Transcript` or close the powershell window
