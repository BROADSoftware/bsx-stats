


def ERROR(err):
    if type(err) is str:
        message = err
    else:
        message = err.__class__.__name__ + ": " + str(err)
    print "* * * * ERROR: " + str(message)
    exit(1)
    