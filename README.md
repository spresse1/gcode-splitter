gcode-splitter
==============

A small utility for splitting gcode files into multiple parts.  This has several advantages:
- Mid-print material changes: By splitting a print in the right location, a print can be stopped, have material changed, and then restarted.
- Failed print resumption: If a print fails 'cleanly', repairs to the printer can be made or a new spool of plastic inserted or whatever must be done to get the printer able to print again, then this can be used to resume a print at the correct height.  See HOWTO below for details.

Input file restrictions
==============

The input file can be of two formats.  First, with annotations to assist the script.  The annotations simply mark the beginning and end of any prefix (setup) and postfix (cooldown, end) gcode.  Each annotation is a gcode comment, and begins with a semicolon.  Each must appear on its own line.  The annotations are as follows:
- ; START_PREFIX - Marks the beginning of the prefix.
- ; END_PREFIX - Marks the end of the prefix
- ; START_POSTFIX - Marks the end of the postfix
- ; END_POSTFIX - Marks the end of the postfix.

The second option is to remove the prefix and postfix from the original gcode file (as output by your slicer). If you do so, you'll need to specify the prefix and postfix on the command line (using the --prefix and --postfix options).

Passing an un-annotated and un-modified gcode file will probably result in incorrect results, as many prefixes include Z-axis movements, which the tool will pick up and treat as a normal layer transition.

HOWTO
=====

Resume a Failed Print
---------------------

This procedure only works if a print has failed cleanly.  This means a sudden failure, such as a loss of power, running out of material, sudden clog or any situation that results in a print failure with no more than one layer's difference in height across the object.
This procedure likely will leave a seam or slight gap in the print.

- First, repair whatever issue caused the print to fail in the first place.
- Second, using your printer's manual interface, figure out the height that the print failed at.
- Run this tool, inputting that height as the location to split
- Ignore the part0 file and print the part1

Note that many printers have calibration in their initial setup and assume the platform is clear.  You may wish to write a different prefix which does not make this assumption.  A more simple option, if your printer has a removable platform, is to remove the platform with the print on it, let the printer calibrate, pause, insert the platform and resume.  You will have to figure out how to cause your printer to pause in gcode, immediately after finishing the calibration procedures.  This is commonly an M0, M1 or M25, M226, or ;PAUSE in the gcode.  Please refer to your printer's documentation.

Tips and Tricks
===============

Resuming Prints
---------------
If you're working with thermoplastics, resuming a print is much like starting a new one - it will take extra effort to get the extruded plastic to stick.  I found that warming the plastic using a hair dryer was sufficient to simulate the print having not failed and get good results in terms of layer adhesion.

Dealing with Curling
--------------------
Thermoplastics also have a tendency to curl when they cool.  This makes it impossible to resume prints without special care.  Again, the hairdryer is the solution.  Place your print upside down on top of a flat surface.  On top of the platform, place heavy objects - I found about 5-10Kg of weight ideal.  Now, heat the object you're printing, giving special focus to the ares that are touching the flat surface (which indicates those areas have curled).  The weight on top should push the now-malleable plastic into the correct shape.  Leave the print under the weight until cool.

If your printer's platform is not removable, the same process works.  However, the flat surface and any objects must be placed on top of the object while still in the printer.  Be sure not to put in enough weight to damage your printer.
