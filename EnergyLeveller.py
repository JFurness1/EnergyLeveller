#!/opt/local/bin/python
# coding=UTF-8
import cairo
import math
import sys
import pango
import pangocairo
import os.path

class Diagram:
    statesList  = {}
    dashes      = [6.0,3.0] # ink, skip
    COLORS = {'RED': [204.0/255.0,37.0/255.0,48.0/255.0], 'GREEN':[62.0/255.0,150.0/255.0,81.0/255.0], 'BLUE':[57.0/255.0,106.0/255.0,177.0/255.0], 'PURPLE':[107.0/255.0,76.0/255.0,154.0/255.0], 'ORANGE':[218.0/255.0,124.0/255.0,48.0/255.0], 'YELLOW':[148.0/255.0,139.0/255.0,61.0/255.0], 'BROWN':[146.0/255.0, 36.0/255.0, 40.0/255.0], 'PINK':[0.97, 0.51, 0.75], 'BLACK':[0,0,0], 'GRAY':[83.0/255.0,81.0/255.0,84.0/255.0], 'LIGHTGRAY':[183.0/255.0,181.0/255.0,184.0/255.0]}
    outputName  = ""
    columns     = 0
    width       = 0
    height      = 0
    tickSize    = 0
    energyUnits = ""

    def __init__(self, width, height, outputName):
        self.width = width
        self.height = height
        self.outputName = outputName

        self.ps = cairo.PDFSurface(self.outputName, self.width, self.height)
        self.cr = cairo.Context(self.ps)
        self.cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        self.cr.set_font_size(12)

        self.pgcr = pangocairo.CairoContext(self.cr)
        self.pgcr.set_antialias(cairo.ANTIALIAS_GRAY)

        self.layout = self.pgcr.create_layout()
        self.fontname = "Times New Roman"
        self.font = pango.FontDescription(self.fontname + " 8")
        self.layout.set_font_description(self.font)

        self.vOffset = 30
        self.LOffset = 30
        self.axesTop = 0.0
        self.axesBot = 0.0
        self.axesTick= 1.0
        self.axesOriginNormalised = 0.0


    def AddState(self, state):
        state.name = state.name.upper()
        state.color = state.color.upper()
        state.label = state.label
        state.labelColor = state.labelColor.upper()
        state.linksTo = state.linksTo.upper()
        if state.name not in self.statesList:
            self.statesList[state.name] = state
        else:
            print "ERROR: States must have unique names. State " + name + " is already in use!"
            sys.exit("Non unique state names.")

    def DetermineEnergyRange(self):
        if len(self.statesList) == 0:
            sys.exit("No states in diagram.")
        maxE = -10E20
        minE = 10E20
        for state in self.statesList.itervalues():
            if state.energy > maxE:
                maxE = state.energy
            if state.energy < minE:
                minE = state.energy
        self.axesTop = maxE
        self.axesMin = minE
        self.axesOriginNormalised =  1+(minE / (maxE - minE))
        return [minE, maxE]

    def MakeLeftRightPoints(self):
        columnWidth = self.width / (2 * self.columns)
        eRange = self.DetermineEnergyRange()
        drawHeight = (self.height-2*self.vOffset)

        for key, state in self.statesList.items():
            state.normalisedPosition = 1 - (state.energy - eRange[0]) / (eRange[1] - eRange[0])
            state.leftPointx = (columnWidth/2) + state.column*columnWidth + (state.column)*(columnWidth/2) + self.LOffset
            state.leftPointy = state.normalisedPosition*drawHeight + self.vOffset
            state.rightPointx = state.leftPointx + columnWidth
            state.rightPointy= state.leftPointy

    def Draw(self):
#   Draw the states themselves
        for state in self.statesList.itervalues():
            self.SetSourceRGB(state.color)
            self.cr.set_line_width(3)
            self.cr.move_to(state.leftPointx, state.leftPointy)
            self.cr.line_to(state.rightPointx, state.rightPointy)
            self.cr.stroke()

