
# Function receives the root Item of the data-tree as 'root'

layers = root.childItems

# layers = [self.getItem for i in layers]

if self.multi_check.checkState() == 2:
    multiples = self.multi_n.value()
    sleep = self.multi_time.value()
    dx = self.multi_dx.value()
    dy = self.multi_dy.value()
else:
    multiples = 1
    sleep = 0
    dx = 0
    dy = 0


for cpy in range(multiples):
    self.sketchAdd('# copy\t%d'%(cpy) )

    for layer in layers:
        if layer.checkState == 0:
            continue
        self.sketchAdd(sItem(layer))

        for child in layer.childItems:
            if child.checkState == 0:
                continue
            item = sItem(child)
            
            # changing values here that require recalculation wont have an effect,
            # call item.calcTime() if you need to

            # print(child.childItems)
            # print(item.name)
            # item.is_closed
            # item.fillAngle
            # item.fillStep
            # item.pathOrder
            # item.name
            # item.volt
            # print(item.volt)
            # item.rate
            item.offset = [cpy*dx,cpy*dy]
            self.sketchAdd(item)

    self.sketchAdd('pause\t%.1f' %(sleep))

