def sptime(value):
    h, m = map(int, value.split()[1].split(":"))
    return round(h+m/60, 2)

def parseTemperature(value: str):
    if value == '--.-':
        return float('NaN')
    return float(value)