import sys, os, json
import crun

#### LOG #####
def error(msg):
    sys.stderr.write("\033[91;1merror\033[0m \033[90mC roblox-c:\033[0m " + msg + "\n")
    sys.exit(1)
def warn(msg):
    sys.stderr.write("\033[1;33m" + "warning: " + "\033[0m" + "\033[90mC roblox-c:\033[0m " + msg + "\n")
def info(msg):
    sys.stderr.write("\033[1;32m" + "info: " + "\033[0m" + "\033[90mC roblox-c:\033[0m " + msg  + "\n")
    
    
#### CONSTANTS ####
CONFIG_FILE = os.path.expanduser('~/.config/rbxc/config.json')
VERSION = "1.0.0"
TAB = "\t\b\b\b\b"

#### DEPENDENCIES ####
try:
    import clang.cindex as clang
    from clang.cindex import Config
except ImportError:
    error("libclang could not be resolved")
    
#### COMPILER PARSER ####
bins = {
    "!": "not ",
    "||": " or ",
    "&&": " and ",
    "==": "==",
    "!=": "~=",
    "<": "<",
    ">": ">",
    "<=": "<=",
    ">=": ">=",
    "**":"^",
    "]": " + 1] ",
    "<<": "/C.bitlshift()*",
    ">>": "/C.bitrshift()*",
    "|": "/C.bor()*",
    "&": "/C.band()*",
    "^": "/C.bxor()*",
}
uns = {
    "++": {
        "v":" += 1",
        "wrap": False,
    },
    "**": {
        "v":"^",
        "wrap": False,
    },
    "--": {
        "v":" -= 1",
        "wrap": False,
    },
    "&": {
        "v":"C.ptr(",
        "wrap": True,
    },
    "*": {
        "v":"C.deref(",
        "wrap": True,
    },
    "!": {
        "v":"not ",
        "wrap": False,
    },
    "sizeof": {
        "v":"C.sizeof(",
        "wrap": True,
    },
    "sizeof...": {
        "v":"C.sizeof(",
        "wrap": True,
    },
    "alignof": {
        "v":"C.alignof(",
        "wrap": True,
    },
    "__real": {
        "v":"C.__real(",
        "wrap": True,
    },
    "__imag": {
        "v":"C.__imag(",
        "wrap": True,
    }
}
def get_ast(file_path, c, check=True, flags=[]):
    if check:
        test(file_path, c, flags)
    try:
        index = clang.Index.create()
        if c:
            std = "c99"
        else:
            std = "c++11"
        translation_unit = index.parse(file_path, args=['-std='+std])
        return translation_unit.cursor
    except clang.LibclangError as e:
        error("libclang error: " + str(e))
        sys.exit(1)
    except Exception as e:
        error(str(e))
        sys.exit(1)
def print_ast(node, depth=0):
    print('  ' * depth + str(node.kind) + ' : ' + node.spelling)
    for child in node.get_children():
        print_ast(child, depth + 1)
def test(file_path, c, flags):
    # Runs gcc on the file to check for errors, if there is an error sys.exit(1)
    if c:
        iserrors = os.system("gcc -fsyntax-only -DRBXCHECK=1 " + " ".join(flags) + " " + file_path)
    else:
        iserrors = os.system("g++ -fsyntax-only -DRBXCHECK=1 " + " ".join(flags) + " " + file_path)
    if iserrors != 0:
        sys.exit(1)

