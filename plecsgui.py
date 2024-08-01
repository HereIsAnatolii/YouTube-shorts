class PlecsGUI(tk.Tk):
    def __init__(self,title):
        ''' title = "The title of your GUI window, the next two commands one needs to use are: 
            \nadd_block(); 
            \nrun()
        '''
        # ensure that the inheritance works properly
        super().__init__()
        
        self.title(title)
#        self.minsize(self.size['x'],self.size['y'])
        self.controller = Controller()
        self.plecs = xml.Server('http://localhost:1080/RPC2').plecs
        # widgets
        self.model = 'default'
        self.opener = Opener(self,self.controller)
        
        self.opener.grid(column=0,row=0)
        self.menu = []
        self.blocks = 1
        # self.menu = Block(self,self.controller,title = "Inductance (uH)",value = 50, 
        #                   steps = (10,50), limits = (10, 500),param = 'LuH')
        # self.menu2 = Block(self,self.controller,title = "DC Voltage",value = 800, 
        #                    steps = (10,50), limits = (0, 1000),param='Vdc')
        # self.menu3 = Block(self,self.controller,title = "Power",value = 3000, 
        #                    steps = (100,500), limits = (100, 4000),param='P')
        
        # self.menu.grid(column=0,row=1)
        # self.menu2.grid(column=1,row=0)
        # self.menu3.grid(column=1,row=1)
        
        
        self.attributes("-topmost", True)
        # Configure what happens when the window is closed
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # run
    
    def add_block(self,**kwargs):
        ''' title, param (that will be used in plecs), multiplier, value, steps : (small step,big step), limits : (min,max)'''
        if 'multiplier' not in kwargs:
            mul = 1
        else:
            mul = kwargs['multiplier']
        if 'loop' not in kwargs:
            kwargs['loop'] = False
            
        self.menu.append( 
            Block(self,self.controller,
                                title=kwargs['title'],
                                multiplier = mul,
                                value = kwargs['value'],
                                steps = kwargs['steps'], 
                                limits = kwargs['limits'],
                                param=kwargs['param'],
                                loop=kwargs['loop']
                     ) 
            )
        
        # Increment every time another block is added
        self.blocks +=1
        # Implement multiplier later
        
    def run(self):
        n_rows = (self.blocks)//5 + 2
        n_cols = self.blocks//n_rows
        
        print(f"number of blocks {self.blocks}; number of cols {n_cols}; number of rows {n_rows}")
        self.size = {'x':146*(n_cols+1),'y':110*(n_rows)}
        self.params = []            
        self.limits = []
        self.muls = []
        self.loops = []
        i = 0
        for col in range(1,n_cols+1):
            for row in range(n_rows):
                try:
                    self.menu[i].grid(column=col,row=row)
                    self.params.append(self.menu[i].args['param']+'.'+self.menu[i].args['title'])
                    self.limits.append(self.menu[i].args['limits'])
                    self.muls.append(self.menu[i].args['multiplier'])
                    self.loops.append(self.menu[i].args['loop'])
                except IndexError:
                    print('Index error for menu')
                i += 1
        print(self.params)
        self.loop = LoopSim(self,self.controller,self.params,self.limits,self.muls,self.loops)
        self.loop.grid(column=0,row=1)
        self.geometry(f"{self.size['x']}x{int(self.size['y']+i/10)}")
        
        self.mainloop()
        
        
    def on_closing(self):
        # Additional functions to run before closing the GUI
        print("Closing the GUI...")
        # Add your additional functions here
        model_name = self.controller.get_shared_var()
        if model_name == 'EMPTY':
            print('PLECS model not loaded')
        else:
            try:
                self.plecs.close(model_name)
            except:
                print("PLECS model is already closed")
        # Finally, close the GUI
        self.destroy()
            
class Controller:
    def __init__(self):
        self.shared_var = "EMPTY"
        
    def update_shared_var(self, new_value):
        self.shared_var = new_value
        
    def get_shared_var(self):
        return self.shared_var
    def set_Nsims(self,Nsims):
        self.Nsims = Nsims
    def get_Nsims(self):
        return self.Nsims
    def set_params(self,param):
        self.param = param
    def get_params(self):
        return self.param
    def set_dict(self,dict_minmax):
        self.dict_minmax = dict_minmax
    def get_dict(self):
        return self.dict_minmax