#   Draw their labels
        for state in self.statesList.itervalues():
            labelUpperText = self.pgcr.create_layout()
            labelUpperText.set_font_description(self.font)
            labelUpperText.set_markup(state.label)
            self.SetTextRGB(state.labelColor)
            LUTpixSize = labelUpperText.get_pixel_size()
            self.pgcr.move_to(state.leftPointx + 5,state.leftPointy - (LUTpixSize[1] + 1))
            self.pgcr.update_layout(labelUpperText)
            self.pgcr.show_layout(labelUpperText)

            self.pgcr.move_to(state.leftPointx + 5,state.leftPointy+3)
            self.layout.set_markup("  " + str(state.energy) )
            self.pgcr.update_layout(self.layout)
            self.pgcr.show_layout(self.layout)

#   Draw the dashed lines connecting them
        for state in self.statesList.itervalues():
            if (state.linksTo != ""):
                self.cr.set_dash(self.dashes)
                self.cr.set_line_width(1)
                for link in state.linksTo.split(','):
                    link = link.strip()
                    raw = link.split(':')
                    dest = raw[0]
                    if len(raw) > 1:
                        color = raw[1]
                    else:
                        color = 'BLACK'
                    if dest in self.statesList:
                        self.SetSourceRGB(color)
                        self.cr.move_to(state.rightPointx, state.rightPointy)
                        self.cr.line_to(self.statesList[dest].leftPointx, self.statesList[dest].leftPointy)
                        self.cr.stroke()
                    else:
                        print "Name: " + dest + " is unknown."

        self.cr.stroke()
        self.cr.set_dash({})
        self.DrawAxes()
        self.cr.show_page()
    def EnergyToAxes(self, inEn):
        eRange = self.DetermineEnergyRange()
        return (inEn + eRange[0]) / eRange[1]

    def DrawAxes(self):
        drawHeight = (self.height-2*self.vOffset)
        startX = self.LOffset
        startY = self.height - self.vOffset + 10
        endX   = self.LOffset
        endY   = self.vOffset - 10
        arrowDeg = 0.3
        arrowLength = 7
        angle = math.atan2( endY - startY, endX - startX) + math.pi
        eRange = self.DetermineEnergyRange()
        tickStep = pow(10, math.floor(math.log10(eRange[1]-eRange[0])))
        tickWidth = 5
        if ((eRange[1]-eRange[0]) / tickStep < 5):
            tickStep = tickStep/2.0

        self.SetSourceRGB('BLACK')
        self.cr.set_line_width(1)
        self.cr.set_line_join(cairo.LINE_JOIN_BEVEL)
#   Draw Line
        self.cr.move_to(startX, startY)
        self.cr.line_to(endX, endY)
        self.cr.line_to(endX + arrowLength * math.cos(angle + arrowDeg), endY + arrowLength * math.sin(angle + arrowDeg))
#   Draw Arrow
        self.cr.move_to(endX, endY)
        self.cr.line_to(endX + arrowLength * math.cos(angle - arrowDeg), endY + arrowLength * math.sin(angle - arrowDeg))
        self.cr.stroke()
#   Draw Energy ticks
        tEn = int(eRange[0]/tickStep) * tickStep
        while ( tEn <= eRange[1]):
            tY = (1- (tEn - eRange[0]) / (eRange[1] - eRange[0])) * drawHeight + self.vOffset
            self.cr.move_to(startX, tY)
            self.cr.line_to(startX + tickWidth, tY)
            self.cr.stroke()

            zeroText = self.pgcr.create_layout()
            zeroText.set_font_description(self.font)
            zeroText.set_markup(str(tEn))
            self.pgcr.move_to(self.LOffset + 7, tY - zeroText.get_pixel_size()[1]/2.0)
            self.pgcr.update_layout(zeroText)
            self.pgcr.show_layout(zeroText)

            zeroOfset = zeroText.get_pixel_size()[0]

            if( tEn != 0):
                self.cr.set_dash([1.0,10.0])
                self.SetSourceRGB('LIGHTGRAY')
            else:
                self.cr.set_dash([2.0,9.0])
                self.SetSourceRGB('GRAY')
            tEn = tEn + tickStep
            self.cr.set_line_width(1)
            self.cr.move_to(self.LOffset + zeroOfset + 10, tY)
            self.cr.line_to(self.width-5,tY)
            self.cr.stroke()
            self.cr.set_dash([1.0,0.0])
            self.SetSourceRGB('BLACK')
        tY = (1- (0 - eRange[0]) / (eRange[1] - eRange[0])) * drawHeight + self.vOffset
        zeroText = self.pgcr.create_layout()
        zeroText.set_font_description(pango.FontDescription(self.fontname + " 12"))
        zeroText.set_markup(str(self.energyUnits))
        self.pgcr.move_to(self.LOffset - zeroText.get_pixel_size()[1]/2,tY - zeroText.get_pixel_size()[0]/2.0)
        self.pgcr.rotate(math.pi/2.0)
        self.pgcr.update_layout(zeroText)
        self.pgcr.show_layout(zeroText)
