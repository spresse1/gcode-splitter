gcode-splitter
==============

A small utility for splitting gcode files into multiple parts.  In theory, this should allow layer to layer material changes by splitting the print job into multiple parts.

Input file restrictions
==============

The input file can be of two formats.  First, with annotations to assist the script.  The annotations simply mark the beginning and end of any prefix (setup) and postfix (cooldown, end) gcode.  Each annotation is a gcode comment, and begins with a semicolon.  Each must appear on its own line.  The annotations are as follows:
; START_PREFIX - Marks the beginning of the prefix.
; END_PREFIX - Marks the end of the prefix
; START_POSTFIX - Marks the end of the postfix
; END_POSTFIX - Marks the end of the postfix.

The second option is to remove the prefix and postfix from the original gcode file (as output by your slicer). If you do so, you'll need to specify the prefix and postfix on the command line (using the --prefix and --postfix options).

Passing an un-annotated and un-modified gcode file will probably result in incorrect results, as many prefixes include Z-axis movements, which the tool will pick up and treat as a normal layer transition.