# recreate ttk Frame method as a class
class Opener(ttk.Frame):
    def __init__(self,parent,controller,**kwargs):
    # create the main method with a parent
    # it is the same as calling the object the same
    # and the parent should be the window
        super().__init__(parent)
        self.args = kwargs
        self.controller = controller
        self.create_opener()
        self.plecs = xml.Server('http://localhost:1080/RPC2').plecs
        
    def create_opener(self):
        main_frame = ttk.Frame(self, borderwidth=5, relief="solid")
        title_frame = ttk.Frame(main_frame,
                               borderwidth=1, relief="solid")
        action_frame = ttk.Frame(main_frame)
        label = ttk.Label(title_frame,text='Open PLECS file')
        
        self.frame_entry = ttk.Entry(action_frame)
        open_button = ttk.Button(action_frame,text='Open File',width=9,command=self.open_file)
        close_button = ttk.Button(action_frame,text='Close File',width=9,command=self.close_file)
        simulate = ttk.Button(action_frame,text='SIMULATE',width=20,command=self.simulate)
        
        main_frame.pack(fill='x',expand=True)
        
        title_frame.pack(fill='x')
        action_frame.pack(fill='x')
        label.pack()
        self.frame_entry.pack()
        simulate.pack(side=tk.BOTTOM)
        open_button.pack(side=tk.LEFT)
        close_button.pack(side=tk.RIGHT)
        
    def simulate(self):
        Nsims = int(self.controller.get_Nsims())
        if Nsims > 1:
            for i in range(Nsims):
                if i == 0:
                    try:
                        self.plecs.scope(self.model+'/Scope','ClearTraces')
                    except:
                        print("Scope 'Scope' is not found")
                # CHANGE THE PARAMETER
                WhatToChange = self.controller.get_params()
                print(f"{WhatToChange} will be looped")
                input_string = self.plecs.get(self.model,'InitializationCommands')
                re_str = WhatToChange + '.*?;'
                
                min_val = self.controller.get_dict()[WhatToChange][0]
                max_val = self.controller.get_dict()[WhatToChange][1]
                print(f"min_val = {min_val}, max_val = {max_val}")
                values = np.linspace(min_val,max_val,Nsims)
                
                command = re.sub(f'^{re_str}',f"{WhatToChange} = {values[i]};",input_string,flags=re.MULTILINE)
                
                # update the current command with the new value
                if input_string == command:
                    command += f"\n{WhatToChange} = {values[i]};"#"*{self.args['multiplier']};"
                self.plecs.set(self.model,'InitializationCommands',command)
                self.plecs.simulate(self.model)
                
                try:
                    self.plecs.scope(self.model+'/Scope','HoldTrace',f"{WhatToChange} = {values[i]}")
                except:
                    print("Scope 'Scope' is not found")
        else:
            try:
                self.plecs.scope(self.model+'/Scope','ClearTraces')
            except:
                print("Scope 'Scope' is not found")
            self.plecs.simulate(self.model)
            
    def close_file(self):
        self.controller.update_shared_var("EMPTY")
        self.plecs.close(self.model)
    def open_file(self):
            
        # Replace 'your_program.exe' with the path to your executable
        executable_path = r'C:\Users\GBT B450M-S2H\Documents\Plexim\PLECS 4.8 (64 bit)\plecs.exe'
        
        # Function to open the file explorer
        # Open the file dialog
        self.file_path = filedialog.askopenfilename(title="Select a File",
                                               filetypes=(("PLECS files", "*.plecs*"), ("all files", "*.*")))
        self.file = self.file_path.split(r'/')[-1]
        self.model = self.file.split('.plecs')[0]
        self.controller.update_shared_var(self.model)
            
        # Use subprocess to launch the executable
        try:
            subprocess.Popen([executable_path])
        except FileNotFoundError:
            print(f"Error: {executable_path} not found or unable to execute.")
        except subprocess.SubprocessError as e:
            print(f"Error: {e}")
            
        self.plecs.load(self.file_path)
        # Print the selected file path (optional)
        print(f"{self.file} is loaded")
        self.frame_entry.insert(0,f"{self.file}")
        
