import aiohttp
import asyncio
import xmltodict
from enum import Enum
from collections import namedtuple
from time import time
from datetime import datetime, timedelta

import logging

_LOGGER = logging.getLogger(__name__)

def sptime(value):
    h, m = map(int, value.split()[1].split(":"))
    return round(h+m/60, 2)

def parseTemperature(value: str):
    if value == '--.-':
        return float('NaN')
    return float(value)

class AccessLevel(Enum):
    LOGOUT = ""
    USER = "user"
    MASTER = "master"

class Buttons:
    SAVE = 200  # Predefined button number for save action

class HardwareDigitalOutput:
    def __init__(self, name, status, control_set, control_get):
        self.name = name
        self.status = status
        self.control_set = control_set
        self.control_get = control_get

class Sensor:
    def __init__(self, name, type, unit="", info="", convertor=None, friendly_name=None, homeassistant_class=None, homeassistant_sclass=None, homeassistant_inversed=False, homeassistant_icon=None, publish_time=0):
        self.name = name
        self.friendly_name = friendly_name
        self.unit = unit
        self.info = info
        self.type = type

        self.convertor = convertor
        self.publish_time = timedelta(seconds=publish_time)

        self.homeassistant_class = homeassistant_class
        self.homeassistant_inversed = homeassistant_inversed
        self.homeassistant_icon = homeassistant_icon
        self.homeassistant_sclass = homeassistant_sclass
        self.last_published = None

    def parse(self, value):
        if self.convertor:
            return self.convertor(value)
        return self.type(value)

    @property
    def need_publish(self):
        if self.last_published is None:
            return True
        return datetime.now() - self.last_published > self.publish_time

    def __repr__(self):
        return '<Value(name="{}", unit="{}", info="{}")>'.format(self.name, self.unit, self.info)

DIGITAL_OUTPUTS = {
    "SP1": HardwareDigitalOutput("SP1", "col400", 
        {"auto": 300, "auto_r": 301, "on": 302, "off": 303}, 
        {"col401": "auto", "col402": "auto_r", "col403": "on", "col404": "off"} 
    ),
    "SP2": HardwareDigitalOutput("SP2", "col405",
        {"auto": 304, "auto_r": 305, "on": 306, "off": 307},
        {"col406": "auto", "col407": "auto_r", "col408": "on", "col409": "off"}
    ),
    "OVR": HardwareDigitalOutput("OVR", "col410", 
        {"auto": 308, "auto_r": 309, "on": 310, "off": 311},
        {"col411": "auto", "col412": "auto_r", "col413": "on", "col414": "off"}
    ),
    "KRB": HardwareDigitalOutput("KRB", "col415",
        {"auto": 312, "auto_r": 313, "on": 314, "off": 315},
        {"col416": "auto", "col417": "auto_r", "col418": "on", "col419": "off"}
    ),
    "SOL": HardwareDigitalOutput("SOL", "col420",
        {"auto": 316, "auto_r": 317, "on": 318, "off": 319},
        {"col421": "auto", "col422": "auto_r", "col423": "on", "col424": "off"},
    ),
    "TVC": HardwareDigitalOutput("TVC", "col425",
        {"auto": 320, "auto_r": 321, "on": 322, "off": 323},
        {"col426": "auto", "col427": "auto_r", "col428": "on", "col429": "off"},
    ),
    "TO1": HardwareDigitalOutput("TO1", "col430",
        {"auto": 324, "auto_r": 325, "on": 326, "off": 327},
        {"col431": "auto", "col432": "auto_r", "col433": "on", "col434": "off"},
    ),
    "TO2": HardwareDigitalOutput("TO2", "col435",
        {"auto": 328, "auto_r": 329, "on": 330, "off": 331},
        {"col436": "auto", "col437": "auto_r", "col438": "on", "col439": "off"},
    ),
    "TCC": HardwareDigitalOutput("TCC", "col440",
        {"auto": 332, "auto_r": 333, "on": 334, "off": 335},
        {"col441": "auto", "col442": "auto_r", "col443": "on", "col444": "off"},
    ),
    "T/C": HardwareDigitalOutput("T/C", "col445",
        {"auto": 336, "auto_r": 337, "on": 338, "off": 339},
        {"col446": "auto", "col447": "auto_r", "col448": "on", "col449": "off"},
    ),
    "H/D": HardwareDigitalOutput("H/D", "col450",
        {"auto": 340, "auto_r": 341, "on": 342, "off": 343},
        {"col451": "auto", "col452": "auto_r", "col453": "on", "col454": "off"},
    ),
    "STO": HardwareDigitalOutput("STO", "col455",
        {"auto": 344, "auto_r": 345, "on": 346, "off": 347},
        {"col456": "auto", "col457": "auto_r", "col458": "on", "col459": "off"},
    ),
}

