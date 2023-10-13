import asyncio
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError
import struct

class BLEReader:
    def __init__(self, debug=False, taskQueue=asyncio.Queue()):
        self.debug = debug
        # Queue of bluetooth request tasks
        self.tasks = taskQueue
        self.ready = False

    # Desc: Connects to a BLE device
    # name = name or address of BLE device to connect
    async def connect(self, name):
        self.deviceName = name
        self.characteristics = {}
        self.characteristicLabelLookup = {}
        await self.connectToDevice()
        self.ready = True

    # Desc: Starts monitoring provided characteristics for changes
    # characteristics = Bluetooth characteristics to monitor
    # onUpdate(characteristic, data) = callback function to be called each time a characteristic updates
    #   characteristic - the characteristic that was updated
    #   data - the newly updated data
    async def startMonitoring(self, characteristics, onUpdate):
        self.characteristicSearchNames = characteristics
        self.onUpdate = onUpdate

        await self.subscribeCharacteristics()
        while True:
            task = await self.tasks.get()
            if task == -1:
                break
            sendData = struct.pack("<h", int(0))
            try:
                await self._BLE_CLIENT.write_gatt_char(char_specifier=self.characteristics[task], data=sendData)
            except:
                self.ready = False
                print("Bluetooth error, reconnecting...")
                await self.connectToDevice()
                await self.subscribeCharacteristics()
                self.ready = True
        
        await self.unsubscribeCharacteristics()
        await self._BLE_CLIENT.disconnect()


    async def connectToDevice(self):
        # Find and connect to a device matching the name provided
        foundDevices = await self.searchBLEDeviceName(self.deviceName)
        self._BLE_CLIENT = BleakClient(address_or_ble_device = foundDevices[0], disconnected_callback = self.clientDisconnectHandler)
        await self._BLE_CLIENT.connect()
        print("Connected to: ", foundDevices[0].name)

    # Scans nearby bluetooth BLE devices for name or address that matches input 
    async def searchBLEDeviceName(self, name):
        foundDevices = []
        while len(foundDevices) == 0:
            scanResults = await BleakScanner.discover(return_adv=True)
            for address, (d, adv) in scanResults.items():
                if name.lower() in str(d.name).lower():
                    foundDevices.append(d)
                elif name.lower() in str(adv.local_name).lower():
                    foundDevices.append(d)
                elif name.lower() in address.lower():
                    foundDevices.append(d)

            if len(foundDevices) == 0:
                print("No devices found matching '%s'. Searching again..." % name)

        return foundDevices
    
    def clientDisconnectHandler(self, client):
        print("Client disconnected: ", client)

    async def subscribeCharacteristics(self):
        print("Descriptors: ")
        if len(self._BLE_CLIENT.services.descriptors) == 0:
            print("None")
        for descriptorNumber in self._BLE_CLIENT.services.descriptors:
            descriptor = self._BLE_CLIENT.services.get_descriptor(descriptorNumber)
            await self.printDescriptorDetails(descriptor)
        
        print("Services: ")
        if len(self._BLE_CLIENT.services.services) == 0:
            print("None")
        for serviceNumber in self._BLE_CLIENT.services.services:
            service = self._BLE_CLIENT.services.get_service(serviceNumber)
            await self.printServiceDetails(service)
        
        for serviceNumber in self._BLE_CLIENT.services.services:
            service = self._BLE_CLIENT.services.get_service(serviceNumber)
            if "Environmental Sensing" in service.description:
                self.env_service = service
                break
        
        for characteristic in self.env_service.characteristics:
            for targetCharacteristic in self.characteristicSearchNames:
                if targetCharacteristic in characteristic.description:
                    self.characteristics[targetCharacteristic] = characteristic
                    self.characteristicLabelLookup[characteristic.uuid] = targetCharacteristic
        
        for name, characteristic in self.characteristics.items():
            await self._BLE_CLIENT.start_notify(characteristic.uuid, self.characteristicUpdate)

    async def unsubscribeCharacteristics(self):
        for name, characteristic in self.characteristics.items():
            await self._BLE_CLIENT.stop_notify(characteristic.uuid)

    def characteristicUpdate(self, characteristic, data):
        updatedVal = float(struct.unpack("<h", data)[0])
        updatedVal = updatedVal/100
        # print("Update characteristic:", characteristic, " val:", updatedVal)
        self.onUpdate(self.characteristicLabelLookup[characteristic.uuid], updatedVal)

    # Helper functions to print Bluetooth attributes for debugging
    async def printDescriptorDetails(self, descriptor):
        print("Descriptor: ", descriptor.description)
        print("Descriptor value: ", await self._BLE_CLIENT.read_gatt_descriptor(descriptor.handle))

    async def printCharacteristicDetails(self, characteristic):
        print("Characteristic description: ", characteristic.description)
        print("Characteristic UUID: ", characteristic.uuid)
        print("Characteristic descriptors: ")
        if len(characteristic.descriptors) == 0:
            print("None")
        else:
            for descriptor in characteristic.descriptors:
                await self.printDescriptorDetails(descriptor)
            print("______End of descriptors______")

    async def printServiceDetails(self, service):
        print("Service description: ", service.description)
        print("List of characteristics in this service:")
        if len(service.characteristics) == 0:
            print("None")
        else: 
            for characteristic in service.characteristics:
                await self.printCharacteristicDetails(characteristic)
            print("______End of characteristics______")

    # Request new data for a specific charateristic
    # Characteristic argument should match the label given to monitorCharacteristics()
    # Writes zero to the characteristic being requested and awaits reponse from bluetooth device
    async def requestCharacteristic(self, characteristic):
        await self.tasks.put(characteristic)


# Demo example
async def main():
    demoReader = BLEReader(debug=True)
    characteristicList = ["Temperature", "Humidity", "Pressure", "PM1 Concentration", "PM2.5", "PM10"]
    def updateFn(label, val):
        print(label, "was updated to:", val)

    await demoReader.connect(name="28:CD:C1:0D:5C:C0")

    async def pollForNewData():
        while True:
            if demoReader.ready:
                characteristicListPoll = ["Temperature", "Humidity", "Pressure", "PM1 Concentration"]
                for characteristic in characteristicListPoll:
                    print("updating ", characteristic)
                    await demoReader.requestCharacteristic(characteristic)
                    await asyncio.sleep(0.5)
                await asyncio.sleep(50)
            else:
                print("waiting for readiness...")
                await asyncio.sleep(2)

    await asyncio.gather(
        demoReader.startMonitoring(characteristics=characteristicList, onUpdate=updateFn),
        pollForNewData()
    )

if __name__ == "__main__":
    asyncio.run(main())