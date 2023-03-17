from pymeasure.instruments.agilent import AgilentE4980
from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import strict_discrete_set, strict_range
from pyvisa.errors import VisaIOError


class HP4284A(AgilentE4980):


    bias_voltage = Instrument.control("BIAS:VOLT:LEV?", "BIAS:VOLT %g",
                                      "DC bias voltage level, in Volts",
                                      validator=strict_range,
                                      values=[0, 20])

    trigger_delay = Instrument.control("TRIG:DEL?", "TRIG:DEL %g",
                                      "Trigger delay time, in seconds",
                                      validator=strict_range,
                                      values=[0, 60])

    impedance = Instrument.measurement("FETC?",
                                       "Measured data A and B, according to :attr:`~.AgilentE4980.mode`",
                                       get_process=lambda x: x[:2])

    def __init__(self, adapter, **kwargs):
        super().__init__(adapter, **kwargs)
        self.timeout = 30000
        self.name = "Helwett-Packard 4284A LCR Meter"

    def make_measurement(self):
        """Trigger measurement --> wait --> Fetch data"""
        self.write("TRIG:IMM")
        while 1:
            try:
                a, b = self.impedance
                break
            except VisaIOError:
                pass
        return a, b


    def enable_bias(self):
        """Enables DC bias, either current or voltage"""
        self.write("BIAS:STAT ON")

    def disable_bias(self):
        """Disables DC bias, either current or voltage"""
        self.write("BIAS:STAT OFF")

    def enable_hipower(self):
        """Enables High-Power, which means Option 001 (Power Amplifier/DC bias) is valid.
           Does nothing on E4980"""
        self.write("OUTP:HPOW ON")

    def enable_opencorrection(self):
        """Enables open-correction function"""
        self.write("CORR:OPEN:STAT ON")

    def enable_shortcorrection(self):
        """Enables short-correction function"""
        self.write("CORR:SHOR:STAT ON")

    def enable_dci_iso(self):
        """Enables DC bias current isolation (DCI:ISO)"""
        self.write("OUTP:DC:ISOL ON")

    def disable_dci_iso(self):
        """Disables DC bias current isolation (DCI:ISO)"""
        self.write("OUTP:DC:ISOL OFF")

    def enable_automaticlevelcontrol(self):
        """Enables Automatic Level Control (ALC)"""
        self.write("AMPL:ALC ON")

    def disable_automaticlevelcontro(self):
        """Disables Automatic Level Control (ALC)"""
        self.write("AMPL:ALC OFF")