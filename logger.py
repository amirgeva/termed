Logger = open('termed.log', 'w')


def logwrite(s):
    if not isinstance(s, str):
        s = str(s)
    Logger.write(s)
    Logger.write('\n')
    Logger.flush()