SENSORS = {
    "outdoorTemp": Sensor(type=float, name="txt113", unit="°C", convertor=parseTemperature, info="T13 teplota venkovního čidla", friendly_name="Outdoor teperature", homeassistant_sclass="measurement", homeassistant_class="temperature"),
    "outdoorTempMin": Sensor(type=float, name="txt714", unit="°C", convertor=parseTemperature, info="Minimální teplota za posledních 24 hodin", friendly_name="Minimal day temp", homeassistant_class="temperature"),
    "outdoorTempMax": Sensor(type=float, name="txt715", unit="°C", convertor=parseTemperature, info="Maximální teplota za posledních 24 hodin", homeassistant_class="temperature"),
    "outdoorTempMean": Sensor(type=float, name="txt713", unit="°C", convertor=parseTemperature, info="Průměrná teplota za posledních 24 hodin", homeassistant_class="temperature"),

    "watertankUpper": Sensor(type=float, name="txt101", unit="°C", convertor=parseTemperature, info="Teplota čidla T01 horní části zásobníku", friendly_name="Zásobník nahoře", homeassistant_class="temperature"),
    "watertankUpperRequest": Sensor(type=float, name="txt501", unit="°C", convertor=parseTemperature, info="Požadovaná teplota S1 horní části zásobníku", homeassistant_class="temperature"),
    "watertankUpperHeating": Sensor(type=bool, name="_ico101", info="Topná spirála SP1", convertor=lambda x: x=="1", homeassistant_class="heat", friendly_name="Topení zásobníku nahoře"),
    "watertankUpperHeatingTime": Sensor(type=float, name="txt740", unit="h", info="Čas topení spirály SP1", convertor=sptime, friendly_name="Topení zásobníku nahoře čas", homeassistant_icon="mdi:clock"),
    "watertankMiddle": Sensor(type=float, name="txt102", unit="°C", convertor=parseTemperature, info="Teplota čidla T02 střední části zásobníku", friendly_name="Zásobník střed", homeassistant_class="temperature"),
    "watertankLower": Sensor(type=float, name="txt106", unit="°C", convertor=parseTemperature, info="Teplota čidla T06 dolní části zásobníku", friendly_name="Zásobník dole", homeassistant_class="temperature"),
    "watertankLowerRequest": Sensor(type=float, name="txt502", unit="°C", convertor=parseTemperature, info="Požadovaná teplota S2 dolní části zásobníku"),
    "watertankLowerHeating": Sensor(type=bool, name="_ico102", info="Topná spirála SP2", convertor=lambda x: x=="1", homeassistant_class="heat", friendly_name="Topení zásobníku dole"),
    "watertankLowerHeatingTime": Sensor(type=float, name="txt741", unit="h", info="Čas topení spirály SP2", convertor=sptime, friendly_name="Topení zásobníku dole čas", homeassistant_icon="mdi:clock"),
    "watertankPressure": Sensor(type=bool, name="col202", info="Stav vstupu tlakového čidla, True = OK", homeassistant_class="problem", homeassistant_inversed=True, friendly_name="Tlak v systému"),

    "lowerFloor": Sensor(type=float, name="txt111", unit="°C", convertor=parseTemperature, info="T11 teplota čidla na výstupu ekvitermního okruhu TO1", friendly_name="Podlahovka přízemí", homeassistant_class="temperature"),
    "lowerFloorRequest": Sensor(type=float, name="txt520", unit="°C", convertor=parseTemperature, info="Požadovaná teplota ekvitermního okruhu TO1", homeassistant_class="temperature"),
    "lowerFloorMixing": Sensor(type=float, name="txt521", unit="%", info="Velikost otevření třícestného směšovacího ventilu okruhu TO1 v procentech", convertor=lambda x: int(x[:-1]), friendly_name="Směšovač přízemí", homeassistant_icon="mdi:call-merge"),
    "lowerFloorLimiting": Sensor(type=bool, name="col115", info="Útlum topného okruhu TO1, True=útlum aktivní", convertor=lambda x: x=="1"),
    "lowerFloorActive": Sensor(type=bool, name="col206", info="Vstup z prostorového termostatu TO1, True=požadavek top", convertor=lambda x: x=="1", friendly_name="Podlahové topení přízemí"),
    "lowerFloorCirculation": Sensor(type=bool, name="_ico107", info="Stav oběhového čerpadla topného okruhu TO1", convertor=lambda x: x=="3"),

    "upperFloor": Sensor(type=float, name="txt112", unit="°C", convertor=parseTemperature, info="T12 teplota čidla na výstupu ekvitermního okruhu TO2", friendly_name="Podlahovka patro", homeassistant_class="temperature"),
    "upperFloorRequest": Sensor(type=float, name="txt526", unit="°C", convertor=parseTemperature, info="Požadovaná teplota ekvitermního okruhu TO2", homeassistant_class="temperature"),
    "upperFloorMixing": Sensor(type=float, name="txt527", unit="%", info="Velikost otevření třícestného směšovacího ventilu okruhu TO2 v procentech", convertor=lambda x: int(x[:-1]), friendly_name="Směšovač patro", homeassistant_icon="mdi:call-merge"),
    "upperFloorLimiting": Sensor(type=bool, name="col116", info="Útlum topného okruhu TO2, True=útlum aktivní", convertor=lambda x: x=="1"),
    "upperFloorActive": Sensor(type=bool, name="col207", info="Vstup z prostorového termostatu TO2, True=požadavek top", convertor=lambda x: x=="1", friendly_name="Podlahové topení patro"),
    "upperFloorCirculation": Sensor(type=bool, name="_ico108", info="Stav oběhového čerpadla topného okruhu TO2", convertor=lambda x: x=="3"),

    "fireplace": Sensor(type=float, name="txt104", unit="°C", convertor=parseTemperature, info="T04 teplota čidla krbu", friendly_name="Krbová vložka", homeassistant_class="temperature"),
    "fireplaceCirculation": Sensor(type=bool, name="_ico104", info="Stav oběhového čerpadla krbového okruhu", convertor=lambda x: x=="3", friendly_name="Oběh krbových kamen"),

    "solarTemperature": Sensor(type=float, name="txt105", unit="°C", convertor=parseTemperature, info="T05 teplota čidla solárních panelů", homeassistant_icon="mdi:sun-thermometer", homeassistant_class="temperature", homeassistant_sclass="measurement"),
    "solarCirculation": Sensor(type=bool, name="col420", info="Stav oběhového čerpadla solárních panelů", convertor=lambda x: x=="1", homeassistant_class="running", homeassistant_icon="mdi:sun-wireless"),

    #"SP1Power": Sensor(type=float, name="txt590", unit='kW', info="Výkon patrony SP1", friendly_name="Výkon patrony SP1"),
    #"SP2Power": Sensor(type=float, name="txt591", unit='kW', info="Výkon patrony SP2", friendly_name="Výkon patrony SP2"),

    "lowTariff": Sensor(type=bool, name="col203", info="Stav vstupu NT nízkého tarifu HDO", convertor=lambda x: x=="1", friendly_name="Nízký tarif"),
    "waterCirculation": Sensor(type=bool, name="col106", info="Stav oběhového čerpadla cirkulace TUV ", convertor=lambda x: x=="1", homeassistant_class="running"),
    "UPS": Sensor(type=bool, name="col211", info="Vstup záložního zdroje", convertor=lambda x: x=="1", friendly_name="Záložní zdroj"),

    #"datetime": Sensor(type=datetime, name="_acctime", info="Aktuální datum a čas", convertor=lambda x: datetime.strptime(x[3:], "%d.%m.%Y  %H:%M:%S"), homeassistant_class="date"),
}