#### GENERATOR ####
class NodeVisitor(object):
    def __init__(self, isC):
        self.indent = 0
        self.code = ""
        if isC:
            self.lang = "C"
        else:
            self.lang = "C++"
            self.namespaces = {}

    ### VISITORS ###
    def visit_translation_unit(self, node):
        for child in node.get_children():
            self.visit(child)
    def visit_do_stmt(self, node):
        self.pushline("repeat")
        for child in node.get_children():
            if child.kind.name.lower() == "compound_stmt":
                self.visit(child)
        self.pushline("until ")
        for child in node.get_children():
            if child.kind.name.lower() != "compound_stmt":
                self.visit(child)
        self.newline()
    def visit_function_decl(self, node):
        if node.spelling != "main":
            self.pushline("function " + node.spelling)
            self.pushexp("(")
            for i, child in enumerate(node.get_children()):
                if child.kind.name.lower() == "parm_decl":
                    self.visit(child)
                    if i < len(list(node.get_children()))-2:
                        self.pushexp(", ")
            self.pushexp(")")
            for child in node.get_children():
                if child.kind.name.lower() != "parm_decl":
                    self.visit(child)
        else:
            self.pushline("do")
            for child in node.get_children():
                if child.kind.name.lower() != "compound_stmt":
                    error("main function must only have a compound statement")
                self.visit(child)
        self.pushline("end")
        
        return node.spelling
    def visit_parm_decl(self, node):
        self.pushexp(node.spelling)
    def visit_compound_stmt(self, node):
        self.indent += 1
        i = 0
        self.newline()
        for child in (node.get_children()):
            self.visit(child)
            i+=1
        if i == 0:
            self.lastline()
        self.indent -= 1
    def visit_call_expr(self, node):
        self.pushexp(node.spelling)
        self.pushexp("(")
        for i, child in enumerate(node.get_children()):
            if i == 0:
                continue
            self.visit(child)
            if i < len(list(node.get_children()))-1:
                self.pushexp(", ")
        self.pushexp(")")
    ### C++ & C: DIFFERENT IMPLEMENATIONS ###
    def visit_unexposed_expr(self, node):
        mode = 0
        for child in node.get_children():
            if child.kind.name.lower() == "decl_ref_expr":
                mode = 1
        if self.lang == "C++" and node.spelling == "" and mode == 1:
            try:
                name = list(list(node.get_children())[0].get_children())[0].spelling
            except:
                name = list(node.get_children())[0].spelling
            self.pushexp(name)
            self.pushexp("(")
            for i, child in enumerate(node.get_children()):
                if i == 0:
                    continue
                self.visit(child)
                
                if i < len(list(node.get_children()))-1:
                    self.pushexp(", ")
            self.pushexp(")")
        else:
            for child in node.get_children():
                self.visit(child)
    ### C++ ONLY ###
    def visit_class_decl(self, node):
        self.pushline("local " + node.spelling + " = {")
        self.indent += 1
        base = None
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "cxx_base_specifier":
                base = child.spelling
            else:
                self.visit(child)
                if child.spelling != "":
                    self.pushexp(",")
        self.indent -= 1
        self.pushline("}")
        if base:
            self.pushline("for i, v in (" + base + ") do")
            self.pushline("\t" + node.spelling + "[i] = v")
            self.pushline("end")
            
        return node.spelling
    def visit_cxx_access_spec_decl(self, node):
        pass
    def visit_constructor(self, node):
        self.pushline("[C.construct] = function")
        self.pushexp("(")
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "parm_decl":
                self.visit(child)
                if i < len(list(node.get_children()))-2:
                    self.pushexp(", ")
        self.pushexp(")")
        for child in node.get_children():
            if child.kind.name.lower() != "parm_decl":
                self.visit(child)
        self.pushline("end")
    def visit_cxx_new_expr(self, node):
        self.pushexp("C.new(")
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "call_expr":
                self.pushexp(child.spelling)
                for i, childchild in enumerate(child.get_children()):
                    if i != len(list(child.get_children())):
                        self.pushexp(", ")
                    self.visit(childchild)
        self.pushexp(")")
    def visit_namespace(self, node):
        self.pushline("local function namespace_"+node.spelling+"()")
        self.indent += 1
        defs = []
        for i, child in enumerate(node.get_children()):
            defs.append(self.visit(child))
        self.pushline("return {")
        self.indent += 1
        for ndef in defs:
            if type(ndef) == str:
                self.pushline("[" + ndef + "] = " + ndef + ",")
        self.indent -= 1
        self.pushline("}")
        self.indent -= 1
        self.pushline("end")
        self.namespaces[node.spelling] = defs
    def visit_using_directive(self, node):
        for child in node.get_children():
            self.pushline("local " + child.spelling + " = namespace_" + child.spelling + "()")
            for ndef in self.namespaces[child.spelling]:
                self.pushline("local " + ndef + " = " + child.spelling + "[\"" + ndef + "\"]")
    def visit_cxx_method(self, node):
        self.pushline(node.spelling + " = function")
        self.pushexp("(")
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "parm_decl" and not child.kind.name.lower() == "cxx_base_specifier":
                self.visit(child)
                if i < len(list(node.get_children()))-2:
                    self.pushexp(", ")
        self.pushexp(")")
        for child in node.get_children():
            if child.kind.name.lower() != "parm_decl":
                self.visit(child)
        self.pushline("end")
    def visit_cxx_base_specifier(self, node):
        self.pushline("[" + node.spelling + "] = " + node.spelling + ",")
    def visit_cxx_delete_expr(self, node):
        self.pushline("C.delete(")
        deletes = []
        for i, child in enumerate(node.get_children()):
            self.visit(child)
            deletes.append(child.spelling)
            if i < len(list(node.get_children()))-1:
                self.pushexp(", ")
        self.pushexp(")")
        for delete in deletes:
            line = delete + " = nil"
            self.pushline(line)
    def visit_destructor(self, node):
        self.pushline("[C.destruct] = function")
        self.pushexp("(")
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "parm_decl":
                self.visit(child)
                if i < len(list(node.get_children()))-2:
                    self.pushexp(", ")
        self.pushexp(")")
        for child in node.get_children():
            if child.kind.name.lower() != "parm_decl":
                self.visit(child)
        self.pushline("end")
    ### ALL ###
    def visit_decl_ref_expr(self, node):
        self.pushexp(node.spelling)
    def visit_decl_stmt(self, node):
        for child in node.get_children():
            self.visit(child)
    def visit_var_decl(self, node):
        equal = ""
        if len(list(node.get_children())) > 0:
            equal = " = "
        self.pushline("local " + node.spelling + equal)
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "integer_literal" and len(list(node.get_children())) < i and list(node.get_children())[i+1].kind.name.lower() == "init_list_expr":
                continue
            self.visit(child)
        if equal == "":
            self.newline()
        return node.spelling    
    def visit_cstyle_cast_expr(self, node):
        line = "C.cast(\"{}\", "
        self.pushexp(line.format(node.type.spelling))
        for child in node.get_children():
            self.visit(child)
        self.pushexp(")")
    def visit_integer_literal(self, node):
        tokens = list(node.get_tokens())
        for i, token in enumerate(tokens):
            self.pushexp(token.spelling)
    def visit_binary_operator(self, node):
        tokens = list(node.get_tokens())
        for i, token in enumerate(tokens):
            if token.spelling in bins:
                spell = bins[token.spelling]
            else:
                spell = token.spelling
            self.pushexp(spell)
        self.pushexp(" ")
    def visit_asm_label_attr(self, node):
        error("to add asm support to roblox-c run `rcc install rasm`")
        pass
    def visit_asm_stmt(self, node):
        error("to add asm support to roblox-c run `rcc install rasm`")
        pass
    
    def visit_while_stmt(self, node):
        self.pushline("while ")
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "compound_stmt":
                continue
            self.visit(child)
        self.pushexp(" do")
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "compound_stmt":
                self.visit(child)
        self.pushline("end")
        self.newline()
    def visit_goto_stmt(self, node):
        warn("goto requires Lua 5.2+, not Luau")
        for child in node.get_children():
            self.pushline("goto " + child.spelling)
        pass
    def visit_label_stmt(self, node):
        warn("labels requires Lua 5.2+, not Luau")
        self.pushline("::" + node.spelling + "::")
    def visit_init_list_expr(self, node):
        self.pushexp("{")
        for i, child in enumerate(node.get_children()):
            self.visit(child)
            if i < len(list(node.get_children()))-1:
                self.pushexp(", ")
        self.pushexp("}")
    def visit_array_subscript_expr(self, node):
        pass
    def visit_floating_literal(self, node):
        tokens = list(node.get_tokens())
        for i, token in enumerate(tokens):
            self.pushexp(token.spelling)
    def visit_return_stmt(self, node):
        self.pushline("return ")
        for child in node.get_children():
            self.visit(child)
        self.newline()
    def visit_if_stmt(self, node):
        self.pushline("if ")
        for i, child in enumerate(node.get_children()):
            
            if child.kind.name.lower() == "compound_stmt" or child.kind.name.lower() == "if_stmt":
                continue
            
            self.visit(child)
        self.pushexp(" then")
        ic = 0
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "compound_stmt":
                if ic != 0:
                    self.pushline("else")
                ic += 1
                self.visit(child)
            elif child.kind.name.lower() == "if_stmt":
                self.pushline("else")
                self.indent += 1
                self.visit(child)
                self.indent -= 1
                self.newline()
                
        self.pushline("end")
        self.newline()
    def visit_switch_stmt(self, node):
        self.pushline("C.switch(")
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "compound_stmt":
                continue
            self.visit(child)
        self.pushexp(", {")
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "compound_stmt":
                self.visit(child)
        self.pushline("})")
        self.newline()
    def visit_case_stmt(self, node):
        case_value = list(node.get_children())[0]
        self.pushline("[")
        self.visit(case_value)
        self.pushexp("] = function()")
        self.indent += 1
        for i, child in enumerate(node.get_children()):
            if i == 0:
                continue
            if child.kind.name.lower() == "break_stmt":
                self.pushline("return C.brk")
            else:
                self.visit(child)
        self.indent -= 1
        self.pushline("end,")
    def visit_default_stmt(self, node):
        self.pushline("[C.def] = function()")
        self.indent += 1
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "break_stmt":
                self.pushline("return C.brk")
            else:
                self.visit(child)
        self.indent -= 1
        self.pushline("end,")
        
    def visit_compound_assign_operator(self, node):
        tokens = list(node.get_tokens())
        self.pushexp("(")
        for i, token in enumerate(tokens):
            self.pushexp(token.spelling)
        self.pushexp(")")
    def visit_for_stmt(self, node):
        content = list(node.get_children())[3]
        decl = list(node.get_children())[0]
        on = list(node.get_children())[2]
        toggle = list(node.get_children())[1]
        self.visit(decl)
        self.pushline("while ")
        self.visit(toggle)
        self.pushexp(" do")
        self.newline()
        self.pushexp("\t")
        self.visit(on)
        self.visit(content)
        self.pushline("end")
        self.newline()
    def visit_break_stmt(self, node):
        self.pushline("break")
    def visit_continue_stmt(self, node):
        self.pushline("continue")
    def visit_typedef_decl(self, node):
        pass
    def visit_union_decl(self, node):
        tokens = list(node.get_tokens())
        if "unnamed" not in node.spelling:
            self.pushline("local " + tokens[1].spelling + " =")
        else:
            self.pushline("local _UNNAMED =")
            
        self.pushline("{")
        self.indent += 1
        for child in node.get_children():
            self.visit(child)
            self.pushexp(",")
        self.indent -= 1
        self.pushline("}")
    def visit_field_decl(self, node):
        if len(list(node.get_children())) > 0:
            self.pushline(node.spelling + " = ")
            for child in (node.get_children()):
                self.visit(child)
            self.newline()
        else:
            self.pushline(node.spelling + " = nil")
    def visit_struct_decl(self, node):
        tokens = list(node.get_tokens())
        if "unnamed" not in node.spelling:
            self.pushline("local " + tokens[1].spelling + " =")
        else:
            self.pushline("local _UNNAMED =")
        self.pushline("{")
        self.indent += 1
        for child in node.get_children():
            self.visit(child)
            self.pushexp(",")
        self.indent -= 1
        self.pushline("}")
    def visit_type_ref(self, node):
        pass
    def visit_enum_decl(self, node):
        tokens = list(node.get_tokens())
        for child in node.get_children():
            self.pushline("local " + child.spelling + " = " + str(child.enum_value) + " -- enum: " + tokens[1].spelling)
        self.newline()
    def visit_string_literal(self, node):
        self.pushexp(node.spelling)
    def visit_paren_expr(self, node):
        self.pushexp("(")
        for child in node.get_children():
            self.visit(child)
        self.pushexp(")")
    def visit_unary_operator(self, node):
        tokens = list(node.get_tokens())
        #self.pushexp("(")
        wrapnext = False
        for i, token in enumerate(tokens):
            spell = token.spelling
            
            if spell in uns:
                wrapnext = uns[spell]["wrap"]
                spell = uns[spell]["v"]
            elif wrapnext:
                spell += ")"
                wrapnext = False
            self.pushexp(spell)
        self.pushexp(" ")
        #self.pushexp(")")
    def visit_unexposed_attr(self, node):
        pass
    def visit_unexposed_decl(self, node):
        pass
    
        
    
    
    ### NODESYSTEM ###
    def visit(self, node):
        method = 'visit_' + node.kind.name.lower()
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)
    def generic_visit(self, node):
        error(f"{node.kind.name.lower()} not implemented")
    def pushline(self, code):
        self.code += "\n"+("\t"*self.indent)+code
    def pushexp(self, code):
        self.code += code
    def newline(self):
        self.code += "\n"+("\t"*self.indent)
    def lastline(self):
        self.code = "\n".join(self.code.split("\n")[0:-1])
    def clean(self):
        lines = self.code.split("\n")
        for i in reversed(range(len(lines))):
            if lines[i].isspace():
                del lines[i]
        self.code = "\n".join(lines)      

