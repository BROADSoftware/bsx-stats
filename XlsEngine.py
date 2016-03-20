import xlsxwriter

def k2g(val):
    return val / (1024*1024)

def b2g(val):
    return val / (1024*1024*1024)


columsIdx = [ 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'AA', 'AB' ]

class XlsEngine:
    
    
    
    def __init__(self, filename):
        self.workbook = xlsxwriter.Workbook(filename + '.xlsx')
        self.headerFormat = self.workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})
        self.num0Format = self.workbook.add_format({'num_format': '###,###,##0'})


    def addPhysVolumesSheet(self, stats):
        PVOLS_HOST_COL = 0
        PVOLS_PATH_COL = 1
        PVOLS_SIZE_COL = 2
        PVOLS_USED_COL = 3
        PVOLS_FREE_COL = 4
        PVOLS_FILES_COL = 5
        PVOLS_EXT_COL = 6
        
        ws = self.workbook.add_worksheet('Phys. Volumes')
        ws.write(0, PVOLS_HOST_COL, "Host", self.headerFormat)
        ws.write(0, PVOLS_PATH_COL, "Path", self.headerFormat)
        ws.write(0, PVOLS_SIZE_COL, "Size (GB)", self.headerFormat)
        ws.write(0, PVOLS_USED_COL, "Used (GB)", self.headerFormat)
        ws.write(0, PVOLS_FREE_COL, "Free (GB)", self.headerFormat)
        ws.write(0, PVOLS_FILES_COL, "Files (GB)", self.headerFormat)
        ws.write(0, PVOLS_EXT_COL, "Other (GB)", self.headerFormat)
        
        ws.set_column(PVOLS_SIZE_COL, PVOLS_EXT_COL, None, self.num0Format)
        
        row = 1
        for host in stats.hosts:
            for volume in host.volumes:
                ws.write(row, PVOLS_HOST_COL, host.name )
                ws.write(row, PVOLS_PATH_COL, volume.path)
                ws.write(row, PVOLS_SIZE_COL, k2g(volume.size))
                ws.write(row, PVOLS_USED_COL, k2g(volume.used))
                ws.write(row, PVOLS_FREE_COL, k2g(volume.free))
                ws.write(row, PVOLS_FILES_COL, b2g(volume.sumOfFiles))
                ws.write(row, PVOLS_EXT_COL, '=' + columsIdx[PVOLS_USED_COL] + str(row+1) + '-' + columsIdx[PVOLS_FILES_COL] + str(row+1))
                row += 1
            
    def addHostsSheet(self, stats):
        HOST_NAME_COL = 0
        HOST_RAM_SIZE_COL = 1
        HOST_RAM_USED_COL = 2
        HOST_RAM_FREE_COL = 3
        HOST_RAM_SHARED_COL = 4
        HOST_RAM_CACHE_COL = 5
        HOST_RAM_AVAILABLE_COL = 6
        HOST_SWAP_SIZE_COL = 7
        HOST_SWAP_USED_COL = 8
        HOST_SWAP_FREE_COL = 9
        HOST_CPUS_COL = 10
        
        
        ws = self.workbook.add_worksheet('Hosts')
        ws.merge_range(0, HOST_NAME_COL, 1, HOST_NAME_COL, "Name", self.headerFormat)
        
        ws.merge_range(0, HOST_RAM_SIZE_COL, 0, HOST_RAM_AVAILABLE_COL,"RAM (GB)", self.headerFormat)
        ws.write(1, HOST_RAM_SIZE_COL, "Size", self.headerFormat)
        ws.write(1, HOST_RAM_USED_COL, "Used", self.headerFormat)
        ws.write(1, HOST_RAM_FREE_COL, "Free", self.headerFormat)
        ws.write(1, HOST_RAM_SHARED_COL, "Shared", self.headerFormat)
        ws.write(1, HOST_RAM_CACHE_COL, "Cache", self.headerFormat)
        ws.write(1, HOST_RAM_AVAILABLE_COL, "Available", self.headerFormat)

        ws.merge_range(0, HOST_SWAP_SIZE_COL, 0, HOST_SWAP_FREE_COL, "SWAP (GB)", self.headerFormat)
        ws.write(1, HOST_SWAP_SIZE_COL, "Size", self.headerFormat)
        ws.write(1, HOST_SWAP_USED_COL, "Used", self.headerFormat)
        ws.write(1, HOST_SWAP_FREE_COL, "Free", self.headerFormat)
        
        ws.merge_range(0, HOST_CPUS_COL, 1, HOST_CPUS_COL, "Cpu", self.headerFormat)
        
        ws.set_column(HOST_RAM_SIZE_COL, HOST_SWAP_FREE_COL, None, self.num0Format)
        
        row = 2
        for host in stats.hosts:
            ws.write(row, HOST_NAME_COL, host.name )
            ws.write(row, HOST_RAM_SIZE_COL, b2g(host.memory.ram.size) )
            ws.write(row, HOST_RAM_USED_COL, b2g(host.memory.ram.used) )
            ws.write(row, HOST_RAM_FREE_COL, b2g(host.memory.ram.free) )
            ws.write(row, HOST_RAM_SHARED_COL, b2g(host.memory.ram.shared) )
            ws.write(row, HOST_RAM_CACHE_COL, b2g(host.memory.ram.cache) )
            ws.write(row, HOST_RAM_AVAILABLE_COL, b2g(host.memory.ram.available) )
            ws.write(row, HOST_SWAP_SIZE_COL, b2g(host.memory.swap.size) )
            ws.write(row, HOST_SWAP_USED_COL, b2g(host.memory.swap.used) )
            ws.write(row, HOST_SWAP_FREE_COL, b2g(host.memory.swap.free) )
            ws.write(row, HOST_CPUS_COL, host.cpus )
            row += 1
        
    def addFiles(self, stats):
        FILE_HOST_COL = 0
        FILE_VOL_COL = 1
        FILE_SIZE_COL = 2
        FILE_PATH_COL = 3

        ws = self.workbook.add_worksheet('Files')
        ws.write(0, FILE_HOST_COL, "Host", self.headerFormat)
        ws.write(0, FILE_VOL_COL, "Volume", self.headerFormat)
        ws.write(0, FILE_SIZE_COL, "Size (GB)", self.headerFormat)
        ws.write(0, FILE_PATH_COL, "Path", self.headerFormat)

        ws.set_column(FILE_SIZE_COL, FILE_SIZE_COL, None, self.num0Format)
        ws.set_column(FILE_PATH_COL, FILE_PATH_COL, 40)
        
        row = 1
        for host in stats.hosts:
            for volume in host.volumes:
                for f in volume.files:
                    ws.write(row, FILE_HOST_COL, host.name )
                    ws.write(row, FILE_VOL_COL, volume.path )
                    ws.write(row, FILE_SIZE_COL, b2g(f.size) )
                    ws.write(row, FILE_PATH_COL, f.name )
                    row += 1
                    

        
            
        
        
