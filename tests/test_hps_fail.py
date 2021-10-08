from pyelo import Elo
from time import sleep

def hps_stress():
    elo = Elo('GPIB::22::INSTR')
    qbs1 = elo._instruments[0]
    while True:
        qbs1.turn_on(True)
        sleep(0.1)
        qbs1.turn_off(True)
        sleep(5)


if __name__ == '__main__':
    hps_stress()
