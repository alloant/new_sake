from enum import Enum

class Flow(str, Enum): # Flow of records
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL_CR = "internal_cr"
    INTERNAL_CL = "internal_cl"
