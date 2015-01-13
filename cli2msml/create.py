# Copyright (C) 2014 Alexander Weigl
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
from __future__ import print_function

"""Transfers CLI executables into an MSML-usable form.


"""

__author__ = 'Alexander Weigl <uiduw@student.kit.edu>'
__date__ = "2014-12-05"
__version__ = "0.2"

from .log import *

import subprocess
import os
import os.path
import jinja2
from path import path

from lxml import etree

do = debug

# Configuration Object
config = {
    'FILE_EXTENSIONS_TO_SORTS': {},
    'FLAGS_TYPES': {},
    'SLOT_NAME_FLAG': {},
    'DEFAULT_OVERRIDES': {}
}


def set_config(cfg):
    global config
    if cfg:
        config = cfg


# region parameter conversion
class chainproperty(object):
    def __init__(self, name):
        self._name = name

    def __get__(self, instance, owner=None):
        if hasattr(instance, "other"):
            val =  getattr(getattr(instance, "other"), self._name, None)
            if val is not None:
                return val
        try:
            return instance[self._name]
        except KeyError:
            raise AttributeError()

    def __set__(self, instance, value):
        instance[self._name] = value


class MsmlArgument(dict):
    def __init__(self,iterable=None,**kwargs):
        if iterable:
            super(MsmlArgument, self).__init__(iterable)
        else:
            super(MsmlArgument, self).__init__(**kwargs)


        #self["doc"] = ""
        self.tag = None
        self.longflag = None
        self.flag = None


    name = chainproperty("name")
    physical = chainproperty("physical")
    logical = chainproperty("logical")
    default = chainproperty("default")
    doc = chainproperty("doc")
    target = chainproperty("target")
    channel = chainproperty("channel")


    @property
    def cli_flag(self):
        if self.tag in config['FLAGS_TYPES']:
            return "{{%s|flag('%s')}}" % (self.name, self.longflag or self.flag)
        else:
            return "{{%s|option('%s')}}" % (self.name, self.longflag or self.flag)


    def copy(self):
        arg =  MsmlArgument(self)
        arg.longflag = self.longflag
        arg.flag = self.flag
        arg.tag = self.tag
        return arg


def gather_enum_values(parent):
    l = []
    for element in parent.getiterator('element'):
        l.append(element.text)
    return l


def file_suffixes(parent):
    p = parent.get('fileExtensions', "")

    if p in config['FILE_EXTENSIONS_TO_SORTS']:
        return config['FILE_EXTENSIONS_TO_SORTS'][p]
    elif p.find(','):
        info("No translation for file extensions '%s' to sort\n"
             "You should consider to add something in FILE_EXTENSIONS_TO_SORTS", p)

    return map(lambda x: x.strip(".*").upper(), p.split(","))


def default_arg(obj, physical=None, logical=None, enum=False):
    arg = MsmlArgument(physical=physical, logical=logical)
    arg.name = obj.findtext('name')

    arg.longflag = obj.findtext('longflag')
    arg.flag = obj.findtext('flag')

    arg.tag = obj.tag

    arg.logical = ""
    default = obj.findtext("_default")

    if default:
        arg.default = default.replace('"', '').replace("'", '')

    arg.index = obj.findtext('index')

    arg.doc = "%s\n\n%s" % (obj.findtext('label'), obj.findtext('description'))

    if enum:
        values = gather_enum_values(obj)
        arg.doc += "\n:Possible Values: %s" % values

    arg.channel = obj.findtext('channel')


    arg.other = config['DEFAULT_OVERRIDES'].get(arg.name)

    return arg


_label = lambda x: None
_description = lambda x: None


def _integer_enumeration(integer_enumeration):
    return default_arg(integer_enumeration, 'vector.int', enum=True)


def _integer_vector(integer_vector):
    return default_arg(integer_vector, 'vector.int', )


def _directory(directory):
    arg = default_arg(directory, 'str')
    arg.doc += "\n:Note: Should be a directory"
    return arg


def _double(double):
    return default_arg(double, 'float')


def _double_enumeration(enum):
    return default_arg(enum, 'float', enum=True)


def _double_vector(vec):
    return default_arg(vec, 'vector.float')


def _file(fil):
    arg = default_arg(fil, 'InFile')
    sfx = file_suffixes(fil)
    arg.physical = sfx
    return arg


def _float(floot):
    return default_arg(floot, 'float', enum=True)


def _float_enumeration(enum):
    return default_arg(enum, 'float')


def _float_vector(vec):
    return default_arg(vec, 'vector.float')


