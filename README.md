A small python script for creating to-scale reaction profile diagrams in PDF form, shared under the <a href="https://choosealicense.com/licenses/mit/">MIT license</a>.

<h3>About</h3>
This tool was born to help students in physical chemistry labs make publication quality figures for their lab reports. Before writing this I could not find a covenient way to plot accurate to-scale energy level diagrams, and this script aims to address this. The script has since found used in a few of my own projects that needed accurate energy profile diagrams, even ending up in <a href="https://dx.doi.org/10.1021/acs.jctc.5b00535">published work</a>. As I wrote the script with inexperienced users in mind it tries to be as tolerant to input errors as possible, troopering on where possible, and advising where not.

The script is written in python, compatible with 2 and 3, and was recently updated to require only the matplotlib library. It uses the "Agg" matplotlib backend, so will happily operate on a headless machine over SSH.

<hr>

<h3>General Operation</h3>
The diagram is defined by an input file passed to the script as the first argument. The script is invoked as:

<code> python EnergyLeveler.py inputfile.inp</code>

Running the script without an input file will print an example input file to the terminal.

<hr>

<h3>Input File Structure</h3>
The simplest way to understand the input to modify the example given below, though a full description is given here for completeness.

The input file is structured as a block of general parameters for the overall plot appearance followed by a series of states defined in curly brace separated blocks. A state is identified in the script by a unique name allowing the definition of lines showing reaction pathways between named states. Lines beginning with a hash symbol <code>#</code> are ignored by the script and can be used to add comments to input files.

<br style="margin-top:2px;">
<h4>General Input</h4>
The following common options control the overall output and are entered as <code>key = value</code>.
<table>
<tbody>
<tr>
<td><code>output-file</code></td>
<td>File name to save the output to.</td>
</tr>
<tr>
<td><code>width</code></td>
<td>Width of the output image.</td>
</tr>
<tr>
<td><code>height</code></td>
<td>Height of the output image.</td>
</tr>
<tr>
<td><code>font-size</code></td>
<td>Font size of all text.</td>
</tr>
<tr>
<td><code>energy-units</code></td>
<td>Unit label for the vertical scale.</td>
</tr>
<tr>
<td><code>energy range</code></td>
<td>Sets the range of the Y axis. Expects comma upper and lower energy bounds.</td>
</tr>
</tbody>
</table>
The code will accept any <a href="https://matplotlib.org/api/colors_api.html">matplotlib compatible colour definition.</a>
<h4>State Input</h4>
Points in the diagram are defined as individual states with various properties defined in the input using curly brace blocks with the following fields entered again as <code>key = value</code>.
<table>
<tbody>
<tr>
<td><code>name</code></td>
<td>The name used by the program to refer to the state when drawing links. <em>The name is <b>not</b> displayed in the final image.</em></td>
</tr>
<tr>
<td><code>label</code></td>
<td>The name displayed for the state above the energy level line. Accepts <a href="https://matplotlib.org/users/mathtext.html#mathtext-tutorial">matplotlib mathtex markup language</a>.</td>
</tr>
<tr>
<td><code>text-colour</code></td>
<td>The colour used for the state's label and numerical energy value. Colours defined in general input can be requested by name.</td>
</tr>
<tr>
<td><code>state-colour</code></td>
<td>The colour used for drawing the state's energy line. Colours defined in general input can be requested by name here.</td>
</tr>
<tr>
<td><code>energy</code></td>
<td>The energy of the state, defining its vertical position, printed below the state line.</td>
</tr>
<tr>
<td><code>column</code></td>
<td>The horizontal position of the state, defined as an integer column number starting from 1.</td>
</tr>
<tr>
<td><code>label-offset</code></td>
<td>A shift in pixels to the state label text, defined as <code>x,y</code>. Useful for fixing overlapping state labels.</td>
</tr>
<tr>
<td><code>energy-text-offset</code></td>
<td>A shift in pixels to the printed energy text, defined as <code>x,y</code>.</td>
</tr>
<tr>
<td><code>links-to</code></td>
<td>Links this state to others in the diagram, discussed in detail below.</td>
</tr>
<tr>
<td><code>hide energy</code></td>
<td>Flags that we should not print a label showing the energy of the state.</td>
</tr>
</tbody>
</table>
States can be linked together to show reaction pathways using the state option <code>links-to</code> with a comma delimited list of named states to connect to. A dashed line is drawn from the right edge of the current state to the left edge of the listed state. A colour for this line can be specified using <code>:colour</code> after the destination state name. User defined colours can be used. For example:

