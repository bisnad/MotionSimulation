import numpy as np

class RingBuffer:
    def __init__(self, pCapacity, pDataType):
        self.mCapacity = pCapacity
        self.mDataType = pDataType
        self.mBuffer = np.zeros(shape=[self.mCapacity] + list(self.mDataType.shape), dtype=self.mDataType.dtype)
        self.mUpdateIndex = 0
    
    def write(self, pValues):
        self.mBuffer[self.mUpdateIndex] = pValues
        self.mUpdateIndex = (self.mUpdateIndex + 1) % self.mCapacity
    
    def read(self, pValueCount):
        pValueCount = min(pValueCount, self.mCapacity)
        returnBuffer = np.zeros(shape=[pValueCount] + list(self.mDataType.shape), dtype=self.mDataType.dtype)
        
        for i in range(pValueCount):
            bufferIndex = (self.mUpdateIndex - 1 - i) % self.mCapacity
            returnBuffer[i] = self.mBuffer[bufferIndex]
            
        return returnBuffer
    
    def clear(self, value):
        self.mBuffer[-1] = value
        self.mUpdateIndex = 0
    
    def __str__(self):
        returnString = ""
        for i in range(self.mCapacity):
            bufferIndex = (self.mUpdateIndex - 1 - i) % self.mCapacity
            returnString += "i " + str(i) + " " + str(self.mBuffer[bufferIndex]) + "\n"
        return returnString
            
