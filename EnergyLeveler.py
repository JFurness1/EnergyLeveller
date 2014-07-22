#!/opt/local/bin/python
import cairo
import math
import sys
import pango
import pangocairo

class Diagram:
    statesList  = {}
    dashes      = [6.0,3.0] # ink, skip
    COLORS = {'RED': [1.0,0,0], 'GREEN':[0,1.0,0], 'BLUE':[0,0,1.0], 'BLACK':[0,0,0], 'WHITE':[1,1,1]}
    outputName  = ""
    columns     = 0
    width       = 0
    height      = 0
    energyUnits = ""
    #ps          = 0
    #cr          = 0

    def __init__(self, width, height, outputName):
        self.width = width
        self.height = height
        self.outputName = outputName

        self.ps = cairo.PDFSurface(self.outputName, self.width, self.height)
        self.cr = cairo.Context(self.ps)
        self.cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        self.cr.set_font_size(12)

        self.pgcr = pangocairo.CairoContext(self.cr)
        self.pgcr.set_antialias(cairo.ANTIALIAS_SUBPIXEL)

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

#    def AddState(self, name, color, label, labelColor, linkedTo, energy, column): #"test1","test2","",-100,0
#        name = name.upper()
#        color = color.upper()
#        label = label.upper()
#        labelColor = labelColor.upper()
#        linkedTo = linkedTo.upper()
#        if name not in self.statesList:
#            self.statesList[name] = State(name, color, label, labelColor, linkedTo, energy, column)
#        else:
#            print "ERROR: States must have unique names. State " + name + " is already in use!"
#            sys.exit("Non unique state names.")

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
            self.SetTextRGB(state.labelColor)
            self.pgcr.move_to(state.leftPointx + 5,state.leftPointy-18)
            self.layout.set_markup(state.label)
            self.pgcr.update_layout(self.layout)
            self.pgcr.show_layout(self.layout)

            self.pgcr.move_to(state.leftPointx + 5,state.leftPointy+5)
            self.layout.set_markup(str(state.energy) + " " + self.energyUnits)
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

    def DrawAxes(self):
        drawHeight = (self.height-2*self.vOffset)
        startX = self.LOffset
        startY = self.height - self.vOffset + 10
        endX   = self.LOffset
        endY   = self.vOffset - 10
        arrowDeg = 0.3
        arrowLength = 7
        angle = math.atan2( endY - startY, endX - startX) + math.pi

        self.SetSourceRGB('BLACK')
        self.cr.set_line_width(1)
        self.cr.set_line_join(cairo.LINE_JOIN_BEVEL)
        self.cr.move_to(startX, startY)
        self.cr.line_to(endX, endY)
        self.cr.line_to(endX + arrowLength * math.cos(angle + arrowDeg), endY + arrowLength * math.sin(angle + arrowDeg))
        self.cr.move_to(endX, endY)
        self.cr.line_to(endX + arrowLength * math.cos(angle - arrowDeg), endY + arrowLength * math.sin(angle - arrowDeg))
        self.cr.stroke()

        self.cr.set_dash([1.0,10.0])
        self.cr.set_line_width(1)
        self.cr.move_to(self.LOffset,self.axesOriginNormalised*drawHeight + self.vOffset)
        self.cr.line_to(self.width-self.LOffset,self.axesOriginNormalised*drawHeight + self.vOffset)
        self.cr.stroke()

        zeroText = self.pgcr.create_layout()
        zeroText.set_font_description(self.font)
        zeroText.set_markup("0.0")
        self.pgcr.move_to(self.LOffset - zeroText.get_pixel_size()[0] - 2, self.axesOriginNormalised*drawHeight + self.vOffset - zeroText.get_pixel_size()[1]/2.0)
        self.pgcr.update_layout(zeroText)
        self.pgcr.show_layout(zeroText)

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

    lc = 0
    for line in inp:
        lc += 1
        line = line.strip()
        if (len(line) > 0 and line.strip()[0] != "#"):
            if (stateBlock):
                if (line.strip()[0] == "{"):
                    print "Unexpected opening '{' within state block on line " + str(lc) + ".\nPossible forgotten closing '}'."
                if (line.strip()[0] == "}"):
                    stateBlock = False
                else:
                    raw = line.split('=')
                    if (len(raw) > 2):
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
                print "ERROR: Not expecting closing } on line: " + str(lc)

            else:
                raw = line.split('=')
                if (len(raw) > 2):
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
                    else:
                        print "WARNING: Skipping unknown line " + str(lc) + ":\n\t" + line

    if (width == 0):
        print "ERROR: Image height not set! e.g.:\nheight = 500"
        system.exit("Height not set")
    if (width == 0):
        print "ERROR: Image width not set! e.g.:\nwidth = 500"
        system.exit("Width not set")
    if (outName == ""):
        print "ERROR: output file name not set! e.g.:\n output-file = example.pdf"
        system.exit("Output name not set")

    outDiagram = Diagram(width, height, outName)
    outDiagram.energyUnits = energyUnits

    maxColumn = 0
    for state in statesList:
        outDiagram.AddState(state)
        if (state.column > maxColumn):
            maxColumn = state.column
    outDiagram.columns = maxColumn + 1

    return outDiagram

######################################################################################################
#           Main driver function
######################################################################################################

def main():

    print "o=======================================================o"
    print "         Beginning Energy Level Diagram"
    print "o=======================================================o"

    if (len(sys.argv) != 2):
        print "Incorrect arguments. Correct call:\npython EnergyLeveler.py <INPUT FILE>"
        sys.exit("Incorrect Arguments.")

    diagram = ReadInput(sys.argv[1])

    diagram.DetermineEnergyRange()
    diagram.MakeLeftRightPoints()

    diagram.Draw()

    print "o=======================================================o"
    print " )            Image "+diagram.outputName+" made!"
    print "o=======================================================o"

if __name__ == "__main__":
    main()