<code>links-to = state2:red,state3:blue</code>

The label drawn above the states uses the <a href="https://matplotlib.org/users/mathtext.html#mathtext-tutorial">matplotlib mathtex markup language</a> to allow super and sub scripts, and other embellishments, in the labels.

<hr>

<h3>Example Input</h3>
An example input is given here, same is printed if the script is run without an input file.

<pre>
output-file     = example.pdf
output-file     = example.pdf
width           = 8
height          = 8
energy-units    = $\Delta$E  kJ/mol
energy range    = -15,35
font size       = 10

#   This is a comment. Lines that begin with a # are ignored.
#   Available colours are those accepted by matplotlib 

#   Now begins the states input

#-------  Path 1 ----------

#   Add the first path, all paths are relative to the reactant energies so
#   start at zero

{
    name        = reactants
    text-colour = black
    label       = CH$_3$O$\cdot$ + X
    energy      = 0.0
    labelColour = black
    linksto     = pre-react1:red, transition2:#003399, pre-react3:#009933
    column      = 1
}

{
    name        = pre-react1
    text-colour = red
    label       = CH$_3$O$\cdot$ $\ldots$ X
    energy      = -10.5
    labelColour = red
    linksto     = transition1:red
    column      = 2
}

{
    name        = transition1
    text-colour = red
    label       = [CH$_3$O$\cdot$ $\ldots$ X]$^{++}$
    energy      =    +20.1
    labelColour = red
    linksto     = post-react1:red
    column      = 3
}

{
    name        = post-react1
    text-colour = red
    label       = $\cdot$CH$_2$OH $\ldots$ X
    energy      = -8.2
    labelColour = red
    linksto     = products:red
    column      = 4
    legend      = Catalyst 2
}

#   All the paths in this practical end at the same energy… why?

{
    name        = products
    text-colour = black
    label       =    $\cdot$CH$_2$OH + X
    energy      = -2.0
    labelColour = black
    column      = 5
}
#--------  Path 2 -------------
{
    name        = transition2
    text-colour = #003399
    label       = [CH$_3$O$\cdot$]$^{++}$
    energy      = +30.1
    labelColour = #003399
    linksto     = products:#003399
    column      = 3
    legend      = Uncatalysed
}

#-------  Path 3 -----------
{
    name        = pre-react3
    text-colour = #009933
    label       =    CH$_3$O$\cdot$ $\ldots$ X
    energy      = -8.3
    labelColour = #009933
    linksto     = transition3:#009933
    column      = 2
    legend      = Catalyst 1
    labelOffset = 0,1
    textOffset  = 0,1.4
}

{
    name        = transition3
    text-colour = #009933
    label       = [CH$_3$O$\cdot$ $\ldots$ X]$^{++}$
    energy      = +25.4
    labelColour = #009933
    linksto     = post-react3:#009933
    column      = 3
}

{
    name        = post-react3
    text-colour = #009933
    label       = $\cdot$CH$_2$OH $\ldots$ X
    energy      = -6.1
    labelColour = #009933
    linksto     = products:#009933
    column      = 4
    labelOffset = 0,1
    textOffset  = 0,1.4
}
</pre>

<hr>

<h3>License</h3>
This code is shared under the <a href="https://choosealicense.com/licenses/mit/">MIT license</a>  Copyright 2017 James Furness.
You are free to use, modify and distribute the code, though recognition of my effort is appreciated!

If you require a feature that is missing from the script please feel free to get in contact with me and I'll look at implementing it, though no guarantee is made. Alternatively you can dig in and add it yourself. If you do I'd love to hear about it and update the copy here with your new functionality (credited of course).
