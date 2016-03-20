import xlsxwriter

def k2g(val):
    return val / (1024*1024)

class XlsEngine:
    
    
    
    def __init__(self, filename):
        self.workbook = xlsxwriter.Workbook(filename + '.xlsx')
        self.headerFormat = self.workbook.add_format({'bold': True, 'align': 'center'})
        self.num0Format = self.workbook.add_format({'num_format': '###,###,##0'})


    def addPhysVolumesSheet(self, stats):
        PVOLS_HOST_COL = 0
        PVOLS_PATH_COL = 1
        PVOLS_SIZE_COL = 2
        PVOLS_USED_COL = 3
        PVOLS_FREE_COL = 4
        
        ws = self.workbook.add_worksheet('Phys. Volumes')
        ws.write(0, PVOLS_HOST_COL, "Host", self.headerFormat)
        ws.write(0, PVOLS_PATH_COL, "Path", self.headerFormat)
        ws.write(0, PVOLS_SIZE_COL, "Size (GB)", self.headerFormat)
        ws.write(0, PVOLS_USED_COL, "Used (GB)", self.headerFormat)
        ws.write(0, PVOLS_FREE_COL, "Free (GB)", self.headerFormat)
        
        ws.set_column(PVOLS_SIZE_COL, PVOLS_FREE_COL, None, self.num0Format)
        
        row = 1
        for host in stats.hosts:
            for volume in host.volumes:
                ws.write(row, PVOLS_HOST_COL, host.name )
                ws.write(row, PVOLS_PATH_COL, volume.path)
                ws.write(row, PVOLS_SIZE_COL, k2g(volume.size))
                ws.write(row, PVOLS_USED_COL, k2g(volume.used))
                ws.write(row, PVOLS_FREE_COL, k2g(volume.free))
                row += 1
            
            
        
        
