import hashlib
import os

from imp import load_source

from bootstrap.utilities.path import assert_directories

from bootstrap.templates.res import CONTAINER_TEMPLATE, FLAG_TEMPLATE
from bootstrap.templates.h import HEADER_CONTAINER_TEMPLATE, HEADER_DEFINITION_TEMPLATE
from bootstrap.templates.str import STR_CONTAINER_TEMPLATE, STR_DEFINITION_TEMPLATE

class Description(object):

    def __init__(self, name, strings, description, flags=None, children=None):
        if flags is None:
            flags = []

        if children is None:
            children = []

        self.name = name
        self.strings = strings
        self.description = description
        self.flags = flags
        self.children = children

    def GetId(self):
        return int(hashlib.sha1(self.name.encode('utf-8')).hexdigest(), 16) % (10 ** 8)

    def __str__(self):
        return str(self.GetId())

    def GenerateResource(self):
        data = {
            "resource": self.description,
            "name": self.name,
            "flags": [x.GenerateResource() for x in self.flags],
            "children": [x.GenerateResource() for x in self.children]
        }

        return CONTAINER_TEMPLATE.Render(data)

    def GenerateHeader(self):
        lines = []

        data = {
            "key": self.name,
            "value": self.GetId(),
        }

        lines.append(HEADER_DEFINITION_TEMPLATE.Render(data))

        lines = lines + [x.GenerateHeader() for x in self.children]

        return "\n".join(lines)

    def GenerateStrings(self):
        strings = {}

        for locale, value in self.strings.items():
            lines = []

            data = {
                "key": self.name,
                "value": value,
            }

            lines.append(STR_DEFINITION_TEMPLATE.Render(data))

            lines = lines + [x.GenerateStrings()[locale] for x in self.children]

            strings[locale] = "\n".join(lines)
        
        return strings

class DescriptionFlag(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def GenerateResource(self):
        data = {
            "key": self.name,
            "value": self.value
        }

        return FLAG_TEMPLATE.Render(data)

class Group(Description):

    def __init__(self, name, strings, flags, children):
        super(Group, self).__init__(name, strings, "GROUP", flags, children)

class Layout(object):

    def __init__(self, name, strings, flags, group):
        self.name = name
        self.strings = strings
        self.flags = flags
        self.group = group

    def Build(self, path):
        dirname, filename = os.path.split(path)
        filenameRoot, filenameExtension = os.path.splitext(filename)

        descriptionPath = os.path.join(dirname, "res/description")

        # generate resource
        resourcePath = os.path.join(descriptionPath, "{}.res".format(self.name.lower()))

        assert_directories(resourcePath)

        with open(resourcePath, "w") as f:
            f.write(self.GenerateResource())

        print("done writing {}".format(resourcePath))

        # generate header
        headerPath = os.path.join(descriptionPath, "{}.h".format(self.name.lower()))

        assert_directories(headerPath)

        with open(headerPath, "w") as f:
            f.write(self.GenerateHeader())

        print("done writing {}".format(headerPath))

        # generate strings
        strings = self.GenerateStrings()

        for locale, value in strings.items():
            stringsPath = os.path.join(dirname, "res", locale, "description", "{}.str".format(self.name.lower()))
            
            assert_directories(stringsPath)

            with open(stringsPath, "w") as f:
                f.write(value)

            print("done writing {}".format(stringsPath))

        # generate plugin file
        with open(path, "r") as inputFile:
            lines = inputFile.read().split("\n")

            computedLines = []

            ignoreLines = False
            idSection = False

            module = load_source(filenameRoot, path)

            for line in lines:
                # id section
                if line.startswith("#----begin_id_section----"):
                    idSection = True

                    continue

                if line.startswith("#----end_id_section----"):
                    idSection = False

                    continue

                if idSection:
                    variables = [x.strip() for x in line.split("=")]

                    if variables:
                        variableName = variables[0]

                        computedLines.append("{} = {}".format(variableName, getattr(module, variableName)))

                    continue

                # skip bootstrap lines
                if line.startswith("#----begin"):
                    ignoreLines = True

                    continue
                
                if line.startswith("#----end"):
                    ignoreLines = False

                    continue

                if not ignoreLines:
                    computedLines.append(line)  

            pluginPath = os.path.join(dirname, "{}.pyp".format(filenameRoot))

            with open(pluginPath, "w") as outputFile:
                outputFile.write("\n".join(computedLines))

            print("done writing {}".format(pluginPath))


    def GenerateResource(self):
        data = {
            "resource": "CONTAINER",
            "name": self.name,
            "flags": [flag.GenerateResource() for flag in self.flags],
            "children": self.group.GenerateResource()
        }
        
        lines = [
            "// auto generated by bootstrap",
            CONTAINER_TEMPLATE.Render(data)
        ]

        return "\n".join(lines)

    def GenerateHeader(self):
        data = {
            "children": self.group.GenerateHeader()
        }

        lines = [
            "// auto generated by bootstrap",
            HEADER_CONTAINER_TEMPLATE.Render(data)
        ]

        return "\n".join(lines)

    def GenerateStrings(self):
        strings = {}

        for locale, value in self.strings.items():
            pluginData = {
                "key": self.name,
                "value": value
            }

            data = {
                "name": self.name,
                "pluginName": STR_DEFINITION_TEMPLATE.Render(pluginData),
                "children": self.group.GenerateStrings()[locale]
            }

            lines = [
                "// auto generated by bootstrap",
                STR_CONTAINER_TEMPLATE.Render(data)
            ]

            strings[locale] = "\n".join(lines)

        return strings