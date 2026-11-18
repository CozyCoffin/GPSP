==============================================================================
  GPSP  -  an offline map and GPS navigator for the Sony PSP
==============================================================================

GPSP is an offline road map for the Sony PSP. With the official PSP-290 GPS
receiver plugged in, it becomes a car navigation unit: it shows a moving
road map with your position on it, lets you search for nearby gas stations,
food, hospitals and more, saves your own places, and gives beeps and
on-screen turn-by-turn directions to wherever you want to go.

NO GPS RECEIVER? NO PROBLEM. Without a PSP-290, GPSP still works fully as an
offline map of your area. You can scroll and zoom around the map, search for
places by category, save places, and preview how long a drive would take
between two places. You just will not see your own position or get live
directions. And since you make the maps yourself, you can update them
whenever you like. See section 6 for the details.

No internet is needed on the PSP. The maps are made once on a computer and
copied to the PSP's memory stick.

ABOUT HOW THIS WAS MADE (PLEASE READ)

  GPSP is 100% AI-coded. Every line of the program, the map maker
  (make_map.py) and this guide was written by an AI assistant (Claude, made
  by Anthropic). The person who put the project together did not write any of
  the code. All they did was prompt the AI with what they wanted, then try
  the results on a real PSP and report back what worked and what did not.

  This matters to you for a few reasons:

    * It is a hobby project, shared as-is with no warranty. It may have bugs
      that nobody has found yet.
    * Support is limited. Since the creator only prompted the AI and did not
      write the code, they may not be able to fix problems by hand. If
      something goes wrong, start with section 13. Giving the source code
      and this guide to an AI assistant and describing the problem is also
      a reasonable way to get help.
    * Please do not rely on it as your only way of finding your way anywhere
      important.

This guide is written for people who are not very technical. Take it one
step at a time and you will be fine. If a word is unfamiliar, there is a
small glossary at the very end.


------------------------------------------------------------------------------
  CONTENTS
------------------------------------------------------------------------------

   1. What you need
   2. What is in this package
   3. Step 1 - Install Python on your computer (needed for making maps)
   4. Step 2 - Make a map of your area
   5. Step 3 - Put GPSP and your map on the PSP
   6. Step 4 - Start GPSP and get a GPS signal (or use it without one)
   7. Using GPSP - the controls
   8. Finding a place and getting directions
   9. Saved places
  10. Using more than one map
  11. Changing the colors (colors.txt)
  12. Editing saved places on a computer (places.txt)
  13. Troubleshooting
  14. Good to know
  15. Credits
  16. Glossary


------------------------------------------------------------------------------
  1. WHAT YOU NEED
------------------------------------------------------------------------------

For the PSP:

  * A Sony PSP that can run homebrew (your own programs). This means it must
    be running "custom firmware" (often shortened to CFW). If you can already
    run homebrew games or apps from the PSP's Game > Memory Stick menu, you
    are all set. If you have never done this, search online for a guide for
    your PSP model first; that part is outside this package.
  * OPTIONAL: the official Sony PSP-290 GPS receiver. It plugs into the small
    USB port on the top edge of the PSP and lets GPSP show where you are and
    give turn-by-turn directions. (GPSP was built for this receiver. Other
    GPS devices will not work.) If you do not have one, GPSP still works as
    an offline map. See the "Using GPSP without a receiver" part of
    section 6.
  * A memory stick with a few free megabytes.

For your computer (only needed to make maps):

  * A Windows, Mac or Linux computer with an internet connection.
  * Python 3 (a free program). Python IS REQUIRED to make maps. Step 1 below
    explains how to install it. You do not need to know how to program.
  * A way to copy files to the PSP's memory stick: connect the PSP to the
    computer with a USB cable and use the PSP's "USB Connection" option in
    the Settings menu, or plug the memory stick into a card reader.

Note: GPSP has been tested with a PSP and a PSP-290 receiver. It has not
been tested on a PSP Go (which has a different connector).


------------------------------------------------------------------------------
  2. WHAT IS IN THIS PACKAGE
------------------------------------------------------------------------------

  GPSP folder      The program itself. Inside it is a file named
                     EBOOT.PBP. This is what you copy to the PSP.

  make_map.py        The "map maker". This is a Python script that runs on
                     your computer, downloads road data for the area you
                     choose, and creates a map file for the PSP.

  README.txt         This guide.

  LICENSE.txt        The MIT License: what you are allowed to do with GPSP.

  source folder      (Optional) The program's source code and build files,
                     for people who want to look at or change how it works.
                     You can ignore this folder if you only want to use it.


