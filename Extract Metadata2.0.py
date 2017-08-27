import xml.etree.cElementTree as etree
import xml.dom.minidom as minidom
from netCDF4 import Dataset
import glob, os

class NCFDimension:
    name= ""
    standardName = ""
    longName= ""
    size=0
    def __init__(self,name, standardName,size ): # Class constructor
        self.name = name
        self.standardName = standardName
        self.size = size

class NCFVariable:
    name = ""
    dimensions = []
    size = 0
    otherAttributes = {}
    def __init__(self,name,dimensions,size, otherAttributes ): # Class constructor
        self.name = name
        self.dimensions = dimensions
        self.size = size
        self.otherAttributes = otherAttributes

def ExtractMetadata(readDirectory,fileName):
    metadata = {}
    #First, reading basic info
    metadata["Title"]= fileName
    nc_fid = Dataset(readDirectory+fileName)
    metadata["Creator"]=nc_fid.getncattr("contact")
    metadata["Publisher"]=nc_fid.getncattr("institution")
    metadata["Driving_Experiment"]=nc_fid.getncattr("driving_experiment")#Custom element to DC
    metadata["CORDEX_Domain"]=nc_fid.getncattr("CORDEX_domain")#Custom element to DC
    metadata["Date"]=nc_fid.getncattr("creation_date")
    metadata["Coverage"]=nc_fid.getncattr("frequency")
    #Second, getting dimensions info
    nc_dims = [dim for dim in nc_fid.dimensions]
    dimensions = []

    for dim in nc_dims:
        dimension = NCFDimension(name=dim, standardName= nc_fid.dimensions[dim].name
                                 , size =len(nc_fid.dimensions[dim]))
        dimensions.append(dimension)
    metadata["Dimensions"] = dimensions
    #Last, getting variables info
    variables = []
    nc_vars = [var for var in nc_fid.variables]
    for var in nc_vars:
        if var not in nc_dims:
            varName = var
            varDimensions = nc_fid.variables[var].dimensions
            varSize= nc_fid.variables[var].size
            otherAttributes ={}
            for attribute in nc_fid.variables[var].ncattrs():
                otherAttributes [attribute] =  nc_fid.variables[var].getncattr(attribute)

            variable = NCFVariable(name= varName, dimensions= varDimensions
                                   , size = varSize, otherAttributes= otherAttributes )
            variables.append(variable)
    metadata["Variables"] = variables
    return metadata

def WriteXML(writeDirectory,metadata):
    root = etree.Element("dublin_core")
    etree.SubElement(root, "dcvalue", element="Title").text = metadata["Title"]
    etree.SubElement(root, "dcvalue", element="Creator").text = metadata["Creator"]
    etree.SubElement(root, "dcvalue", element="Publisher").text = metadata["Publisher"]
    etree.SubElement(root, "dcvalue", element="Date").text = metadata["Date"]
    etree.SubElement(root, "dcvalue", element="Coverage").text = metadata["Coverage"]
    etree.SubElement(root, "CORDEX_Domain").text = metadata["CORDEX_Domain"]
    etree.SubElement(root, "Driving_Experiment").text = metadata["Driving_Experiment"]
    #Writing dimensions
    for dimension in metadata["Dimensions"]:
        dimensionElement = etree.SubElement(root, "Dimension")
        etree.SubElement(dimensionElement, "Standard_Name").text= dimension.name
        etree.SubElement(dimensionElement, "Size").text = str(dimension.size)
    # Writing variables
    for variable in metadata["Variables"]:
        variableElement = etree.SubElement(root, "Variable")
        etree.SubElement(variableElement, "Name").text = variable.name
        etree.SubElement(variableElement, "Size").text = str(variable.size)
        for dimension in variable.dimensions:
            etree.SubElement(variableElement, "Dimension").text = dimension
        for key in variable.otherAttributes.keys():
            etree.SubElement(variableElement, key).text = str(variable.otherAttributes[key])

    xmlOutput = minidom.parseString(etree.tostring(root, 'utf-8')) \
        .toprettyxml(indent="\t")

    with open(writeDirectory+metadata["Title"]+".xml", "w") as f:
        f.write(xmlOutput)

def main():
    readDirectory ="NetCDF/"
    writeDirectory = "Output/"

    directory_list = list()
    for root, dirs, files in os.walk(readDirectory, topdown=False):
        for name in dirs:
            directory_list.append(name+"/")

    for folder in directory_list:
        os.chdir(readDirectory+folder)
        for file in glob.glob("*.nc"):
            print("Current file: "+readDirectory+folder+file)
            metadata = ExtractMetadata(readDirectory+folder,file)
            if not os.path.exists(writeDirectory+folder):
                os.makedirs(writeDirectory+folder)
            WriteXML(writeDirectory+folder,metadata)

main()
