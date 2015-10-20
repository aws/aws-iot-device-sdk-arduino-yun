# tool func
###################################
def get_input(debug, buf):
    if(debug): # read from the given buffer
        terminator = buf[0].find('\n')
        if(len(buf[0]) != 0 and terminator != -1):
            ret = buf[0][0:terminator]
            buf[0] = buf[0][(terminator+1):]
            return ret
        else:  # simulate no-input blocking
            while 1:
                pass
    else:
        return raw_input() # read from stdin

def send_output(debug, buf, content):
    if(debug): # write to the given buffer
        buf[0] = buf[0][:0] + content[0:]
    else:
        print(content) # write to stdout