------------------------------------------------------------------------------
  3. STEP 1 - INSTALL PYTHON ON YOUR COMPUTER
------------------------------------------------------------------------------

Python is the free program that runs the map maker. You only have to install
it once. You do NOT need to install anything else: the map maker uses only
what comes with Python.

WINDOWS

  1. Open a web browser and go to:   https://www.python.org/downloads/
  2. Click the big yellow "Download Python" button and open the file it
     downloads.
  3. IMPORTANT: on the very first screen of the installer, tick the box at the
     bottom that says "Add python.exe to PATH" (it may say "Add Python to
     PATH"). If you forget this, the map maker will not start.
  4. Click "Install Now" and wait for it to finish, then click Close.

  To check that it worked: press the Windows key, type  cmd  and press Enter
  to open a black window (the Command Prompt). Type:

        python --version

  and press Enter. You should see something like "Python 3.12.4". Any
  version starting with 3 is fine. If Windows says Python was not found or
  opens the Microsoft Store, run the installer again and make sure the PATH
  box is ticked.

MAC

  1. Go to  https://www.python.org/downloads/  and download the macOS
     installer. Open it and follow the steps.
  2. To check: open the "Terminal" app and type  python3 --version
     On a Mac, always type  python3  instead of  python  in the commands
     below.

LINUX

  Python 3 is usually already installed. Open a terminal and type
  python3 --version  to check. If it is missing, install it with your
  distribution's package manager (for example:  sudo apt install python3 ).
  On Linux, type  python3  instead of  python  in the commands below.


------------------------------------------------------------------------------
  4. STEP 2 - MAKE A MAP OF YOUR AREA
------------------------------------------------------------------------------

The map maker downloads free road, town and business data from OpenStreetMap
and packs it into a single map file ending in ".pmap".

You need an internet connection for this step. Making a map can take a few
minutes, longer for bigger areas.

THE EASY WAY (Windows)

  1. Put make_map.py in a folder you can find easily, for example a new
     folder on your Desktop called "maps".
  2. Double-click make_map.py. A black window opens and asks which place you
     want. Type something like:

        Madison County, Alabama

     and press Enter. (Use the form "place, state" or "place, country". A
     county, a city or a region all work.)
  3. It looks the place up and shows you what it found. If several places
     match, it lets you pick the right one by number. Answer any yes/no
     questions it asks.
  4. Wait while it downloads and builds the map. When it says "Done!", press
     Enter to close the window.
  5. A new file ending in .pmap now sits in the same folder as make_map.py.
     That is your map.

THE COMMAND WAY (Windows, Mac or Linux)

  1. Open the Command Prompt (Windows) or Terminal (Mac/Linux) in the folder
     that contains make_map.py. On Windows you can do this by opening the
     folder in File Explorer, clicking the address bar at the top, typing
     cmd and pressing Enter.
  2. Type this and press Enter (remember: use python3 on Mac and Linux):

        python make_map.py "Madison County, Alabama"

     Keep the quotation marks around the place name.

Handy options you can add to the end of the command:

  --name "Huntsville"      The name shown in the PSP's map list.
  --margin 5               Extra kilometers of map around the place
                           (default is 2). Useful so the edge of town is not
                           the edge of your map.
  --pick 1                 If several places match your search, automatically
                           use the first (best) match.
  --yes                    Do not ask for confirmation.
  --no-routing             Leave out the driving-directions data. This makes
                           the file smaller, but you will not be able to get
                           turn-by-turn directions on that map.
  --force                  Allow a very large area. By default the map maker
                           warns you and asks before building something huge.
  --out myfile.pmap        Choose the name of the output file.
  --bbox S W N E           Give the area yourself as four coordinates (south,
                           west, north, east latitude/longitude), instead of
                           typing a place name.

Example with options:

        python make_map.py "Walker County, Alabama" --margin 4 --name "Walker"

TIPS FOR CHOOSING AN AREA

  * Think about where you actually drive. A county or two around home is a
    good start. Bigger maps use more of the PSP's memory and take longer to
    build.
  * You can build as many maps as you like and keep several on the memory
    stick. Neighboring maps can overlap a little; that is fine.
  * Street names and business names are shown in plain English letters
    only (the PSP's font has no accents or special symbols, so the map maker
    removes them).


------------------------------------------------------------------------------
  5. STEP 3 - PUT GPSP AND YOUR MAP ON THE PSP
------------------------------------------------------------------------------

  1. Connect your PSP to the computer with a USB cable and, on the PSP, go to
     Settings > USB Connection and press X. (Or put the memory stick in a
     card reader.) The PSP's memory stick now appears on your computer as a
     drive.
  2. On the memory stick, open the folder named PSP, then the folder named
     GAME.
  3. Create a new folder inside GAME named exactly:

        GPSP

  4. Copy the file EBOOT.PBP into that GPSP folder.
  5. Copy your map file (the one ending in .pmap) into the SAME GPSP folder.

     When you are done, the folder should look like this:

        PSP/GAME/GPSP/EBOOT.PBP
        PSP/GAME/GPSP/madison_county_alabama.pmap     (your map's name)

  6. Safely disconnect the PSP (press Circle on the PSP to leave USB mode, or
     eject the memory stick properly from your computer).

On the PSP, GPSP now appears under Game > Memory Stick with its own icon,
named "GPSP".

Other files that GPSP creates for itself in that folder, which you do not
need to copy:

  colors.txt       The color settings (see section 11).
  places.txt       Your saved places (see section 12).
  settings.txt     Remembers whether automatic map switching is on or off.
  last_map.txt     Remembers which map you used last.


------------------------------------------------------------------------------
  6. STEP 4 - START GPSP AND GET A GPS SIGNAL (OR USE IT WITHOUT ONE)
------------------------------------------------------------------------------

  1. Plug the PSP-290 GPS receiver into the USB port on the top of the PSP.
  2. Take the PSP and receiver outside or put it where the receiver has a
     clear view of the sky, for example on the dashboard or against the
     windshield of a car. GPS signals do not pass well through roofs, thick
     walls or the inside of a building.
  3. On the PSP, open Game > Memory Stick and start "GPSP".
  4. The first time you start it, GPSP creates colors.txt in its folder.
  5. At first the top line of the screen says "Searching for GPS...". This is
     normal. After the receiver finds enough satellites, the top line changes
     to show your speed (in km/h) and how many satellites it is using, and
     your position appears on the map.

The first signal of the day can take a few minutes, especially after the
receiver has been off for a long time or moved far from where it was last
used. Be patient and keep it in the open.

Until the signal arrives, you can still look around the map, search for
places and plan routes. Only turn-by-turn navigation and saving your current
location need the GPS signal.

USING GPSP WITHOUT A RECEIVER

  You do not need a PSP-290 to get value from GPSP. Without one it is a
  detailed offline map of your area that you can keep up to date yourself.

  Just start GPSP normally with no receiver plugged in. The top line of the
  screen will say "GPS start failed". With no receiver, that is expected and
  nothing is wrong. Everything below works as normal:

    * Scroll around the map with the analog stick or D-pad, and zoom with L
      and R.
    * Find nearby places (gas, food, hospitals and so on). With no GPS,
      distances are measured from the middle of the screen, so scroll the map
      to where you want to search from first.
    * Pick a spot on the map with the crosshair, and save it as a named place.
    * Keep a list of saved places, and add more by editing places.txt on a
      computer (section 12).
    * Preview a trip between two places: Triangle > Saved places, highlight
      the starting place and press Triangle, then choose where to go. The map
      shows the route with its distance and travel time.
    * Switch between maps, and change the colors.

  What needs the receiver: your position marker and speed, "Save my current
  location", turn-by-turn directions, rerouting, and automatic map switching.

  To update your offline map, run make_map.py again (section 4) and copy the
  new .pmap file over the old one on the memory stick. Maps are a snapshot, so
  new roads and businesses show up when you rebuild.


------------------------------------------------------------------------------
  7. USING GPSP - THE CONTROLS
------------------------------------------------------------------------------

On the MAP screen:

  Analog stick ......... Move around the map. The farther you push, the
                         faster the map moves.
  D-pad ................ Move around the map at a slow, steady speed.
  L button ............. Zoom out (see more area).
  R button ............. Zoom in (see more detail).
  X (Cross) ............ "Follow me": jump back to your position and keep the
                         map centered on you. (If you are looking at a route
                         preview, X starts the trip instead; see section 8.)
  SELECT ............... Switch between "north-up" (north is always at the
                         top) and "heading-up" (the map turns so the
                         direction you are driving is at the top).
  Triangle ............. Open the GO TO menu: find a place, pick a saved
                         place, or choose a spot on the map.
  Square ............... Clear the current destination or route.
  Circle ............... Turn the beeps on or off. A short message ("Sound on"
                         or "Sound off") appears.
  START ................ Open the main menu (resume, change map, automatic map
                         switching, quit). Press START again to return.

The top two lines of the screen show:

  Line 1: your speed, the number of satellites in use (for example "sats
          6/9"), whether the map is following you or free, whether it is
          north-up or heading-up, and MUTE if sound is off. Before the first
          GPS fix it says "Searching for GPS...".
  Line 2: your destination, how far away it is, and the estimated travel time.
          If you have no destination it says to press Triangle to find a
          place.

In every menu:

  Up / Down ............ Move the highlight.
  X (Cross) ............ Choose the highlighted item.
  Circle ............... Go back one step.
  START ................ Go straight back to the map.

The MAIN MENU (START) contains:

  Resume ............... Go back to the map.
  Change map... ........ Choose another map (see section 10).
  Auto map switching ... ON or OFF. When ON, GPSP automatically changes to
                         another map on the memory stick when you drive out
                         of the one you are using.
  Quit GPSP .......... Close the program and return to the PSP menu.


------------------------------------------------------------------------------
  8. FINDING A PLACE AND GETTING DIRECTIONS
------------------------------------------------------------------------------

Press Triangle on the map to open the GO TO menu. It has three choices.

A. FIND NEARBY PLACES

  Choose a category: gas stations, hospitals, urgent care, pharmacies,
  grocery stores, convenience stores, restaurants, fast food, coffee shops,
  banks, ATMs, post offices, police, fire stations or hotels.

  GPSP lists the closest matches, nearest first. If you do not have a GPS
  fix yet, distances are measured from the middle of the screen's map view
  instead. Highlight one and press X to get directions to it.

B. SAVED PLACES

  Your own list of places such as Home, Work or Grandma's house. See
  section 9.

C. PICK A SPOT ON THE MAP

  A crosshair appears in the middle of the screen. Move the map with the
  analog stick or D-pad (and zoom with L and R) until the crosshair is over
  the spot you want. The second line at the top of the screen shows the
  coordinates and how far away the spot is from you. Then:

     X ........ Get directions to that spot.
     Square ... Save that spot to your saved places (you will be asked to
                name it).
     Circle ... Cancel and go back to the map.

WHEN YOU CHOOSE A DESTINATION

  GPSP works out a driving route, draws it on the map and shows the total
  distance and travel time. Once you are underway you will see:

  * The route drawn on the map.
  * A banner at the screen showing the next turn, the distance to it and the
    street name (for example "Turn left onto Main Street").
  * Beeps as you approach turns (unless the sound is off).
  * Remaining distance and time on the second status line.
  * "Rerouting": if you miss a turn or leave the route, GPSP notices after
    a few seconds and automatically works out a new route from where you are
    now. A message says "Rerouted" and you hear a beep.
  * When you are within a few dozen meters of your destination you hear a
    series of beeps and a message says "Arrived at ...", and the route is
    cleared.

  Press Square at any time to cancel the trip.

  If there is no GPS signal yet, GPSP shows a straight line to the
  destination and tells you "no GPS fix, straight line only". Once the signal
  arrives you can choose the destination again to get a real route.

  Messages you may see: "no route found, straight line only" means the roads
  in this map do not connect your position to that place (try a bigger
  map). "map has no road network" means the map was built with
  --no-routing. "not enough memory to route" means the trip is too large for
  the PSP to calculate; try a closer destination.

PLANNING A TRIP FROM SOMEWHERE ELSE

  You can also look at a trip that starts somewhere other than where you are
  now, for example to see how long it would take to get from home to work:

  1. Triangle > Saved places.
  2. Highlight the starting place and press Triangle.
  3. Choose the destination (find nearby, saved places, or pick a spot).
  4. The map shows a PREVIEW of that trip with its distance and time.
  5. To really start driving the trip from where you are now, press X on the
     map. To discard it, press Square.


------------------------------------------------------------------------------
  9. SAVED PLACES
------------------------------------------------------------------------------

Open them with Triangle > Saved places. You can store up to 64 places.

The first row of the list is always "Save my current location". It needs a
GPS fix (it saves the spot you are standing at right now).

When a saved place is highlighted:

  X ........ Get directions to it.
  Triangle . Plan a route that STARTS at this place (see section 8).
  Square ... Rename it.
  SELECT ... Delete it. You must press SELECT a second time to confirm, so
             you cannot delete something by accident.
  Circle ... Back.

NAMING A PLACE (the on-screen keyboard)

  A grid of letters appears. Use the D-pad to move around it.

  X ........ Type the highlighted letter.
  Circle ... Delete the last letter.
  Square ... Type a space.
  Triangle . Switch between capital letters and lowercase.
  R ........ Save the name.
  L ........ Cancel.

  Names can be up to 24 characters long.

Saved places are stored on the memory stick in places.txt, so they are still
there next time. They belong to the GPSP folder, not to a particular map,
so a place you saved works with any map that covers it.


------------------------------------------------------------------------------
  10. USING MORE THAN ONE MAP
------------------------------------------------------------------------------

You can keep up to 16 map files in the GPSP folder.

  * To switch manually: START > Change map..., highlight a map and press X.
    The map you are using right now is marked with a star (*).
  * To let GPSP switch for you: START > Auto map switching: ON. When your
    GPS position leaves the current map and lands inside another one on the
    memory stick, GPSP switches to it automatically and shows a short
    message with the map's name.
  * If you ever see "You are outside this map", you have driven out of the
    area you built. Press START > Change map and choose another map, or
    build a new map that covers where you are.

If a map was made with a very old version of the map maker, GPSP shows a
message saying it is from an older version. Just build that map again with
the make_map.py that came in this package.


------------------------------------------------------------------------------
  11. CHANGING THE COLORS (colors.txt)
------------------------------------------------------------------------------

The first time GPSP starts, it writes a file named colors.txt in its
folder. Every color the program uses is listed in it, one per line, each with
a short description of what it colors. The lines look like this:

        some_name = #FFA500   ; what it colors

To change a color:

  1. Turn the PSP off or quit GPSP, then connect the PSP to your computer.
  2. Open colors.txt in Notepad (Windows) or TextEdit (Mac). Plain text
     only.
  3. Change the six-character code after the # to the color you want. These
     are standard web color codes: for example #FF0000 is red, #00FF00 is
     green, #0000FF is blue, #FFA500 is orange, #000000 is black and #FFFFFF
     is white. You can pick colors and see their codes on any "color picker"
     web page. The short form with three characters (like #F00) also works.
  4. Save the file and start GPSP again.

Good to know:

  * Lines that start with a semicolon (;) are notes and are ignored.
  * If you delete or misspell a line, GPSP simply uses its default color
    for that item.
  * If you make a mistake in the file, GPSP shows a short message on
    screen when it starts, telling you which line has the problem. Nothing
    breaks.
  * If you ever want to start over, delete colors.txt. GPSP creates a fresh
    one with all the original colors the next time it starts.


------------------------------------------------------------------------------
  12. EDITING SAVED PLACES ON A COMPUTER (places.txt)
------------------------------------------------------------------------------

You can save places from the PSP, but you can also write them yourself in
places.txt, which is handy if you have a list of addresses with coordinates.

places.txt is created the first time you save, rename or delete a place on the
PSP. If you want to write it by hand before that, just create a plain text
file named places.txt in the GPSP folder.

The format is one place per line: the name, a vertical bar, the latitude, a
vertical bar, the longitude:

        ; GPSP saved places - one per line:  name | latitude | longitude
        Home | 33.512345 | -86.801234
        Work | 33.520100 | -86.812300
        Grandma | 33.480000 | -86.790000

Rules:

  * Lines that start with ; are notes and are ignored.
  * Latitude is the north/south number (positive in the northern hemisphere).
    Longitude is the east/west number (negative in the western hemisphere,
    which includes the whole of the United States). Use decimal numbers like
    the ones above, not degrees/minutes/seconds.
  * You can get coordinates for any spot by right-clicking it in Google
    Maps, or OpenStreetMap on a computer. The coordinates appear at the top
    of the menu or in the info box.
  * Use plain letters and numbers in names. The PSP's font cannot show accents
    or special symbols, and a vertical bar cannot be part of a name.
  * Lines that are not in the right format are skipped.
  * The PSP loads the file when GPSP starts, so edit it while GPSP is not
    running.


------------------------------------------------------------------------------
  13. TROUBLESHOOTING
------------------------------------------------------------------------------

"No map found. Copy a .pmap map file into ms0:/PSP/GAME/GPSP/"
    There is no map in the GPSP folder. Make one (section 4) and copy it
    in (section 5). Make sure it ends in .pmap and sits in the same folder as
    EBOOT.PBP, not in a sub-folder.

"The map files are from an older version of GPSP. Rebuild them..."
    Build the map again with the make_map.py from this package.

"Could not load ... (error ...)"
    The map file may be damaged, for example if the copy was interrupted.
    Copy it to the PSP again or rebuild it.

"GPS start failed"
    The PSP did not detect a GPS receiver. If you do not own a PSP-290, this
    is normal and you can ignore it: GPSP works as an offline map without
    one. If you do have a receiver, check that it is plugged in firmly before
    you start GPSP, then quit and start GPSP again. If you just plugged it
    in, quit and restart GPSP.

"Searching for GPS..." forever
    Take the PSP outdoors or to a window with a clear view of the sky. Wait a
    few minutes. Metal roofs, garages, tunnels, and heavy tree cover block the
    signal.

I am not on the map
    The position marker only appears when you have a GPS fix. If it says
    "You are outside this map", the area you are in was not included when you
    built the map. Build a map that covers it or switch maps (section 10).

Search finds nothing in a category
    Businesses come from OpenStreetMap. In small towns, some businesses may
    simply not be listed there. Another category or a bigger map may help.

The map maker says Python is not recognized / not found (Windows)
    Python is not installed, or the "Add python.exe to PATH" box was not
    ticked. Run the Python installer again, choose Modify or Repair if offered,
    and tick the PATH box. Then close and reopen the black window.

The map maker cannot connect / times out
    The free OpenStreetMap servers are sometimes busy. Wait a few minutes and
    try again. A smaller area, such as one county, is much more likely to
    succeed than a whole state.

The map maker warns that the area is very large
    This is on purpose, to stop you from accidentally downloading far more
    than you need. Choose a smaller area, or add --force if you really want it.

The program will not start on the PSP
    Check that EBOOT.PBP is directly inside PSP/GAME/GPSP on the memory
    stick and that your PSP is running custom firmware.


------------------------------------------------------------------------------
  14. GOOD TO KNOW
------------------------------------------------------------------------------

  * GPSP is a hobby project, not a certified navigation product. Roads
    change, map data can be wrong or out of date, and the PSP's GPS is not as
    precise as a modern phone. Always obey traffic signs and signals and use
    your own judgment while driving.
  * Please do not operate the PSP while driving. Set your destination before
    you leave, or have a passenger do it.
  * Maps are a snapshot of the data at the time you built them. Rebuild your
    maps every so often (for example every few months) to pick up new roads
    and businesses.
  * Beeps are the only sound. Turn them off with Circle.
  * The PSP battery drains faster with the screen and GPS receiver on. In a
    car, keep it plugged into a charger.


------------------------------------------------------------------------------
  15. CREDITS
------------------------------------------------------------------------------

The program, the map maker and this guide were written entirely by AI
(Claude, made by Anthropic), directed only by prompts from the project's
creator. No human wrote the code.

GPSP is free to use, copy, change and share under the MIT License. The full
text is in the file LICENSE.txt. In short: do what you like with it, but it
comes with no warranty. The license covers GPSP only; the OpenStreetMap data
in your maps has its own license, described below.

Map data (c) OpenStreetMap contributors, available under the Open Database
License (ODbL). See https://www.openstreetmap.org/copyright

Any map you build with make_map.py contains OpenStreetMap data, so if you
share a map file with others, please keep this credit with it.


------------------------------------------------------------------------------
  16. GLOSSARY
------------------------------------------------------------------------------

Custom firmware (CFW)   A modified PSP system software that allows you to run
                        homebrew programs such as GPSP.
EBOOT.PBP               The program file that the PSP runs. Think of it like
                        the "app".
Homebrew                Programs made by hobbyists rather than sold by Sony.
.pmap                   The map file format GPSP uses. You make these with
                        make_map.py.
OpenStreetMap           A free map of the world made by volunteers. It is the
                        source of the road and business data in your maps.
Python                  A free programming language. You install it so your
                        computer can run make_map.py.
GPS fix                 When the receiver has locked on to enough satellites
                        to know where you are.
North-up / heading-up   North-up keeps north at the top of the screen.
                        Heading-up turns the map so the direction you are
                        traveling is at the top.
Reroute                 When you leave the planned route, GPSP works out a
                        new route from where you are now.
Latitude / longitude    The two numbers that describe a place on Earth:
                        latitude is north/south, longitude is east/west.

Enjoy the drive!