class LoopSim(ttk.Frame):
    def __init__(self,parent,controller,params,limits,mul,loops):
    # create a block with RadioButtons which determine
    # the loop-simulation
        super().__init__(parent)
        self.params = params
        self.mul = mul
        self.limits = limits
        self.loops = loops
        print(self.limits)
        for i, limit in enumerate(self.limits):
            self.limits[i] = [val*self.mul[i] for val in limit]
#           self.limits[i] = limits[i]*self.mul[i]#*self.mul
            
        print(self.limits)
        self.controller = controller
        self.create_block()
        self.controller.set_Nsims(1)
        
    def create_block(self):
        main_frame = ttk.Frame(self, borderwidth=5, relief="solid")
        title_frame = ttk.Frame(main_frame,
                               borderwidth=1, relief="solid")
        action_frame = ttk.Frame(main_frame)
        
        self.entry_var = tk.StringVar(value=1)
        self.entry_var.trace_add("write", self.on_entry_change)
        label = ttk.Label(title_frame,text='Number of Simulations')

#        self.entry_var = tk.StringVar()
#        self.entry_var.trace_add("write", self.on_entry_change)
#        self.entry_var.set(f"{self.args['value']}")
        self.frame_entry = ttk.Entry(action_frame, textvariable=self.entry_var)
        
#        self.frame_entry.insert(0,self.args['value'])
        
        button_up = ttk.Button(action_frame,text='>',width=9,command=self.increase)
        button_dn = ttk.Button(action_frame,text='<',width=9,command=self.decrease)
        self.choice = []
        self.dict_params = {}
        self.var = tk.StringVar(value=self.params[0].split('.')[0])  # Set default value to "Option 1"
        print(self.params[0].split('.')[0] + " = " + self.params[0].split('.')[1])
        for i in range(len(self.params)):
            if self.loops[i] == True:
                self.choice.append( tk.Radiobutton(action_frame, variable=self.var, text=self.params[i].split('.')[1], value=self.params[i].split('.')[0],command=self.set_choice) )
                self.dict_params[self.params[i].split('.')[0]] = self.limits[i]
                self.dict_params[self.params[i].split('.')[0]] = self.limits[i]
        self.controller.set_dict(self.dict_params)
        main_frame.pack()
        title_frame.pack(fill='x')
        label.pack()
        
        action_frame.pack(fill='x')
        self.frame_entry.pack(fill='x')
        for i in range(len(self.params)):
            if self.loops[i] == True:
                self.choice[i].pack(side=tk.BOTTOM)
            
        button_dn.pack(side=tk.LEFT)
        button_up.pack(side=tk.LEFT)
    def decrease(self):
        self.modify_entry(operand='-')
    def increase(self):
        self.modify_entry(operand='+')
    def on_entry_change(self, *args):
        # This method is called whenever the content of the entry widget changes
        model_name = self.controller.get_shared_var()
        if model_name == 'EMPTY':
            print('PLECS model not loaded')
        else:
            value = self.entry_var.get().split('.')[0]
            self.controller.set_Nsims(value)
            self.controller.set_params(self.var.get())
            print(self.dict_params[self.var.get()])
    def set_choice(self):
        selected_value = self.var.get()
        print(f"Selected option: {selected_value}")
        self.controller.set_params(self.var.get())
        print(self.dict_params[self.var.get()])
        
    def modify_entry(self,operand='+'):
        current_value = float(self.frame_entry.get())
        
        if operand == '+':
            new_value = current_value + 1
        elif operand == '-':
            new_value = current_value - 1
            
        if new_value <= 1:
            new_value = 1
        try:
            self.frame_entry.delete(0,tk.END)
            self.frame_entry.insert(0,new_value)
        except ValueError:
            self.frame_entry.insert(0,current_value)
            print('ValueError')
# recreate ttk Frame method as a class
class Block(ttk.Frame):
    def __init__(self,parent,controller,**kwargs):
    # create the main method with a parent
    # it is the same as calling the object the same
    # and the parent should be the window
        super().__init__(parent)
        self.args = kwargs
            
        self.controller = controller
        self.create_block()
        self.plecs = xml.Server('http://localhost:1080/RPC2').plecs