#### HEADER ####
REQUIRE = "local C = require(game.ReplicatedStorage:WaitForChild(\"Packages\").cruntime)\n\n"
HEADER = "--// Generated by roblox-c v" + VERSION + " \\\\--\n--Note: This code will not be very clean.\n\n"+REQUIRE
LIBS = ["malloc", "free", "realloc", "calloc", "memset", "memcpy", "memmove", "memcmp", "memchr", "printf"]

def gen(code):
    header = ""
    for lib in LIBS:
        if lib in code:
            header += lib+" = C."+lib+"\n"
    return header
#### INTERFACE #### 
def check():
    if not os.path.exists(os.path.expanduser('~/.config/rbxc')):
        os.makedirs(os.path.expanduser('~/.config/rbxc'))
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({}, f)
def config(key, value):
    check()
    # Load existing config file or create a new one if it doesn't exist
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
    else:
        config_data = {}

    # Update the config with the new key-value pair
    config_data[key] = value

    # Save the updated config to disk
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f)
def isconfig(key):
    check()
    # Load the config file
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
    else:
        config_data = {}

    # Return the value of the specified key, or None if it doesn't exist
    return config_data.get(key)  

def usage():
    print("\n"+f"""usage: \033[1;94mrbxc\033[0m [file] [options] -o [gen]
\033[1mOptions:\033[0m
{TAB}\033[1m-v\033[0m        show version information
{TAB}\033[1m-c\033[0m        debug mode
{TAB}\033[1m-s\033[0m        generate cruntime
{TAB}\033[1m-o\033[0m        output file
{TAB}\033[1m-vd\033[0m       show version number only
{TAB}\033[1m-p\033[0m        set libclang path
{TAB}\033[1m-u\033[0m        open this
{TAB}\033[1;31m-h\033[0m\033[31m        hardcore mode\033[0m""")
    sys.exit()
