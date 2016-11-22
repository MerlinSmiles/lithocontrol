layers = self.model.getRows()
for layer in layers:
    if layer.name == 'Virtual Electrodes':
        layer.setValues('Volt',  25)
        layer.setValues('Angle',  '0,90')
        layer.setValues('Rate',  2.5)
        layer.setValues('Step',  0.13)
        self.collapse(layer)
        
    elif layer.name == 'Virtual Electrodes 2':
        layer.setValues('Volt',  35)
        layer.setValues('Rate',  1)
        self.collapse(layer)
        
    elif layer.name in ['Contacts', 'Contacts2', 'Probes']:
        layer.setValues('Volt',  25)
        layer.setValues('Rate',  1.5)
        
        self.collapse(layer)
        # self.expand(layer)
        
    elif layer.name == 'Delete':
        layer.setValues('Volt',  -10)
        layer.setValues('Rate',  2)
        layer.setValues('Angle',  '-45,45')
        
    elif (layer.name == 'Ring') or (layer.name == 'Wire'):
        layer.setValues('Volt',  20)
        layer.setValues('Rate',  0.05)
        layer.setValues('Closed',  False)



#for layer in layers:
#    items = layer.getRows()
#    for num, item in enumerate(items):
#        print(num, item, layer)
#        item.setValues('Volt',num*2)
