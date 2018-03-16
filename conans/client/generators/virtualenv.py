import os
from conans.model import Generator
from conans.tools import os_info


class VirtualEnvGenerator(Generator):

    append_with_spaces = ["CPPFLAGS", "CFLAGS", "CXXFLAGS", "LIBS", "LDFLAGS", "CL"]

    def __init__(self, conanfile):
        self.conanfile = conanfile
        self.env = conanfile.env
        self.venv_name = "conanenv"
        super(VirtualEnvGenerator, self).__init__(conanfile)

    @property
    def filename(self):
        return

    def _variable_placeholder(self, name, flavor):
        ''' Returns a placeholder for the variable name formatted for a certain
        shell. (e.g., cmd, ps1, sh).
        '''
        if flavor == "cmd":
            return "%%%s%%" % name
        if flavor == "ps1":
            return "$env:%s" % name
        # flavor == sh
        return "$%s" % name

    def _activate_values(self, variables, flavor):
        '''
        '''
        pathsep,quoteElements,quoteFullValue,enableSpacePathsep = ":",True,False,True
        if flavor in ["cmd", "ps1"]:
            pathsep,quoteElements,enableSpacePathsep = ";",False,False
        if flavor in ["ps1"]:
            quoteFullValue = True

        ret = []
        for name, value in variables:
            if isinstance(value, list):
                placeholder = self._variable_placeholder(name, flavor)
                if enableSpacePathsep and name in self.append_with_spaces:
                    # Variables joined with spaces look like: CPPFLAGS="one two three"
                    value = " ".join(value+[placeholder])
                    value = "\"%s\"" % value if value else ""
                else:
                    # Quoted variables joined with pathset may look like: PATH="one path":"two paths"
                    # Unquoted variables joined with pathset may look like: PATH=one path;two paths
                    value = ["\"%s\"" % v for v in value] if quoteElements else value
                    value = pathsep.join(value+[placeholder])
            else:
                # single value
                value = "\"%s\"" % value if quoteElements else value
            value = "\"%s\"" % value if quoteFullValue else value
            ret.append( (name, value) )
        return ret

    def _deactivate_values(self, variables, flavor, env=None):
        '''
        '''
        env = env or os.environ
        quoteFullValue = flavor not in ["cmd"]
        ret = []
        for name, _ in variables:
            value = env.get( name, "" )
            value = "\"%s\"" % value if quoteFullValue else value
            ret.append( (name, value) )
        return ret

    def _sh_lines(self):
        variables = [("OLD_PS1", "$PS1")]
        variables.append(("PS1", "(%s) $PS1" % self.venv_name))
        variables.extend(self.env.items())
        activate_values   = self._activate_values(variables, "sh")
        deactivate_values = self._deactivate_values(variables, "sh")

        activate_lines = []
        for name, value in activate_values:
            activate_lines.append("%s=%s" % (name,value))
            activate_lines.append("export %s" % name)
        activate_lines.append('')

        deactivate_lines = []
        for name, value in deactivate_values:
            deactivate_lines.append("%s=%s" % (name,value))
            deactivate_lines.append("export %s" % name)
        deactivate_lines.append('')
        return activate_lines, deactivate_lines

    def _cmd_lines(self):
        variables = [("PROMPT", "(%s) %%PROMPT%%" % self.venv_name)]
        variables.extend(self.env.items())
        activate_values   = self._activate_values(variables, "cmd")
        deactivate_values = self._deactivate_values(variables, "cmd")

        activate_lines = ["@echo off"]
        for name, value in activate_values:
            activate_lines.append("SET %s=%s" % (name,value))
        activate_lines.append('')

        deactivate_lines = ["@echo off"]
        for name, value in deactivate_values:
            deactivate_lines.append("SET %s=%s" % (name,value))
        deactivate_lines.append('')
        return activate_lines, deactivate_lines

    def _ps1_lines(self):
        variables = self.env.items()
        activate_values   = self._activate_values(variables, "ps1")
        deactivate_values = self._deactivate_values(variables, "ps1")

        activate_lines = ['function global:_old_conan_prompt {""}']
        activate_lines.append('$function:_old_conan_prompt = $function:prompt')
        activate_lines.append('function global:prompt { write-host "(%s) " -nonewline; & $function:_old_conan_prompt }' % self.venv_name)
        for name, value in activate_values:
            activate_lines.append('$env:%s = %s' % (name,value))
        activate_lines.append('')

        deactivate_lines = ['$function:prompt = $function:_old_conan_prompt']
        deactivate_lines.append('remove-item function:_old_conan_prompt')
        for name, value in deactivate_values:
            deactivate_lines.append('$env:%s = %s' % (name,value))
        deactivate_lines.append('')
        return activate_lines, deactivate_lines

    @property
    def content(self):
        result = {}
        if os_info.is_windows:
            activate, deactivate = self._cmd_lines()
            result["activate.bat"] = os.linesep.join(activate)
            result["deactivate.bat"] = os.linesep.join(deactivate)

            activate, deactivate = self._ps1_lines()
            result["activate.ps1"] = os.linesep.join(activate)
            result["deactivate.ps1"] = os.linesep.join(deactivate)
        else:
            activate, deactivate = self._sh_lines()
            result["activate.sh"] = os.linesep.join(activate)
            result["deactivate.sh"] = os.linesep.join(deactivate)

        return result
