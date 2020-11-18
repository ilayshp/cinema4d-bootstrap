import hashlib

from bootstrap.template import Template

resource_container = Template(
"""{key} {id}
{{
    {value}
}}"""
)

resource_assignment = Template("{key} {value};")

locales_container = Template(
"""STRINGTABLE {id}
{{
    {value}
}}
"""
)

locales_assignment = Template("{key} \"{value}\";")

headers_container = Template(
"""#ifndef _Oatom_H_
#define _Oatom_H_

enum
{{
    {value}
}};

#endif
"""
)

headers_assignment = Template("{key} = {id},")

class Description(object):

    def __init__(self, config):
        default_config = {
            "id": None,
            "key": None,
            "value": None,
            "locales": None
        }

        self.config = {**default_config, **config}

    def __getattr__(self, name):
        if name in self.config.keys():
            return self.config[name]

        raise AttributeError("type object 'Description' has no attribute '{}'".format(name))

    def GetId(self):
        if not self.id:
            raise AttributeError("no id has been assigned")

        return int(hashlib.sha1(self.id.encode('utf-8')).hexdigest(), 16) % (10 ** 8)

    def PrepareResourceData(self):
        return {}

    def RenderResource(self):
        pass

    def RenderLocales(self):
        locales = {}

        if isinstance(self.locales, dict):
            for key, value in self.locales.items():
                data = {
                    "key": self.id,
                    "value": value
                }

                locales[key] = locales_assignment.Render(data)

        return locales

    def RenderHeaders(self):
        try:
            data = {
                "key": self.id,
                "id": self.GetId()
            }

            return headers_assignment.Render(data)
        except AttributeError:
            return ""

class Container(Description):

    def PrepareResourceData(self):
        data = {**self.config}

        if isinstance(data["value"], list):
            data["value"] = "\n".join([x.RenderResource() for x in data["value"]]) 

        return data
    
    def RenderResource(self):
        return resource_container.Render(self.PrepareResourceData())

    def RenderLocales(self):
        locales = super(Container, self).RenderLocales()        

        if isinstance(self.value, list):
            for description in self.value:
                child_locales = description.RenderLocales()

                for key, value in child_locales.items():
                    if key in locales.keys():
                        locales[key] = "\n".join([locales[key], value])
                    else:
                        locales[key] = value     

        return locales

    def RenderHeaders(self):
        headers = super(Container, self).RenderHeaders()

        if isinstance(self.value, list):
            child_headers = "\n".join(filter(None, [x.RenderHeaders() for x in self.value]))

            headers = "\n".join(filter(None, [headers, child_headers]))

        return headers

class Assignment(Description):

    def PrepareResourceData(self):
        return {**self.config}

    def RenderResource(self):
        data = {**self.config}

        return resource_assignment.Render(self.PrepareResourceData())

class Root(Container):

    def PrepareResourceData(self):
        data = super(Root, self).PrepareResourceData()

        data["key"] = "CONTAINER"

        return data

    def RenderLocales(self):
        locales = super(Root, self).RenderLocales()

        for key, value in self.locales.items():
            data = {
                "id": self.id,
                "value": locales[key] if key in locales.keys() else ""
            }

            locales[key] = locales_container.Render(data)

        return locales

    def RenderHeaders(self):
        headers = super(Root, self).RenderHeaders() 

        data = {
            "value": headers
        }

        return headers_container.Render(data)

strength = Container({
    "id": "STRENGTH",
    "key": "REAL",
    "value": [
        Assignment({
            "key": "MIN",
            "value": 0.0
        }),
        Assignment({
            "key": "MAX",
            "value": 100.0
        }),
        Assignment({
            "key": "MINSLIDER",
            "value": 0.0
        }),
        Assignment({
            "key": "MAXSLIDER",
            "value": 100.0
        }),
        Assignment({
            "key": "STEP",
            "value": 1.0
        }),
        Assignment({
            "key": "UNIT",
            "value": "PERCENT"
        }),
        Assignment({
            "key": "CUSTOMGUI",
            "value": "REALSLIDER"
        })
    ]
})

up_vector_xplus = Assignment({
    "id": "UP_VECTOR_XPLUS",
    "key": "UP_VECTOR_XPLUS",
    "locales": {
        "strings_us": "X+"
    }
})

up_vector_xminus = Assignment({
    "id": "UP_VECTOR_XMINUS",
    "key": "UP_VECTOR_XMINUS",
    "locales": {
        "strings_us": "X-"
    }
})

up_vector = Container({
    "id": "UP_VECTOR",
    "key": "LONG",
    "value": [
        Assignment({
            "key": "ANIM",
            "value": "OFF"
        }),
        Container({
            "key": "CYCLE",
            "value": [
                up_vector_xplus,
                up_vector_xminus
            ]
        })
    ],
    "locales": {
        "strings_us": "Up Vector"
    }
})

base_settings = Container({
    "id": "GROUP_BASE_SETTINGS",
    "key": "GROUP",
    "value": [
        Assignment({
            "key": "DEFAULT",
            "value": 1
        }),
        up_vector
    ],
    "locales": {
        "strings_us": "Base Settings"
    }
})

root = Root({
    "id": "Tmyawesomeplugin",
    "value": [
        Assignment({
            "key": "NAME",
            "value": "Tmyawesomeplugin"
        }),
        Assignment({
            "key": "INCLUDE",
            "value": "Tbase"
        }),
        Assignment({
            "key": "INCLUDE",
            "value": "Texpression"
        }),
        base_settings
    ],
    "locales": {
        "strings_us": "My awesome plugin"
    }
})

print(root.RenderResource())
print(root.RenderLocales()["strings_us"])
print(root.RenderHeaders())