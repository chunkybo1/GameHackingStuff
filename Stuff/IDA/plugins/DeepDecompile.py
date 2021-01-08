import idaapi

def get_called_functions(fn):
    called_fns = []
    for item in FuncItems(fn):
        for xref in XrefsFrom(item):
            if xref.iscode:
                if (xref.type == fl_CN) or (xref.type == fl_CF):
                    called_fns.append(xref.to)
    return called_fns

def get_called_functions_recursive(fn, depth):
    called_fns = []
    called_fns.append(fn)
    if depth <= 1:
        return get_called_functions(fn) + called_fns
    for _fn in get_called_functions(fn):
        called_fns = get_called_functions_recursive(_fn, depth-1) + called_fns
    return called_fns

def DeepDecompileFn(fn, depth, hx_view = None):
    inPseudocode = hx_view and 1 or 0
    for func in get_called_functions_recursive(fn, depth):
        idaapi.decompile(func)
    idaapi.open_pseudocode(fn, inPseudocode)

class DeepDecompile(idaapi.action_handler_t):
    
    def __init__(self, depth):
        idaapi.action_handler_t.__init__(self)
        self.depth = depth or 1
    def activate(self, ctx):
        if ctx.form_title[0:10] == "Pseudocode":
            hx_view = idaapi.get_tform_vdui(ctx.form)
            ea = hx_view.cfunc.entry_ea
        else:
            hx_view = None
            ea = ScreenEA()
        DeepDecompileFn(ea, self.depth, hx_view)
        return
    def update(self, ctx):
        return idaapi.AST_ENABLE_ALWAYS
#cannot get this working :(
class Hooks(idaapi.UI_Hooks):
    def __init__(self):
        idaapi.UI_Hooks.__init__(self)
    def hook(self):
        print "UI Hook Installed"
        pass
    def populating_tform_popup(self, form, popup):
        print "populating"
        if idaapi.get_tform_type(form) == idaapi.BWN_DISASM or idaapi.get_tform_type(form) == idaapi.BWN_DISASMS:
            idaapi.attach_action_to_popup(form, popup, "mee:DeepDecompile1", None)
            idaapi.attach_action_to_popup(form, popup, "mee:DeepDecompile3", None)
        

def hexrays_events_callback(*args):
    hexrays_event = args[0]

    if hexrays_event == idaapi.hxe_populating_popup:
        form, popup, hx_view = args[1:]
        item = hx_view.item
        idaapi.attach_action_to_popup(form, popup, "mee:DeepDecompile1", None)
        idaapi.attach_action_to_popup(form, popup, "mee:DeepDecompile3", None)
    return 0

class myplugin_t(idaapi.plugin_t):
    flags = idaapi.PLUGIN_UNL
    comment = "Plugin to deep decompile with hexrays"

    help = "Just right click and press the button"
    wanted_name = "Deep Decompile"
    wanted_hotkey = "Alt-F8"

    def init(self):
        if not idaapi.init_hexrays_plugin():
            print "[ERROR] Failed to initialize Hex-Rays SDK"
            return isaapi.PLUGIN_SKIP

        idaapi.register_action(
            idaapi.action_desc_t(
                "mee:DeepDecompile1",
                "Deep Decompile Function",
                DeepDecompile(1),
                None
            )
        )

        idaapi.register_action(
            idaapi.action_desc_t(
                "mee:DeepDecompile3",
                "Deep Decompile Function 3 Deep",
                DeepDecompile(3),
                None
            )
        )

        self.hooks = Hooks()
        self.hooks.hook()
        
        idaapi.attach_action_to_menu("View/Open subviews/Local types","mee:DeepDecompile3",idaapi.SETMENU_APP) 
        idaapi.attach_action_to_menu("View/Open subviews/Local types","mee:DeepDecompile1",idaapi.SETMENU_APP)
        idaapi.install_hexrays_callback(hexrays_events_callback)


        return idaapi.PLUGIN_KEEP

    def run(self, arg):
        DeepDecompileFn(idaapi.get_func(ScreenEA()).startEA, 1)

    def term(self):
        idaapi.unregister_action("mee:DeepDecompile1")
        idaapi.unregister_action("mee:DeepDecompile3")
        self.hooks.unhook()

def PLUGIN_ENTRY():
    return myplugin_t()
