import sys, os, json

#### LOG #####
def error(msg):
    print("\033[91;1merror\033[0m \033[90mC roblox-c:\033[0m " + msg)
    sys.exit(1)
def warn(msg):
    sys.stderr.write("\033[1;33m" + "warning: " + "\033[0m" + "\033[90mC roblox-c:\033[0m " + msg)
def info(msg):
    sys.stderr.write("\033[1;32m" + "info: " + "\033[0m" + "\033[90mC roblox-c:\033[0m " + msg)
    
    
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
def get_ast(file_path, c, check=True):
    if check:
        test(file_path, c)
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
def print_ast(node, depth=0):
    print('  ' * depth + str(node.kind) + ' : ' + node.spelling)
    for child in node.get_children():
        print_ast(child, depth + 1)
def test(file_path, c):
    # Runs gcc on the file to check for errors, if there is an error sys.exit(1)
    if c:
        iserrors = os.system("gcc -fsyntax-only " + file_path)
    else:
        iserrors = os.system("g++ -fsyntax-only " + file_path)
    if iserrors != 0:
        sys.exit(1)

#### GENERATOR ####
class NodeVisitor(object):
    def __init__(self):
        self.indent = 0
        self.code = ""

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
                self.visit(child)
        self.pushline("end")
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
    def visit_unexposed_expr(self, node):
        for child in node.get_children():
            self.visit(child)
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
        for child in node.get_children():
            self.visit(child)
        if equal == "":
            self.newline()
    def visit_integer_literal(self, node):
        tokens = list(node.get_tokens())
        for i, token in enumerate(tokens):
            self.pushexp(token.spelling)
    def visit_binary_operator(self, node):
        tokens = list(node.get_tokens())
        self.pushexp("(")
        for i, token in enumerate(tokens):
            self.pushexp(token.spelling)
        self.pushexp(")")
    def visit_asm_label_attr(self, node):
        error("assembly cannot be embedded in roblox-c")
        pass
    def visit_return_stmt(self, node):
        self.pushline("return ")
        for child in node.get_children():
            self.visit(child)
        self.newline()
    def visit_if_stmt(self, node):
        self.pushline("if ")
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "compound_stmt":
                continue
            
            self.visit(child)
        self.pushexp(" then")
        for i, child in enumerate(node.get_children()):
            if child.kind.name.lower() == "compound_stmt":
                self.visit(child)
        self.pushline("end")
    def visit_compound_assign_operator(self, node):
        tokens = list(node.get_tokens())
        self.pushexp("(")
        for i, token in enumerate(tokens):
            self.pushexp(token.spelling)
        self.pushexp(")")
    def visit_typedef_decl(self, node):
        pass
    def visit_union_decl(self, node):
        tokens = list(node.get_tokens())
        self.pushline("local " + tokens[1].spelling + " =")
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
        self.pushline("local " + tokens[1].spelling + " =")
        self.pushline("{")
        self.indent += 1
        for child in node.get_children():
            self.visit(child)
            self.pushexp(",")
        self.indent -= 1
        self.pushline("}")
    def visit_type_ref(self, node):
        self.pushexp(node.spelling)
    def visit_enum_decl(self, node):
        tokens = list(node.get_tokens())
        self.pushline("local " + tokens[1].spelling + " = \"enum\"")
        for child in node.get_children():
            self.visit(child)
        self.newline()
    def visit_enum_constant_decl(self, node):
        self.pushline(node.spelling + " = " + str(node.enum_value))
        for child in node.get_children():
            self.visit(child)
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
        for i, token in enumerate(tokens):
            spell = token.spelling
            if token.spelling == "++":
                spell = " += 1"
            elif token.spelling == "--":
                spell = " -= 1"
                
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
        
#### HEADER ####
HEADER = "--// Generated by roblox-c v" + VERSION + " \\\\--\n--Note: This code will not be very clean."
    
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
{TAB}\033[1m-vd\033[0m       show version number only
{TAB}\033[1m-p\033[0m        set libclang path
{TAB}\033[1m-u\033[0m        open this""")
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
    
    
    if isconfig("lclang"):
        Config.set_library_file(isconfig("lclang"))
        
    for i, arg in enumerate(args):
        if arg == "-o":
            lookForOutput = True
        elif arg == "-c":
            check = False
        elif arg == "-p":
            if len(args) > 1:
                Config.set_library_file(args[i+1])
                config("lclang", args[i+1])
                skip = True
            else:
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
        elif inputf is None:
            inputf = arg
        elif lookForOutput:
            outputf = arg
            lookForOutput = False
        elif skip:
            skip = False
        else:
            error("too many arguments")
            sys.exit(1)
    
    if inputf is None:
        usage()
        sys.exit(1)
    
    if outputf is None:
        error("no output file specified")
        sys.exit(1)
    
    isC = None
    if inputf.endswith(".c"):
        isC = True
    elif inputf.endswith(".cpp") or inputf.endswith(".cxx") or inputf.endswith(".cc") or inputf.endswith(".C"):
        isC = False
    else:
        error("file must end with '.c', '.cpp', '.cxx', '.cc', or '.C'")
        sys.exit(1)
        
    parsed = get_ast(inputf, isC, check)
    print_ast(parsed)
    Engine = NodeVisitor()
    Engine.visit(parsed)
    with open(outputf, "w") as f:
        f.write(HEADER + Engine.code)
    
if __name__ == "__main__":
    main()