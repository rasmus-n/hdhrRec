# hdhrRec

Automatic recodring scheduler for HDHomeRun devices.

## Purpose

This is primarely a personal project to satisfy my own TV recording needs.

My recording hardware consist of an [alix3d2](http://www.pcengines.ch/alix3d2.htm) from PC Engines, a [HDHomeRun Dual](http://www.silicondust.com/products/models/hdhr3-eu/) from SiliconDust and a USB harddrive.

The alix3d2 is a single board computer with a 500MHz CPU and 256MB of RAM, it has no video output. It should be possible to make hdhrRec run on most devices that can run python: In my setup, recording a TV program only puts about 6% load on the CPU.

The purpose of this project is to provide a relatively simple, lightweight, automatic recording scheduler for HDHomeRun devices, suitable for running headless on low power hardware.

The primary interfaces are:
* A web interface for status and management of recording rules and recording profiles.
* The file system, so recordings can be shared / managed etc. by general purpose tools.

## Motivation
In the past I have used MythTV with MythWeb and later TVHeadend.

I stopped using MythTV because:
* Not well suited for headless operation.
* Not "friendly" to general purpose tools.

Compared to MythTV, I really like TVHeadend, but stopped using it because:
* No native support for HDHomeRun devices (it did work with [dvbhdhomerun](http://sourceforge.net/apps/trac/dvbhdhomerun/)).
* Would rewrap the streams in MKV.
* Would fail to identify the audio on some TV channels, and thus not put the audio stream in the MKV.

## Features

* Calls an external script to update the program table (a script for dr.dk, danish national tv, is provided).
* Decides what to record based on rules that may add "weight" to the programs in the program table.
* Can record multiple programs simultaneously on the same MUX (MultiRec).
* Should handle multiple HDHomeRun devices (not tested).
* Web interface shows what will be recorded and allows modification of rules and profiles.

## Operational concept

* The rule table can at any time be modified via the web interface.
* On a regular basis (currently every 12h) a script is called to collect TV program data from an external source and insert it into the program table.
* If either the program or the rule table has been updated, every program is evaluated against every rule.
  * Whenever there is a match, the "weight" of the rule is added to the program (negative weights are allowed)
  * For each program, the single matching rule with the heighest weight will decide which recording profile to use.
  * Programs with an accumulated "weight" above the threshold (currently 0) are added to the recording table. The recording profile may specify an amount of pre and post record time.
* The recording table is evaluated every 10s and when a recording is started, the file name is generated from a pattern specified by the recording profile.

## Technology
Dynamic data (program data, rules etc.) is stored in a SQLite database.

The scheduler and the web interface are two independent applications who "communicate" through the database.

The scheduler is written in python and only depends on one module not part of the python standard modules; to get satisfactory performance the actual "recording", i.e. filtering of streams and writing to file, is done in a python module written i C.

Building the python module requires development files for python and libhdhomerun. Due to some problems with dropped UDP packages, the recorder module will try to increase the RX buffer size, so it may be necessary . 

The web interface is also written in python, using the [web.py](http://webpy.org/) framework.

## Status / disclaimer

As stated above, this project was started because I was not satisfied with the other projects I tried. Now I have something that works for me, but I will not promise that it works for you.

### Missing
* Installation guide / script to create the initial database and configuration file
* The web interface is only half finished (it is functional, but it can't be used for any of the one-time configuration).
* Robustness against bad input from web interface.
* No prioritising in case the number of required tuners exceeds the number of available tuner (not tested, it might even cause the application to crash).
* Script to insert tv program data from a XMLTV-file.
* Mobile phone friendly web interface
* ...