def version():
    print("\033[1;34m" + "copyright:" + "\033[0m" + " roblox-py " + "\033[1m" + VERSION + "\033[0m" + " licensed under the MIT License by " + "\033[1m" + "@AsynchronousAI" + "\033[0m")
    sys.exit(0)
def main():
    # read args
    args = sys.argv[1:]
    flags = []
    inputf = None
    outputf = None
    check = True

    lookForOutput = False
    skip = False
    hardcore = False
    
    if isconfig("lclang"):
        Config.set_library_file(isconfig("lclang"))
        
    flags = []
    
    for i, arg in enumerate(args):
        if arg.startswith("-W"):
            flags.append(arg)
        elif arg == "-o":
            lookForOutput = True
        elif arg == "-c":
            check = False
        elif arg == "-h":
            hardcore = True
        elif arg == "-p":
            try:
                Config.set_library_file(args[i+1])
                config("lclang", args[i+1])
                skip = True
            except:
                config("lclang", None)
                error("no path specified")
                sys.exit(1)
        elif arg == "-v":
            version()
        elif arg == "-vd":
            print(VERSION)
            sys.exit(0)
        elif arg == "-u":
            usage()
        elif arg.startswith("-"):
            flags.append(arg)
        elif (inputf is None) and "-s" not in args:
            inputf = arg
        elif lookForOutput:
            outputf = arg
            lookForOutput = False
        elif skip:
            skip = False
        else:
            error("too many arguments")
            sys.exit(1)
    
    if (inputf is None) and "-s" not in args:
        usage()
        sys.exit(1)
    
    if outputf is None:
        error("no output file specified")
        sys.exit(1)
        
    if "-s" in args:
        print(crun.cruntime)
        sys.exit(0)
    
    isC = None
    if inputf.endswith(".c"):
        isC = True
    elif inputf.endswith(".cpp") or inputf.endswith(".cxx") or inputf.endswith(".cc") or inputf.endswith(".C"):
        isC = False
    else:
        error("file must end with '.c', '.cpp', '.cxx', '.cc', or '.C'")
        sys.exit(1)
        
    parsed = get_ast(inputf, isC, check, flags)
    if not check:
        print_ast(parsed)
    Engine = NodeVisitor(isC)
    Engine.visit(parsed)
    Engine.clean()
    with open(outputf, "w") as f:
        code = (HEADER + gen(Engine.code) + Engine.code)
        if hardcore:
            code = "xpcall(function() -- hardcore mode\n" + code + "\nend, function(err) -- hardcore mode\n\terror('Segmenation fault: 11') -- hardcore mode\nend) -- hardcore mode"
            
        f.write(code)
    
if __name__ == "__main__":
    main()