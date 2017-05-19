#!/usr/bin/env python3

from adc import MCP3221
from adc_rpc import ADCServer
from settings import PH_CONFIG


def main():
    adc = MCP3221(i2c_busn=PH_CONFIG['adc']['i2c_busn'],
                  i2c_addr=PH_CONFIG['adc']['i2c_addr'],
                  v_ref=PH_CONFIG['adc']['v_ref'])

    server = ADCServer(adc)
    server.serve_forever()


if __name__ == "__main__":
    main()
