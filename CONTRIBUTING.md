# How to contribute to rich-traceroute

Hello, and thanks for taking time to contribute to this project!

Please feel free to open a PR on GitHub and propose your idea.

A good way to contribute to this tool is to improve traceroute parsers, or to add a new one. I'll provide some hints on how to do it below.

## Traceroute parsers

Parsers take care of converting the input texts that the users paste into the tool into an abstract representation of traceroutes.

They are used to understand which hops and which hosts show up in the text, and to convert them into *numbers* (IP addresses, packet loss levels, latencies).

The tool parses the input text using all the parsers that are available, and eventually it selects the output of the parser that produced the more hops and hosts as the candidate one to be used to process a traceroute.

Their implementation is done inside *rich_traceroute/parsers*: generically speaking, one file for each format is used. The modules must contain one or more classes that inherit from `BaseParser` (*base.py* - [see it on GitHub](https://github.com/pierky/rich-traceroute/blob/master/rich_traceroute/traceroute/parsers/base.py)). They must have the `DESCRIPTION` and the `EXAMPLES` attributes: the former must contain a short description of the format parsed by the class (example: "MTR JSON"), the latter must be a list of paths to one or more files that contain an example of the text that the parser is able to process.

The main method that must be implemented on each parser class is `_parse`, that is where all the magic must happen. `self.raw_data` contains the text that the user provided as the input; `self.hops` is what the parser must set before returning, assuming that it was able to understand the input text. The expected output is this:

```python
class HopHost(NamedTuple):

    host: str
    loss: Optional[float]
    avg_rtt: Optional[float]
    min_rtt: Optional[float]
    max_rtt: Optional[float]

self.hops: Dict[int, List[HopHost]] = {}
```

So, `self.hops` must be set with a dictionary: the number of each hop must be the key, and the value must be a list of hosts for which replies were received for that hop. If no replies were found for a specific hop, the list must be empty.

In case a parser is not able to understand a specific input format, it must raise a `ParserError` exception.

A helper class that makes the processing of certain formats easier can be found in *line_by_line.py* ([see it on GitHub](https://github.com/pierky/rich-traceroute/blob/master/rich_traceroute/traceroute/parsers/line_by_line.py)): `LineByLineParser`. This class can be used to parse traceroutes whoes output format includes only hosts and latencies, one (or more) on each line. More comments can be found inside the files itself.

Once a new parser class is created, it must be added to the `parsers` list in *__init__.py* of *rich_traceroute/parsers*.

### Tests

For each parser, proper tests must be included. It's just a matter of adding a file containing the input text in *tests/data/traceroute/* and writing a test like one of those already present in *tests/parsers*.
