

Logger = open('termed.log','w')


def logwrite(s):
    Logger.write(s)
    Logger.write('\n')
    Logger.flush()