#   Draw 0 line
#   Draw 0 text


    def SetSourceRGB(self,color):
        if color in self.COLORS:
            self.cr.set_source_rgb(self.COLORS[color][0],self.COLORS[color][1],self.COLORS[color][2])
        else:
            print "Colour: " + color + " not a known colour!"
            self.cr.set_source_rgb(0,0,0)

    def SetTextRGB(self,color):
        if color in self.COLORS:
            self.pgcr.set_source_rgb(self.COLORS[color][0],self.COLORS[color][1],self.COLORS[color][2])
        else:
            print "Colour: " + color + " not a known colour!"
            self.pgcr.set_source_rgb(0,0,0)

class State:
    name        = ""
    color       = ""
    labelColor  = ""
    linksTo     = ""
    label       = ""
    energy      = 0.0
    normalisedPosition = 0.0
    column      = 1
    leftPointx  = 0
    leftPointy  = 0
    rightPointx = 0
    rightPointy = 0


#    def __init__(self, name, color, label, labelColor, linksTo, energy, column):
#        self.name = name
#        self.color = color
#        self.label =label
#        self.labelColor = labelColor
#        self.linksTo = linksTo
#        self.energy = float(energy)
#        self.column = column

######################################################################################################
#           Input reading block
######################################################################################################

def ReadInput(filename):
    try:
        inp = open(filename,'r')
    except:
        print "Error opening file. File: " + filename + " may not exist."
        sys.exit("Could not open Input file.")

    stateBlock = False
    statesList = []
    width = 0
    height = 0
    outputName = ""
    energyUnits = ""
    colorsToAdd = {}
    lc = 0
    for line in inp:
        lc += 1
        line = line.strip()
        if (len(line) > 0 and line.strip()[0] != "#"):
            if (stateBlock):
                if (line.strip()[0] == "{"):
                    print "Unexpected opening '{' within state block on line " + str(lc) + ".\nPossible forgotten closing '}'."
                    sys.exit("ERROR: Unexpected { on line " + str(lc))
                if (line.strip()[0] == "}"):
                    stateBlock = False
                else:
                    raw = line.split('=')
                    if (len(raw) != 2):
                        print "Ignoring unrecognised line " + str(lc) + ":\n\t"+line
                    else:
                        raw[0] = raw[0].upper().strip()
                        raw[1] = raw[1].strip()
                        if (raw[0] == "NAME"):
                            statesList[-1].name = raw[1].upper()
                        elif (raw[0] == "TEXTCOLOR" or raw[0] == "TEXTCOLOUR" or raw[0] == "TEXT-COLOUR" or raw[0] == "TEXT-COLOR" or raw[0] == "TEXT COLOUR" or raw[0] == "TEXT COLOR"):
                            statesList[-1].color = raw[1].upper()
                        elif (raw[0] == "LABEL"):
                            statesList[-1].label = raw[1]
                        elif (raw[0] == "LABELCOLOR" or raw[0] == "LABELCOLOUR"):
                            statesList[-1].labelColor = raw[1].upper()
                        elif (raw[0] == "LINKSTO" or raw[0] == "LINKS TO"):
                            statesList[-1].linksTo = raw[1].upper()
                        elif (raw[0] == "COLUMN"):
                            try:
                                statesList[-1].column = int(raw[1])-1
                            except ValueError:
                                print "ERROR: Could not read integer for column number on line " + str(lc)+ ":\n\t"+line
                        elif (raw[0] == "ENERGY"):
                            try:
                                statesList[-1].energy = float(raw[-1])
                            except ValueError:
                                print "ERROR: Could not read real number for energy on line " + str(lc)+ ":\n\t"+line
                        else:
                            print "Ignoring unrecognised line " + str(lc) + ":\n\t"+line

            elif (line.strip()[0] == "{"):
                statesList.append(State())
                stateBlock = True   # we have entered a state block

            elif (line.strip()[0] == "}"):
                print "WARNING: Not expecting closing } on line: " + str(lc)

            else:
                raw = line.split('=')
                if (len(raw) != 2):
                    print "Ignoring unrecognised line " + str(lc) + ":\n\t"+line
                else:
                    raw[0] = raw[0].upper().strip()
                    raw[1] = raw[1].strip().lstrip()
                    if (raw[0] == "WIDTH"):
                        try:
                            width = int(raw[1])
                        except ValueError:
                            print "ERROR: Could not read integer for diagram width on line " + str(lc)+ ":\n\t"+line
                    elif (raw[0] == "HEIGHT"):
                        try:
                            height = int(raw[1])
                        except ValueError:
                            print "ERROR: Could not read integer for diagram height on line " + str(lc)+ ":\n\t"+line
                    elif (raw[0] == "OUTPUT-FILE" or raw[0] == "OUTPUT"):
                        raw[1] = raw[1].lstrip()
                        if ( not raw[1].endswith('.pdf')):
                            print "WARNING: Output will be .pdf. Adding this to output file.\nFile will be saved as "+raw[1] + ".pdf"
                            outName = raw[1] + ".pdf"
                        else:
                            outName = raw[1]
                    elif (raw[0] == "ENERGY-UNITS" or raw[0] == "ENERGYUNITS" or raw[0] == "ENERGY UNITS"):
                        energyUnits = raw[1]
                    elif(raw[0] == "NEW COLOUR" or raw[0] == "NEW COLOR"):
                        parts = raw[1].split(',')
                        if (len(parts) != 4):
                            print "WARNING: Could not read colour. Please use comma sepparated NAME,R,G,B format. Line:" + str(lc)+ ":\n\t"+line
                        else:
                            parts[0] = parts[0].upper()
                            if (parts[0] not in colorsToAdd):
                                try:
                                    R = float(parts[1])
                                    G = float(parts[2])
                                    B = float(parts[3])
                                    colorsToAdd[parts[0]] = [R, G, B]
                                except ValueError:
                                    print "WARNING: Could not understand colour on line: "+ str(lc)+ ":\n\t"+line
                            else:
                                print "WARNING: Colour: " + parts[0] + " already defined at line: " + str(lc)+ ":\n\t"+line
                    else:
                        print "WARNING: Skipping unknown line " + str(lc) + ":\n\t" + line
    if (stateBlock):
        print "WARNING: Final closing '}' is missing."
    if (width == 0):
        print "ERROR: Image height not set! e.g.:\nheight = 500"
        sys.exit("Height not set")
    if (width == 0):
        print "ERROR: Image width not set! e.g.:\nwidth = 500"
        sys.exit("Width not set")
    if (outName == ""):
        print "ERROR: output file name not set! e.g.:\n output-file = example.pdf"
        sys.exit("Output name not set")

    outDiagram = Diagram(width, height, outName)
    outDiagram.energyUnits = energyUnits
    for color in colorsToAdd:
        outDiagram.COLORS[color] = colorsToAdd[color]
    maxColumn = 0
    for state in statesList:
        outDiagram.AddState(state)
        if (state.column > maxColumn):
            maxColumn = state.column
    outDiagram.columns = maxColumn

    return outDiagram