DEFAULT_PASSWORD = {
    AccessLevel.LOGOUT: "",
    AccessLevel.USER: "1234",
    AccessLevel.MASTER: "Servis254"
}

async def getXml(url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"HTTP {response.status}")
                text = await response.text()
                responseXML = xmltodict.parse(text)["response"]
                return responseXML
    except asyncio.TimeoutError:
        _LOGGER.error(f"Timeout while fetching {url}")
        raise
    except Exception as e:
        _LOGGER.error(f"Error fetching XML from {url}: {e}")
        raise

class IQR23:
    @staticmethod
    async def discovery(host: str):
        if not host.startswith('http'):
            host =  'http://'+host

        try:
            response = await getXml(f'{host}/data.xml')
            return response["_accvers"]
        except Exception as e:
            _LOGGER.error(f"Discovery failed for {host}: {e}")
            return None

    def __init__(self, host: str, user_pass=None, master_pass=None):
        self.host = host if host.startswith('http') else 'http://'+host
        self.password = {
            AccessLevel.LOGOUT: DEFAULT_PASSWORD[AccessLevel.LOGOUT],
            AccessLevel.USER: user_pass if user_pass else DEFAULT_PASSWORD[AccessLevel.USER],
            AccessLevel.MASTER: master_pass if master_pass else DEFAULT_PASSWORD[AccessLevel.MASTER]
        }
        self.state = dict()
        self.loadtime = 0
        self._sequential_lock = asyncio.Lock()

    async def loadFile(self, file):
        return await getXml(f"{self.host}/{file}.xml")
    
    async def load(self):
        #_LOGGER.warning(f"Loading....")
        files = (
            'data',
            'data_i_all',
            'data_t_zas',
        #    'data_n_zas',
            'data_n_txo',
        )

        self.state = dict()
        for file in files:
            file_data = await self.loadFile(file)
            self.state.update(file_data)


    async def loadIfRequired(self):
        now = time()
        async with self._sequential_lock:
            if self.loadtime + 5 < now:
                await self.load() 
                self.loadtime = now


    async def login(self, level=AccessLevel.LOGOUT):
        async with self._sequential_lock:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f'{self.host}/login.html', 
                        data={"pass": self.password[level]},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        return response.status == 200
            except Exception as e:
                _LOGGER.error(f"Login failed: {e}")
                return False
    
    async def logout(self, save=False):
        if save:
            await self._pressBtn(Buttons.SAVE)
        await self.login(AccessLevel.LOGOUT)

    async def _pressBtn(self, button: int):
        async with self._sequential_lock:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f'{self.host}/t_but.cgi?but={button}',
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        return response.status == 200
            except Exception as e:
                _LOGGER.error(f"Button press failed: {e}")
                return False

    async def setDigitalOutputMode(self, output, value):
        try:
            output = DIGITAL_OUTPUTS[output]
        except KeyError: 
            raise KeyError("Output not found")
        try:
            btn = output.control_set[value]
        except KeyError:
            raise KeyError("Value not found")
        await self.login(AccessLevel.MASTER)
        await self._pressBtn(btn)
        await self.logout()
        await self.load()
    
    async def getDigitalOutputMode(self, output):
        await self.loadIfRequired()
        try:
            output = DIGITAL_OUTPUTS[output]
        except KeyError: 
            raise KeyError("Output not found")
        setup = output.control_get
        for k, v in setup.items():
            if(self.state.get(k) == '1'):
                return v
        else:
            raise KeyError("Value not found")
        return None

    async def getDigitalOutputState(self, output):
        await self.loadIfRequired()
        try:
            output = DIGITAL_OUTPUTS[output]
        except KeyError: 
            raise KeyError("Output not found")

        try:
            value = self.state.get(output.status)
        except:
            raise KeyError("Value not found")
        return value == '1'
    
    async def getSensor(self, name):
        await self.loadIfRequired()
        try:
            sensor = SENSORS[name]
        except KeyError: 
            raise KeyError("Sensor not found")

        try:
            value = self.state[sensor.name]
        except KeyError:
            raise KeyError("Value not found")
        return sensor.parse(value)

    def __repr__(self):
        return f"<IQR23({self.host}, {self.loadtime})>"


def run_async(coroutine):
    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(coroutine)
