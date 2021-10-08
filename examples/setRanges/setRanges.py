import pyelo

if __name__ == '__main__':
    elo = pyelo.Elo('GPIB::22::INSTR')

    elo.set_calibration_mode(True, "1234")
    inst = elo.instruments[0]

    print(inst.get_calibration_datetime())
    print(inst.get_calibration_serial())
    print(inst.get_calibration_remark())

    for inst in elo.instruments:
        inst.select()
        if inst.type == "QBS":
            range = (-800, 800)
        else:
            range = (-5000, 0)
        for channel in inst.channels:
            elo.write('CAL:OUTPUT:RANGE (@%d),%f,%f' % (channel, range[0], range[1]))

    elo.close()