######################################################################################################
#          Example printing function. Skip to bottom.
######################################################################################################

def MakeExampleFile():
    output = open("example.inp", 'w')

    output.write("output-file     = example.pdf\nwidth           = 800\nheight          = 800\nenergy-units    = ∆E  kJ/mol\n\n#   This is a comment. Lines that begin with a # are ignored.\n#   Available colours are 'red', 'blue, 'green' 'purple' 'orange' 'yellow' 'brown' 'pink' 'black' and 'gray'.\n#   New colours are declared with rgb 0.0-1.0 in the style:\n#   NEW COLOUR = NAME,RED,GREEN,BLUE  \n\nnew colour = DarkBlue,0.27,0.51,0.71\n\n#   Now begins the states input\n\n#—————–  Path 1 ————————————————\n\n#   Add the first path, all paths are relative to the reactant energies so\n#   start at zero\n\n{\n    name        = reactants\n    text-colour = black\n    label       = CH<sub>3</sub>O<sup><b>.</b></sup> + X\n    energy      = 0.0\n            labelColour = black\n    linksto     = pre-react1:red, transition2:blue, pre-react3:green\n    column      = 1\n}\n\n{\n    name        = pre-react1\n    text-colour = red\n    label       = CH<sub>3</sub>O<sup><b>.</b></sup> … X\n    energy      = -10.5\n    labelColour = red\n    linksto     = transition1:red\n    column      = 2\n}\n\n{\n    name        = transition1\n    text-colour = red\n    label       = [CH<sub>3</sub>O<sup><b>.</b></sup> … X]<sup>‡</sup>\n    energy            =    +20.1\n    labelColour = red\n    linksto     = post-react1:red\n    column      = 3\n}\n\n{\n    name        = post-react1\n    text-colour = red\n    label       = <sup><b>.</b></sup>CH<sub>2</sub>OH … X\n    energy      = -8.2\n    labelColour = red\n    linksto     = products:red\n    column      = 4\n}\n\n#   All the paths in this practical end at the same energy… why?\n\n{\n    name        = products\n    text-colour = black\n    label       =    <sup><b>.</b></sup>CH<sub>2</sub>OH    +    X\n    energy      = -2.0\n    labelColour = black\n    column      = 5\n}\n#—————–  Path 2 ————————————————\n{\n    name        = transition2\n    text-colour = blue\n    label       = [CH<sub>3</sub>O<sup><b>.</b></sup>]<sup>‡</sup>\n    energy      = +30.1\n    labelColour = blue\n    linksto     = products:blue\n    column      = 3\n}\n\n#—————–  Path 3 ————————————————\n{\n    name        = pre-react3\n    text-colour = green\n    label       =    CH<sub>3</sub>O<sup><b>.</b></sup> … X\n    energy      = -8.3\n    labelColour = green\n    linksto     = transition3:green\n    column      = 2\n}\n\n{\n    name        = transition3\n    text-colour = green\n    label       = [CH<sub>3</sub>O<sup><b>.</b></sup> … X]<sup>‡</sup>\n    energy      = +25.4\n    labelColour = green\n    linksto     = post-react3:green\n    column      = 3\n}\n\n{\n    name        = post-react3\n    text-colour = green\n    label            =            <sup><b>.</b></sup>CH<sub>2</sub>OH … X\n    energy      = -6.1\n    labelColour = green\n    linksto     = products:green\n    column      = 4\n}\n")
    output.close()
    print "Made example file as 'example.inp'."

######################################################################################################
#           Main driver function
######################################################################################################
def main():

    print "o=======================================================o"
    print "         Beginning Energy Level Diagram"
    print "o=======================================================o"
    if (len(sys.argv) == 1):
        print "\nI need an input file!\n"
        if (not os.path.exists("example.inp")):
            print "\nAn example file will be made."
            MakeExampleFile()
        sys.exit("No Input file.")
    if (len(sys.argv) > 2):
        print "Incorrect arguments. Correct call:\npython EnergyLeveler.py <INPUT FILE>"
        sys.exit("Incorrect Arguments.")

    diagram = ReadInput(sys.argv[1])

    diagram.DetermineEnergyRange()
    diagram.MakeLeftRightPoints()

    diagram.Draw()

    print "o=======================================================o"
    print "         Image "+diagram.outputName+" made!"
    print "o=======================================================o"

if __name__ == "__main__":
    main()
