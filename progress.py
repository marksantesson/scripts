

def progress(p, length=60, last = [-1]):
    if last[0]==-1:
        print('[', end='')
        last[0] = 0
    length = 55
    if int(p*length) > last[0]:
        print('-'*(int(p*length)-last[0]), end='', flush=True)
        last[0] = int(p*length)
    if p==1.0:
        print(']')