#        self.place(x = 0, y = 0)#, relwidth = 0.5, relheight = 1)
        
    def create_block(self):
        main_frame = ttk.Frame(self, borderwidth=5, relief="solid")
        title_frame = ttk.Frame(main_frame,
                               borderwidth=1, relief="solid")
        action_frame = ttk.Frame(main_frame)
        
        self.entry_var = tk.StringVar(value=self.args['value'])
        self.entry_var.trace_add("write", self.on_entry_change)
        label = ttk.Label(title_frame,text=self.args['title'])
        
        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", self.on_entry_change)
        self.entry_var.set(f"{self.args['value']}")
        self.frame_entry = ttk.Entry(action_frame, textvariable=self.entry_var)
#        self.frame_entry.insert(0,self.args['value'])
        
        button_up = ttk.Button(action_frame,text='>',width=4,command=self.increase_small)
        button_dn = ttk.Button(action_frame,text='<',width=4,command=self.decrease_small)
        button_2dn = ttk.Button(action_frame,text='<<',width=4,command=self.decrease_big)
        button_2up = ttk.Button(action_frame,text='>>',width=4,command=self.increase_big)
        button_rst = ttk.Button(action_frame,text='RESET',command=self.reset)
        
        main_frame.pack()
        title_frame.pack(fill='x')
        label.pack()
        
        action_frame.pack(fill='x')
        self.frame_entry.pack(fill='x')
        button_rst.pack(side=tk.BOTTOM,fill='both')
        button_2dn.pack(side=tk.LEFT)
        button_dn.pack(side=tk.LEFT)
        button_2up.pack(side=tk.RIGHT)
        button_up.pack(side=tk.RIGHT)
        
    def on_entry_change(self, *args):
        # This method is called whenever the content of the entry widget changes
        model_name = self.controller.get_shared_var()
        if model_name == 'EMPTY':
            print('PLECS model not loaded')
        else:
            value = self.entry_var.get()
            input_string = self.plecs.get(model_name,'InitializationCommands')
            re_str = self.args['param'] + '.*?;'
            command = re.sub(f'^{re_str}',f"{self.args['param']} = {value}*{self.args['multiplier']};",input_string,flags=re.MULTILINE)
            
            # update the current command with the new value
            if input_string == command:
                command += f"\n{self.args['param']} = {value}*{self.args['multiplier']};"
                # if self.args['multiplier'] == 1:
                #     command += f"\n{self.args['param']} = {value};"
                # else:
                #     command += f"\n{self.args['param']}_1 = {value};\n{self.args['param']} = n{self.args['param']}_1 * {self.args['multiplier']}"
                    
            print(command)
# command = re.sub(f'^{re_str}',f"{self.args['param']}_1 = {value};\n{self.args['param']} = {self.args['param']}_1 * {self.args['multiplier']};",input_string,flags=re.MULTILINE)
            self.plecs.set(model_name,'InitializationCommands',command)
            print(f"Entry content changed to: {self.entry_var.get()}")
        
    def reset(self):
        self.modify_entry(operand='rst',value=self.args['value'],rounding=2)
    def decrease_small(self):
        self.modify_entry(operand='-',value=self.args['steps'][0],rounding=2)
    def increase_small(self):
        self.modify_entry(operand='+',value=self.args['steps'][0],rounding=2)
    def decrease_big(self):
        self.modify_entry(operand='-',value=self.args['steps'][1],rounding=2)
    def increase_big(self):
        self.modify_entry(operand='+',value=self.args['steps'][1],rounding=2)
        
    def modify_entry(self,operand='+',value=1,rounding=5):
        current_value = float(self.frame_entry.get())
        
        if operand == '+':
            new_value = round(current_value + value,rounding)
        elif operand == '-':
            new_value = round(current_value - value,rounding)
        elif operand == 'rst':
            new_value = self.args['value']
            
        if new_value > self.args['limits'][1]:
            new_value = self.args['limits'][1]
        elif new_value < self.args['limits'][0]:
            new_value = self.args['limits'][0]
        try:
            self.frame_entry.delete(0,tk.END)
            self.frame_entry.insert(0,new_value)
        except ValueError:
            self.frame_entry.insert(0,current_value)
            print('ValueError')
            
