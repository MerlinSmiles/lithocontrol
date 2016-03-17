layers = self.model.getRows()
for layer in layers:
    if layer.name == 'Virtual Electrodes':
        layer.setValues('Volt',  25)
        layer.setValues('Angle',  '0,90')
        layer.setValues('Rate',  1.5)
        layer.setValues('Step',  0.13)
        
    elif layer.name == 'Contacts':
        layer.setValues('Volt',  25)
        layer.setValues('Rate',  1.5)
        
        self.collapse(layer)
        # self.expand(layer)
        
    elif layer.name == 'Delete':
        layer.setValues('Volt',  -10)



#for layer in layers:
#    items = layer.getRows()
#    for num, item in enumerate(items):
#        print(num, item, layer)
#        item.setValues('Volt',num*2)