def _geometry(geometry):
    return default_arg(geometry)


def _image(image):
    arg = default_arg(image, 'Image')
    sfx = file_suffixes(image)
    # arg.physical = ','.join(map(lambda x: 'Image.%s' % x, sfx))
    arg.physical = sfx
    return arg


def _point(point):
    return default_arg(point, 'Point2D')


def _region(region):
    return default_arg(region, 'Region')


def _string(string):
    return default_arg(string, 'str')


def _string_enumeration(enum):
    return default_arg(enum, 'str', enum=True)


def _string_vector(vec):
    return default_arg(vec, 'vector.str')


def _boolean(boolean):
    return default_arg(boolean, 'bool')


def _integer(integer):
    return default_arg(integer, 'int')

# endregion
# region jinja
jinjaenv = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


def indent(string, i):
    return string.strip().replace("\n", " " * i + "\n")


jinjaenv.globals["indent"] = indent

operator_template_msml = jinjaenv.get_template("operator.msml.jinja2")
operator_template_rst = jinjaenv.get_template("operator.rst.jinja2")
operator_template_md = jinjaenv.get_template("operator.md.jinja2")
# endregion

class AbortOperationError(BaseException):
    pass


class CreateCLI(object):
    def __init__(self, cli_exec):
        self._executable = cli_exec
        self.name = path(self._executable).namebase

    def _get_xml(self):
        command = "%s --xml" % self._executable
        sp = subprocess.Popen(command,
                              stderr=subprocess.STDOUT,
                              stdout=subprocess.PIPE,
                              shell=True)
        sp.wait()
        if sp.returncode == 0:
            return sp.stdout.read()
        else:
            error(" '%s' did not work", command)
            raise AbortOperationError()


    def _get_cli_model(self):
        self._xml = self._get_xml()
        do("XML retrieved, create binding")
        try:
            parser = etree.XMLParser(encoding="utf-8",
                                     # TODO XMLSchema_schema=".",
                                     remove_blank_text=True,
                                     remove_comments=True,
                                     remove_pis=True, strip_cdata=True
            )
            b = etree.fromstring(self._xml, parser)
            return b
        except BaseException as e:
            error("Could not parse XML from %s", self._executable)
            print(e)
            print(self._xml)
            raise AbortOperationError()

    def do(self):
        do("Executable %s", self._executable)
        model = self._get_cli_model()

        category = model.findtext('category')
        title = model.findtext('title') or self.name
        description = model.findtext('description')
        license = model.findtext('license') or "unknown"
        contributor = model.findtext('contributor')

        debug("Category is %s", category)
        debug("Title is %s", title)
        debug("Description is %s", description)
        debug("License is %s", license)
        debug("Contributor is %s", contributor)

        self.outputs = list()
        self.parameters = list()
        self.inputs = list()

        defined_slots = []
        for ps in model.iterfind('parameters'):
            for p in ps.iterchildren():
                fn = "_%s" % p.tag.replace("-", '_')
                fn = globals()[fn]
                r = fn(p)
                if r:
                    if r.channel == 'input':
                        ls = self.inputs
                    elif r.channel == 'output':
                        ls = self.outputs
                    else:
                        ls = self.parameters

                    ls.append(r)

        ##
        # duplicate output slots for input names
        for out in self.outputs:
            para = out.copy()
            para.name = "t" + out.name
            para.target = True
            para.other = config['DEFAULT_OVERRIDES'].get(para.name, None)

            para.physical = "str" # hardcore setting of physical string type

            self.parameters.insert(0, para)

        self._values = dict(
            template=self.template,
            name=self.name,
            documentation="",
            executable=self._executable,
            category=category,
            title=title,
            description=description,
            license=license,
            contributor=contributor,
            inputs=self.inputs,
            parameters=self.parameters,
            outputs=self.outputs
        )

    @property
    def template(self):
        sort_by_index = lambda x: sorted(x, lambda a, b: cmp(int(a.index), int(b.index)))
        t = "{name} {para} {out} {inp}"

        def format_args(seq):
            return ' '.join(map(lambda x: x.cli_flag, seq))

        para = format_args(self.parameters)
        # out = format_args(self.outputs)
        inp = format_args(self.inputs)

        return t.format(name=self.name, para=para, out="", inp=inp)

    @property
    def msml(self):
        return operator_template_msml.render(**self._values)

    @property
    def rst(self):
        return operator_template_rst.render(**self._values)

    @property
    def markdown(self):
        return operator_template_md.render(**self._values)

